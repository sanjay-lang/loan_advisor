def simulate_prepayment(principal, annual_rate, tenure_years, extra_monthly_payment):
    if principal <= 0 or annual_rate < 0 or tenure_years <= 0:
        raise ValueError("Loan amount and tenure must be positive, and rate cannot be negative.")

    if extra_monthly_payment < 0:
        raise ValueError("Extra monthly payment cannot be negative.")

    original_months = tenure_years * 12
    monthly_rate = annual_rate / (12 * 100)

    if monthly_rate == 0:
        regular_emi = principal / original_months
    else:
        regular_emi = (
            principal
            * monthly_rate
            * (1 + monthly_rate) ** original_months
            / ((1 + monthly_rate) ** original_months - 1)
        )

    original_interest = (regular_emi * original_months) - principal

    balance = principal
    total_interest = 0
    months_paid = 0
    monthly_payment = regular_emi + extra_monthly_payment

    while balance > 0.01 and months_paid < original_months:
        interest_for_month = balance * monthly_rate
        principal_payment = monthly_payment - interest_for_month

        if principal_payment <= 0:
            raise ValueError("Monthly payment must be greater than monthly interest.")

        total_interest += interest_for_month
        balance -= min(principal_payment, balance)
        months_paid += 1

    return {
        "regular_emi": regular_emi,
        "extra_monthly_payment": extra_monthly_payment,
        "total_monthly_payment": monthly_payment,
        "original_months": original_months,
        "new_months": months_paid,
        "new_tenure_years": months_paid / 12,
        "emis_saved": original_months - months_paid,
        "original_interest": original_interest,
        "new_interest": total_interest,
        "interest_saved": original_interest - total_interest,
    }
