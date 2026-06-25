from analysis import generate_loan_analysis


customer = {
    "name": input("Customer Name: ").strip(),
    "phone": input("Phone Number: ").strip(),
    "email": input("Email Address: ").strip(),
}

result = generate_loan_analysis(
    loan_amount=float(input("Loan Amount: ")),
    current_rate=float(input("Current Interest Rate: ")),
    new_rate=float(input("New Interest Rate: ")),
    remaining_tenure=int(input("Remaining Tenure (Years): ")),
    processing_fee=float(input("Processing Fee: ")),
    legal_fee=float(input("Legal Fee: ")),
    extra_monthly_payment=float(input("Extra Monthly Payment: ")),
    customer=customer,
)

print(f"\nBest Option: {result['best_option']}")
print(f"Best Strategy Savings: Rs. {result['best_savings']:,.2f}")
print("Report generated: report.html")
