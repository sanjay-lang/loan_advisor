import os
import base64
import re
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, url_for
import requests

from analysis import generate_loan_analysis


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
DEFAULT_FROM_EMAIL = "onboarding@resend.dev"
app = Flask(__name__)


def build_report_pdf_path(phone):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_phone = re.sub(r"[^0-9A-Za-z]+", "", phone or "unknown")
    REPORTS_DIR.mkdir(exist_ok=True)
    return REPORTS_DIR / f"report_{timestamp}_{safe_phone}.pdf"


def configure_weasyprint_library_path():
    library_paths = ["/opt/homebrew/lib", "/usr/local/lib"]
    existing_path = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    existing_paths = [path for path in existing_path.split(":") if path]
    for library_path in library_paths:
        if Path(library_path).exists() and library_path not in existing_paths:
            existing_paths.append(library_path)
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(existing_paths)


def create_report_pdf(html_path, pdf_path):
    configure_weasyprint_library_path()

    from weasyprint import HTML

    html = Path(html_path).read_text(encoding="utf-8")
    HTML(string=html, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))


def send_report_email(customer_email, pdf_path):
    if not customer_email:
        app.logger.info("Customer email not provided. Skipping report email.")
        return False

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        app.logger.warning("RESEND_API_KEY is not configured. Skipping report email.")
        return False

    try:
        attachment_content = base64.b64encode(Path(pdf_path).read_bytes()).decode("utf-8")
        payload = {
            "from": DEFAULT_FROM_EMAIL,
            "to": [customer_email],
            "subject": "Your Loan Advisor Report",
            "html": (
                "<p>Hi,</p>"
                "<p>Your Loan Advisor report is attached as a PDF.</p>"
                "<p>Regards,<br>Loan Advisor</p>"
            ),
            "attachments": [
                {
                    "filename": "Loan_Advisor_Report.pdf",
                    "content": attachment_content,
                }
            ],
        }
        app.logger.info(
            "Sending Resend email payload: from=%s to=%s attachment=%s "
            "base64_length=%s",
            payload["from"],
            payload["to"],
            payload["attachments"][0]["filename"],
            len(attachment_content),
        )
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        if response.status_code >= 400:
            app.logger.error(
                "Resend response for %s: status=%s body=%s",
                customer_email,
                response.status_code,
                response.text,
            )
        else:
            app.logger.info(
                "Resend response for %s: status=%s body=%s",
                customer_email,
                response.status_code,
                response.text,
            )
        response.raise_for_status()
        app.logger.info("Report email accepted by Resend for %s.", customer_email)
        return True
    except Exception:
        app.logger.exception("Failed to send report email.")
        return False


def save_lead_to_sheet(data):
    webhook_url = os.environ.get("GOOGLE_SHEETS_WEBHOOK_URL")
    app.logger.info(f"Trying to save lead to Google Sheets: {data}")
    app.logger.info(f"Webhook URL exists: {bool(webhook_url)}")
    if not webhook_url:
        app.logger.warning("GOOGLE_SHEETS_WEBHOOK_URL is not configured.")
        return

    try:
        response = requests.post(webhook_url, json=data, timeout=5)
        app.logger.info(f"Google Sheets response: {response.status_code} - {response.text}")
        response.raise_for_status()
    except Exception:
        app.logger.exception("Failed to save lead to Google Sheets.")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            extra_monthly_payment = float(request.form["extra_monthly_payment"])
            if extra_monthly_payment not in {0, 5000, 10000, 20000}:
                raise ValueError(
                    "Extra monthly prepayment must be Rs. 0, Rs. 5,000, "
                    "Rs. 10,000, or Rs. 20,000."
                )

            customer = {
                "name": request.form.get("customer_name", "").strip(),
                "phone": request.form.get("phone", "").strip(),
                "email": request.form.get("email", "").strip(),
            }
            loan_amount = float(request.form["loan_amount"])
            current_rate = float(request.form["current_rate"])
            new_rate = float(request.form["new_rate"])

            result = generate_loan_analysis(
                loan_amount=loan_amount,
                current_rate=current_rate,
                new_rate=new_rate,
                remaining_tenure=int(request.form["remaining_tenure"]),
                processing_fee=float(request.form["processing_fee"]),
                legal_fee=float(request.form["legal_fee"]),
                extra_monthly_payment=extra_monthly_payment,
                customer=customer,
            )

            app.logger.info(f"Analysis result keys: {result.keys()}")

            save_lead_to_sheet(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "customer_name": customer["name"],
                    "phone": customer["phone"],
                    "email": customer["email"],
                    "loan_amount": loan_amount,
                    "current_rate": current_rate,
                    "new_rate": new_rate,
                    "monthly_saving": result["monthly_saving"],
                    "net_saving": result["net_savings"],
                    "recommendation": result["recommendation"],
                }
            )

            try:
                pdf_path = build_report_pdf_path(customer["phone"])
                create_report_pdf(BASE_DIR / result["report_path"], pdf_path)
                send_report_email(customer["email"], pdf_path)
            except Exception:
                app.logger.exception("Failed to create or email the PDF report.")
        except (KeyError, ValueError, ZeroDivisionError) as error:
            return render_template(
                "index.html",
                error=f"Please check the entered values: {error}",
                values=request.form,
            )

        return redirect(url_for("view_report"))

    return render_template("index.html", error=None, values={})


@app.route("/report")
def view_report():
    return send_file(BASE_DIR / "report.html")


@app.route("/savings_chart.html")
def savings_chart():
    return send_file(BASE_DIR / "savings_chart.html")


@app.route("/break_even_chart.html")
def break_even_chart():
    return send_file(BASE_DIR / "break_even_chart.html")


if __name__ == "__main__":
    app.run(debug=True)
