from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, url_for

from analysis import generate_loan_analysis


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


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
            generate_loan_analysis(
                loan_amount=float(request.form["loan_amount"]),
                current_rate=float(request.form["current_rate"]),
                new_rate=float(request.form["new_rate"]),
                remaining_tenure=int(request.form["remaining_tenure"]),
                processing_fee=float(request.form["processing_fee"]),
                legal_fee=float(request.form["legal_fee"]),
                extra_monthly_payment=extra_monthly_payment,
                customer=customer,
            )
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
