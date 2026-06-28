from loan import Loan


def calculate_transfer_metrics(
    loan_amount,
    current_rate,
    new_rate,
    tenure_years,
    transfer_cost
):
    current_loan = Loan("Current Bank", loan_amount, current_rate, tenure_years)
    new_loan = Loan("New Bank", loan_amount, new_rate, tenure_years)
    current_emi = current_loan.calculate_emi()
    new_emi = new_loan.calculate_emi()
    monthly_saving = current_emi - new_emi
    months = tenure_years * 12

    if monthly_saving <= 0:
        break_even_months = float("inf")
        net_savings = (monthly_saving * months) - transfer_cost
    else:
        break_even_months = transfer_cost / monthly_saving
        net_savings = (monthly_saving * months) - transfer_cost

    if transfer_cost == 0:
        roi = float("inf")
    else:
        roi = (net_savings / transfer_cost) * 100

    return {
        "current_emi": current_emi,
        "new_emi": new_emi,
        "monthly_saving": monthly_saving,
        "break_even_months": break_even_months,
        "net_savings": net_savings,
        "roi": roi,
    }


def build_lender_comparison(
    loan_amount,
    current_rate,
    target_rate,
    tenure_years,
    transfer_cost
):
    indicative_lenders = [
        ("HDFC Bank", target_rate),
        ("ICICI Bank", target_rate + 0.10),
        ("SBI", target_rate + 0.15),
    ]
    lenders = []

    for lender_name, rate in indicative_lenders:
        metrics = calculate_transfer_metrics(
            loan_amount,
            current_rate,
            rate,
            tenure_years,
            transfer_cost
        )
        lenders.append(
            {
                "name": lender_name,
                "rate": rate,
                **metrics,
            }
        )

    return sorted(lenders, key=lambda lender: lender["net_savings"], reverse=True)


def build_rate_sensitivity(
    loan_amount,
    current_rate,
    target_rate,
    tenure_years,
    transfer_cost
):
    rates = sorted(
        {
            max(0, target_rate - 0.25),
            target_rate,
            target_rate + 0.25,
            target_rate + 0.50,
        },
        reverse=True
    )

    return [
        {
            "rate": rate,
            **calculate_transfer_metrics(
                loan_amount,
                current_rate,
                rate,
                tenure_years,
                transfer_cost
            ),
        }
        for rate in rates
    ]


def build_break_even_timeline(monthly_saving, transfer_cost, break_even_months):
    if monthly_saving <= 0:
        return [{"month": 0, "position": -transfer_cost}]

    final_month = max(4, int(break_even_months) + 3)
    return [
        {
            "month": month,
            "position": (monthly_saving * month) - transfer_cost,
        }
        for month in range(final_month + 1)
    ]


def calculate_loan_health_score(
    current_rate,
    new_rate,
    tenure_years,
    extra_monthly_payment,
    net_savings,
    break_even_months,
    decision_score
):
    rate_gap = current_rate - new_rate
    components = [
        {
            "label": "Interest Rate",
            "status": "Good" if rate_gap < 0.50 else "Needs attention",
            "points": 22 if rate_gap < 0.50 else 10,
        },
        {
            "label": "Prepayment",
            "status": "Active" if extra_monthly_payment > 0 else "Not active",
            "points": 22 if extra_monthly_payment > 0 else 5,
        },
        {
            "label": "Remaining Tenure",
            "status": "Long runway" if tenure_years >= 10 else "Limited runway",
            "points": 20 if tenure_years >= 10 else 12,
        },
        {
            "label": "Balance Transfer",
            "status": "Attractive" if net_savings > 500000 else "Marginal",
            "points": 22 if net_savings > 500000 else 10,
        },
        {
            "label": "Break-even",
            "status": "Fast" if break_even_months <= 12 else "Slow",
            "points": 14 if break_even_months <= 12 else 5,
        },
    ]

    return decision_score, components


def calculate_confidence_score(decision_score):
    return decision_score


def calculate_transfer_score(
    loan_amount,
    current_rate,
    new_rate,
    break_even_months,
    net_savings,
    tenure_years
):
    rate_reduction = max(current_rate - new_rate, 0)
    rate_score = min(rate_reduction / 1, 1) * 25

    savings_ratio = max(net_savings, 0) / loan_amount
    savings_score = min(savings_ratio / 0.15, 1) * 30

    if break_even_months == 0:
        break_even_score = 25
    else:
        break_even_score = max(0, min(1, (24 - break_even_months) / 18)) * 25

    tenure_score = min(max(tenure_years, 0) / 15, 1) * 20

    return round(rate_score + savings_score + break_even_score + tenure_score)


def get_recommendation(decision_score, monthly_saving, net_savings):
    if monthly_saving <= 0 or net_savings <= 0:
        return "Not Recommended"
    if decision_score >= 75:
        return "Strongly Recommended"
    if decision_score >= 50:
        return "Recommended"
    return "Marginal Opportunity"


def compare_loans(current_loan, new_loan,
                  processing_fee,
                  legal_fee):
    total_cost = processing_fee + legal_fee
    metrics = calculate_transfer_metrics(
        current_loan.principal,
        current_loan.rate,
        new_loan.rate,
        current_loan.tenure,
        total_cost
    )
    current_emi = metrics["current_emi"]
    new_emi = metrics["new_emi"]
    monthly_saving = metrics["monthly_saving"]
    break_even_months = metrics["break_even_months"]
    net_savings = metrics["net_savings"]
    roi = metrics["roi"]
    gross_savings = monthly_saving * current_loan.tenure * 12
    decision_score = calculate_transfer_score(
        current_loan.principal,
        current_loan.rate,
        new_loan.rate,
        break_even_months,
        net_savings,
        current_loan.tenure
    )

    print("\n------ Loan Comparison ------")
    print(f"Current Bank : {current_loan.bank_name}")
    print(f"New Bank     : {new_loan.bank_name}")
    print(f"Current EMI  : ₹{current_emi:,.2f}")
    print(f"New EMI      : ₹{new_emi:,.2f}")
    print(f"Monthly Saving : ₹{monthly_saving:,.2f}")

    print(f"\nTransfer Cost : ₹{total_cost:,.2f}")
    if break_even_months == 0:
        print("Break Even Period : Immediate")
    elif break_even_months == float("inf"):
        print("Break Even Period : Not achieved")
    else:
        print(f"Break Even Period : {break_even_months:.1f} months")
    print(f"Gross Tenure Savings : ₹{gross_savings:,.2f}")
    print(f"Net Savings : ₹{net_savings:,.2f}")
    print("ROI on Transfer : Infinite" if roi == float("inf") else f"ROI on Transfer : {roi:.0f}%")

    if monthly_saving > 0:
        print("✅ Balance transfer makes sense.")
    else:
        print("❌ Balance transfer does not help.")

    recommendation = get_recommendation(
        decision_score,
        monthly_saving,
        net_savings
    )

    print(f"Optimize Decision Score : {decision_score}/100")
    print(recommendation)

    return (
    monthly_saving,
    break_even_months,
    net_savings,
    roi,
    recommendation
    )
