import os
import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
import requests

from analysis import generate_loan_analysis


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORT_CONTEXT_PATH = BASE_DIR / "latest_report_context.json"
DEFAULT_FROM_EMAIL = "onboarding@resend.dev"
app = Flask(__name__)
latest_report_context = {}


def save_latest_report_context(context):
    try:
        REPORT_CONTEXT_PATH.write_text(json.dumps(context), encoding="utf-8")
    except Exception:
        app.logger.exception("Failed to save latest report context.")


def load_latest_report_context():
    if not REPORT_CONTEXT_PATH.exists():
        return {}

    try:
        return json.loads(REPORT_CONTEXT_PATH.read_text(encoding="utf-8"))
    except Exception:
        app.logger.exception("Failed to load latest report context.")
        return {}


def format_money(amount):
    if amount == float("inf"):
        return "Infinite"
    if amount < 0:
        return f"-₹{abs(amount):,.0f}"
    return f"₹{amount:,.0f}"


def format_lakh(amount):
    if amount < 0:
        return f"-₹{abs(amount) / 100000:,.1f} lakh"
    return f"₹{amount / 100000:,.1f} lakh"


def format_break_even(months):
    if months == 0:
        return "Immediate"
    if months == float("inf"):
        return "Not achieved"
    return f"{months:.1f} months"


def format_roi(roi):
    if roi == float("inf"):
        return "Infinite"
    return f"{roi:.0f}%"


def summarize_report_context(context):
    if not context:
        return "No report has been generated yet."

    prepayment = context.get("prepayment_result", {})
    strategies = context.get("strategies", [])
    strategy_summary = "; ".join(
        (
            f"{strategy['name']}: monthly payment {format_money(strategy['monthly_payment'])}, "
            f"payoff {strategy['months']} months, savings {format_lakh(strategy['savings'])}"
        )
        for strategy in strategies
    )

    return "\n".join(
        [
            f"Loan amount: {format_money(context['loan_amount'])}",
            f"Current rate: {context['current_rate']:.2f}%",
            f"New rate: {context['new_rate']:.2f}%",
            f"Current EMI: {format_money(context['current_emi'])}",
            f"New EMI: {format_money(context['new_emi'])}",
            f"Monthly saving: {format_money(context['monthly_saving'])}",
            f"Net saving: {format_money(context['net_savings'])} ({format_lakh(context['net_savings'])})",
            f"Break-even period: {format_break_even(context['break_even'])}",
            f"ROI: {format_roi(context['roi'])}",
            f"Recommendation: {context['recommendation']}",
            f"Transfer score: {context['transfer_score']}/100",
            f"Extra monthly prepayment: {format_money(context['extra_monthly_payment'])}",
            (
                "Prepayment simulation: "
                f"new tenure {prepayment.get('new_tenure_years', 0):.1f} years, "
                f"interest saved {format_lakh(prepayment.get('interest_saved', 0))}, "
                f"EMIs saved {prepayment.get('emis_saved', 0)} months"
            ),
            (
                f"Best strategy: {context['best_option']} with "
                f"{format_lakh(context['best_savings'])} savings"
            ),
            f"Strategy comparison: {strategy_summary}",
        ]
    )


def fallback_chat_answer(question, context):
    if not context:
        return "Please generate a loan report first, then I can answer questions about it."

    question_text = question.lower()
    if any(word in question_text for word in ["recommend", "should", "transfer", "switch"]):
        return (
            f"Recommendation: {context['recommendation']}. "
            f"The transfer score is {context['transfer_score']}/100, monthly saving is "
            f"{format_money(context['monthly_saving'])}, net saving is "
            f"{format_lakh(context['net_savings'])}, and break-even is "
            f"{format_break_even(context['break_even'])}."
        )
    if "emi" in question_text:
        return (
            f"Your current EMI is {format_money(context['current_emi'])}. "
            f"The new EMI is {format_money(context['new_emi'])}, giving a monthly saving of "
            f"{format_money(context['monthly_saving'])}."
        )
    if any(word in question_text for word in ["saving", "save", "benefit"]):
        return (
            f"Monthly saving is {format_money(context['monthly_saving'])}. "
            f"Net saving over the remaining tenure is {format_money(context['net_savings'])} "
            f"({format_lakh(context['net_savings'])})."
        )
    if any(word in question_text for word in ["break", "recover", "cost"]):
        return (
            f"The transfer cost is {format_money(context['transfer_cost'])}. "
            f"The break-even period is {format_break_even(context['break_even'])}."
        )
    if "roi" in question_text:
        return f"The estimated ROI on the transfer is {format_roi(context['roi'])}."
    if any(word in question_text for word in ["prepay", "prepayment", "extra"]):
        prepayment = context["prepayment_result"]
        return (
            f"With an extra monthly prepayment of {format_money(context['extra_monthly_payment'])}, "
            f"the loan can close in {prepayment['new_tenure_years']:.1f} years, "
            f"saving {format_lakh(prepayment['interest_saved'])} in interest and "
            f"{prepayment['emis_saved']} EMIs."
        )
    if any(word in question_text for word in ["strategy", "best option", "best"]):
        return (
            f"The best strategy is {context['best_option']}, with estimated savings of "
            f"{format_lakh(context['best_savings'])} compared with continuing the existing loan."
        )

    return (
        f"Here is the quick summary: loan amount {format_money(context['loan_amount'])}, "
        f"current rate {context['current_rate']:.2f}%, new rate {context['new_rate']:.2f}%, "
        f"monthly saving {format_money(context['monthly_saving'])}, net saving "
        f"{format_lakh(context['net_savings'])}, break-even {format_break_even(context['break_even'])}, "
        f"and recommendation: {context['recommendation']}."
    )


def ask_openai(question, context):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    prompt = (
        "You are a helpful loan advisor assistant. Answer only using the report data below. "
        "Be concise, practical, and avoid inventing details.\n\n"
        f"Report data:\n{summarize_report_context(context)}"
    )
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "input": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.2,
            },
            timeout=20,
        )
        if response.status_code >= 400:
            app.logger.error(
                "OpenAI response error: status=%s body=%s",
                response.status_code,
                response.text,
            )
        response.raise_for_status()
        data = response.json()
        answer = data.get("output_text")
        if answer:
            return answer.strip()
    except Exception:
        app.logger.exception("Failed to get OpenAI chatbot answer.")

    return None


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
    global latest_report_context

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
            latest_report_context = result.get("report_context", {})
            save_latest_report_context(latest_report_context)

            save_lead_to_sheet(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "customer_name": customer["name"],
                    "customerName": customer["name"],
                    "name": customer["name"],
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


@app.route("/ask", methods=["POST"])
def ask():
    global latest_report_context

    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"answer": "Please type a question about your loan report."}), 400

    report_context = latest_report_context or load_latest_report_context()
    latest_report_context = report_context

    answer = ask_openai(question, report_context)
    if not answer:
        answer = fallback_chat_answer(question, report_context)

    return jsonify({"answer": answer})


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
