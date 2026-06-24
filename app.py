def calculate_loan_details(loan_amount, annual_rate, tenure_years):
    monthly_rate = annual_rate / (12 * 100)
    number_of_months = tenure_years * 12

    if monthly_rate == 0:
        monthly_emi = loan_amount / number_of_months
    else:
        monthly_emi = (
            loan_amount
            * monthly_rate
            * (1 + monthly_rate) ** number_of_months
            / ((1 + monthly_rate) ** number_of_months - 1)
        )

    total_amount_paid = monthly_emi * number_of_months
    total_interest = total_amount_paid - loan_amount

    return monthly_emi, total_amount_paid, total_interest


loan_amount = float(input("Loan Amount: "))
interest_rate = float(input("Interest Rate (% per year): "))
tenure = int(input("Tenure (years): "))

if loan_amount <= 0 or interest_rate < 0 or tenure <= 0:
    print("Please enter valid values.")
else:
    monthly_emi, total_amount_paid, total_interest = calculate_loan_details(
        loan_amount,
        interest_rate,
        tenure,
    )

    print(f"\nMonthly EMI: Rs. {monthly_emi:,.2f}")
    print(f"Total Amount Paid: Rs. {total_amount_paid:,.2f}")
    print(f"Total Interest: Rs. {total_interest:,.2f}")
