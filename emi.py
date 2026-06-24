def calculate_emi(principal, annual_rate, tenure_years):
    monthly_rate = annual_rate / (12 * 100)
    number_of_months = tenure_years * 12

    if monthly_rate == 0:
        return principal / number_of_months

    return (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** number_of_months
        / ((1 + monthly_rate) ** number_of_months - 1)
    )


principal = float(input("Enter principal amount: "))
annual_rate = float(input("Enter annual interest rate (%): "))
tenure_years = int(input("Enter loan tenure (years): "))

if principal <= 0 or annual_rate < 0 or tenure_years <= 0:
    print("Please enter valid values.")
else:
    emi = calculate_emi(principal, annual_rate, tenure_years)
    print(f"The calculated monthly EMI is: Rs. {emi:,.2f}")
