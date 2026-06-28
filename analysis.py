from comparison import (
    build_break_even_timeline,
    build_lender_comparison,
    build_rate_sensitivity,
    calculate_confidence_score,
    calculate_loan_health_score,
    calculate_transfer_score,
    compare_loans,
)
from dashboard import generate_report
from loan import Loan
from prepayment import simulate_prepayment
from report import create_break_even_chart, create_savings_chart


def generate_loan_analysis(
    loan_amount,
    current_rate,
    new_rate,
    remaining_tenure,
    processing_fee,
    legal_fee,
    extra_monthly_payment,
    customer=None,
):
    current_loan = Loan(
        "Current Bank",
        loan_amount,
        current_rate,
        remaining_tenure,
    )
    new_loan = Loan(
        "New Bank",
        loan_amount,
        new_rate,
        remaining_tenure,
    )

    (
        monthly_saving,
        break_even,
        net_savings,
        roi,
        recommendation,
    ) = compare_loans(
        current_loan,
        new_loan,
        processing_fee,
        legal_fee,
    )

    current_emi = current_loan.calculate_emi()
    new_emi = new_loan.calculate_emi()
    transfer_cost = processing_fee + legal_fee
    transfer_score = calculate_transfer_score(
        loan_amount,
        current_rate,
        new_rate,
        break_even,
        net_savings,
        remaining_tenure,
    )

    current_prepayment = simulate_prepayment(
        loan_amount,
        current_rate,
        remaining_tenure,
        extra_monthly_payment,
    )
    transfer_prepayment = simulate_prepayment(
        loan_amount,
        new_rate,
        remaining_tenure,
        extra_monthly_payment,
    )

    strategies = [
        {
            "name": "Continue Existing Loan",
            "monthly_payment": current_emi,
            "months": remaining_tenure * 12,
            "interest": current_prepayment["original_interest"],
        },
        {
            "name": "Balance Transfer",
            "monthly_payment": new_emi,
            "months": remaining_tenure * 12,
            "interest": transfer_prepayment["original_interest"] + transfer_cost,
        },
        {
            "name": "Current Loan + Prepayment",
            "monthly_payment": current_prepayment["total_monthly_payment"],
            "months": current_prepayment["new_months"],
            "interest": current_prepayment["new_interest"],
        },
        {
            "name": "Transfer + Prepayment",
            "monthly_payment": transfer_prepayment["total_monthly_payment"],
            "months": transfer_prepayment["new_months"],
            "interest": transfer_prepayment["new_interest"] + transfer_cost,
        },
    ]
    baseline_cost = strategies[0]["interest"]

    for strategy in strategies:
        strategy["savings"] = max(baseline_cost - strategy["interest"], 0)

    best_strategy = max(strategies, key=lambda strategy: strategy["savings"])
    best_option = best_strategy["name"]
    best_savings = best_strategy["savings"]

    lenders = build_lender_comparison(
        loan_amount,
        current_rate,
        new_rate,
        remaining_tenure,
        transfer_cost,
    )
    rate_sensitivity = build_rate_sensitivity(
        loan_amount,
        current_rate,
        new_rate,
        remaining_tenure,
        transfer_cost,
    )
    break_even_timeline = build_break_even_timeline(
        monthly_saving,
        transfer_cost,
        break_even,
    )
    loan_health_score, loan_health_components = calculate_loan_health_score(
        current_rate,
        new_rate,
        remaining_tenure,
        extra_monthly_payment,
        net_savings,
        break_even,
        transfer_score,
    )
    confidence_score = calculate_confidence_score(transfer_score)

    if net_savings > 500000 and break_even <= 12:
        wait_recommendation = "Transfer now"
        wait_reason = (
            f"Estimated savings are Rs. {net_savings:,.0f} and transfer costs "
            f"are recovered {'immediately' if break_even == 0 else f'in {break_even:.1f} months'}."
        )
    else:
        wait_recommendation = "Review before transferring"
        wait_reason = (
            "The current savings or break-even period are not strong enough "
            "for an immediate transfer decision."
        )

    create_savings_chart(monthly_saving, transfer_cost, net_savings)
    create_break_even_chart(break_even_timeline)
    generate_report(
        loan_amount,
        current_rate,
        new_rate,
        monthly_saving,
        break_even,
        net_savings,
        roi,
        recommendation,
        current_emi,
        new_emi,
        transfer_cost,
        transfer_score,
        extra_monthly_payment,
        transfer_prepayment,
        strategies,
        best_option,
        best_savings,
        lenders,
        rate_sensitivity,
        loan_health_score,
        loan_health_components,
        confidence_score,
        wait_recommendation,
        wait_reason,
        customer=customer,
    )

    return {
        "monthly_saving": monthly_saving,
        "net_savings": net_savings,
        "recommendation": recommendation,
        "best_option": best_option,
        "best_savings": best_savings,
        "report_path": "report.html",
    }
