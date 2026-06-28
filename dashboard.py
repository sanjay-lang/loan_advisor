from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def format_lakh(amount):
    if amount < 0:
        return f"-₹{abs(amount) / 100000:,.1f} lakh"
    return f"₹{amount / 100000:,.1f} lakh"


def format_money(amount):
    if amount < 0:
        return f"-₹{abs(amount):,.0f}"
    return f"₹{amount:,.0f}"


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


def get_savings_color_class(amount):
    if amount > 1000000:
        return "savings-green"
    if amount >= 500000:
        return "savings-blue"
    if amount >= 100000:
        return "savings-orange"
    return "savings-grey"


def generate_report(
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
    prepayment_result,
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
    customer=None
):
    customer = customer or {}
    customer_name = customer.get("name") or "Customer"
    customer_phone = customer.get("phone") or "Not provided"
    customer_email = customer.get("email") or "Not provided"
    break_even_display = format_break_even(break_even)
    roi_display = format_roi(roi)
    rate_drop = current_rate - new_rate
    recommendation_class = "neutral-recommendation"
    if recommendation == "Strongly Recommended":
        recommendation_class = "positive-recommendation"
    elif recommendation == "Recommended":
        recommendation_class = "caution-recommendation"
    elif recommendation == "Not Recommended":
        recommendation_class = "negative-recommendation"
    recovery_text = "immediately" if break_even == 0 else f"within {break_even_display}"
    if break_even == float("inf"):
        recovery_text = "not currently recovered"
    star_count = max(0, min(5, round(transfer_score / 20)))
    transfer_stars = "★" * star_count + "☆" * (5 - star_count)
    net_savings_lakh = format_lakh(net_savings)
    interest_saved_lakh = format_lakh(prepayment_result["interest_saved"])
    chart_values = [
        ("Monthly Saving", monthly_saving),
        ("Transfer Cost", transfer_cost),
        ("Net Saving", net_savings),
    ]
    max_chart_value = max([abs(value) for _, value in chart_values] + [1])
    pdf_savings_bars = "".join(
        f"""
                    <div class="pdf-bar-row">
                        <span>{label}</span>
                        <div class="pdf-bar-track">
                            <div
                                class="pdf-bar {'negative-bar' if value < 0 else ''}"
                                style="width: {max(8, abs(value) / max_chart_value * 100):.1f}%;"
                            ></div>
                        </div>
                        <strong>{format_money(value)}</strong>
                    </div>
        """
        for label, value in chart_values
    )
    pdf_break_even_rows = "".join(
        f"""
                    <div class="pdf-timeline-row">
                        <span>Month {month}</span>
                        <strong>{format_money((monthly_saving * month) - transfer_cost)}</strong>
                    </div>
        """
        for month in range(0, 5)
    )
    strategy_rows = "".join(
        f"""
                        <tr class="{"best-row" if strategy["name"] == best_option else ""}">
                            <td>{strategy["name"]}</td>
                            <td>{format_money(strategy["monthly_payment"])}</td>
                            <td>{strategy["months"]} months</td>
                            <td>{format_money(strategy["interest"])}</td>
                            <td>
                                <span class="savings-pill {get_savings_color_class(strategy["savings"])}">
                                    {format_lakh(strategy["savings"]) if strategy["savings"] else format_money(0)}
                                </span>
                            </td>
                        </tr>
        """
        for strategy in strategies
    )
    strategy_cards = "".join(
        f"""
                    <div class="strategy-card {"strategy-winner" if strategy["name"] == best_option else ""}">
                        <span>{strategy["name"]}</span>
                        <strong>{format_lakh(strategy["savings"]) if strategy["savings"] else format_money(0)}</strong>
                        <small>Total savings vs continuing</small>
                    </div>
        """
        for strategy in strategies
    )
    lender_rows = "".join(
        f"""
                        <tr class="{"best-row" if index == 0 else ""}">
                            <td>{lender["name"]}</td>
                            <td>{lender["rate"]:.2f}%</td>
                            <td>{format_money(lender["new_emi"])}</td>
                            <td>{format_lakh(lender["net_savings"])}</td>
                            <td>{format_break_even(lender["break_even_months"])}</td>
                        </tr>
        """
        for index, lender in enumerate(lenders)
    )
    sensitivity_rows = "".join(
        f"""
                        <tr>
                            <td>{scenario["rate"]:.2f}%</td>
                            <td>{format_money(scenario["new_emi"])}</td>
                            <td>{format_money(scenario["monthly_saving"])}</td>
                            <td>{format_lakh(scenario["net_savings"])}</td>
                        </tr>
        """
        for scenario in rate_sensitivity
    )
    health_rows = "".join(
        f"""
                    <div class="health-row">
                        <span>{component["label"]}</span>
                        <strong>{component["status"]}</strong>
                    </div>
        """
        for component in loan_health_components
    )

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Loan Advisor Report</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            html {{
                width: 100%;
                overflow-x: hidden;
            }}

            body {{
                width: 100%;
                min-width: 0;
                margin: 0;
                font-family: Arial;
                background: #f5f7fa;
                padding: 40px;
                overflow-x: hidden;
            }}

            .report {{
                width: 100%;
                max-width: 980px;
                min-width: 0;
                margin: auto;
                padding: 40px;
                overflow: hidden;
                background: white;
                border-radius: 8px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }}

            .report > * {{
                min-width: 0;
                max-width: 100%;
            }}

            .cards {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 20px;
                margin-top: 40px;
                margin-bottom: 40px;
            }}

            .card {{
                background: white;
                min-width: 0;
                padding: 24px;
                border: 1px solid #e4e8f0;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}

            .card h3 {{
                color: #666;
                margin: 0 0 10px;
            }}

            .card p {{
                margin: 0;
                font-size: 30px;
                font-weight: bold;
                color: #243c8f;
                overflow-wrap: anywhere;
            }}

            h1 {{
                margin: 0 0 24px;
                color: #1e3a8a;
                overflow-wrap: anywhere;
            }}

            .row {{
                display: flex;
                justify-content: space-between;
                gap: 20px;
                padding: 12px 0;
                border-bottom: 1px solid #eee;
            }}

            .row div:last-child {{
                flex: 0 0 auto;
                text-align: right;
            }}

            .customer-details {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 1px;
                margin: 0 0 28px;
                overflow: hidden;
                border: 1px solid #dbe3f5;
                border-radius: 12px;
                background: #dbe3f5;
            }}

            .customer-detail {{
                min-width: 0;
                padding: 16px;
                background: #f7f9ff;
            }}

            .customer-detail span {{
                display: block;
                margin-bottom: 6px;
                color: #64748b;
                font-size: 12px;
            }}

            .customer-detail strong {{
                display: block;
                overflow-wrap: anywhere;
                color: #243c8f;
            }}

            .recommendation {{
                margin-top: 30px;
                padding: 30px;
                border-radius: 20px;
                font-size: 32px;
                text-align: center;
                font-weight: bold;
                box-shadow: 0 6px 24px rgba(8,116,67,0.12);
                overflow-wrap: anywhere;
            }}

            .positive-recommendation {{
                background: #ecfdf5;
                color: #087443;
            }}

            .caution-recommendation {{
                background: #fffbeb;
                color: #92400e;
            }}

            .negative-recommendation {{
                background: #fef2f2;
                color: #991b1b;
                box-shadow: 0 6px 24px rgba(153,27,27,0.10);
            }}

            .neutral-recommendation {{
                background: #f8fafc;
                color: #334155;
            }}

            .transfer-score {{
                display: grid;
                grid-template-columns: auto 1fr;
                gap: 24px;
                align-items: center;
                margin-top: 30px;
                padding: 28px;
                border: 1px solid #dbe3f5;
                border-radius: 20px;
                background: #f7f9ff;
            }}

            .score-number {{
                width: 130px;
                height: 130px;
                display: grid;
                place-items: center;
                border: 12px solid #243c8f;
                border-radius: 50%;
                color: #243c8f;
                font-size: 30px;
                font-weight: bold;
            }}

            .score-copy h2 {{
                margin: 0 0 8px;
                color: #243c8f;
            }}

            .stars {{
                color: #f59e0b;
                font-size: 28px;
                letter-spacing: 2px;
            }}

            .advisor-box {{
                min-width: 0;
                overflow: hidden;
                margin-top: 40px;
                padding: 30px;
                background: #ffffff;
                border-radius: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                line-height: 1.8;
            }}

            .advisor-box h2 {{
                color: #243c8f;
                margin: 0 0 20px;
            }}

            .advisor-box p {{
                font-size: 20px;
                color: #333;
                overflow-wrap: anywhere;
            }}

            .report-section {{
                width: 100%;
                min-width: 0;
                margin-top: 40px;
                overflow-x: auto;
                overscroll-behavior-inline: contain;
            }}

            .report-section h2 {{
                color: #243c8f;
                margin-bottom: 20px;
            }}

            .chart-frame {{
                display: block;
                width: 100%;
                max-width: 100%;
                height: 460px;
                border: 1px solid #e4e8f0;
                border-radius: 8px;
                background: white;
            }}

            .pdf-chart {{
                display: none;
            }}

            .pdf-bar-row {{
                display: grid;
                grid-template-columns: 135px 1fr 115px;
                gap: 12px;
                align-items: center;
                margin: 12px 0;
            }}

            .pdf-bar-track {{
                height: 18px;
                overflow: hidden;
                border-radius: 999px;
                background: #e2e8f0;
            }}

            .pdf-bar {{
                height: 100%;
                border-radius: 999px;
                background: #16a34a;
            }}

            .negative-bar {{
                background: #ef4444;
            }}

            .pdf-timeline-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e2e8f0;
            }}

            .comparison-table {{
                width: 100%;
                min-width: 680px;
                border-collapse: collapse;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            }}

            .comparison-table th,
            .comparison-table td {{
                padding: 16px;
                border-bottom: 1px solid #e4e8f0;
                text-align: left;
            }}

            .comparison-table th {{
                background: #243c8f;
                color: white;
            }}

            .comparison-table tbody tr:nth-child(even) {{
                background: #f7f9fc;
            }}

            .prepayment-box {{
                margin-top: 40px;
                padding: 30px;
                border-radius: 20px;
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
            }}

            .prepayment-box h2 {{
                margin: 0 0 8px;
                color: #087443;
            }}

            .prepayment-box > p {{
                margin: 0;
                color: #4b5563;
                line-height: 1.6;
            }}

            .prepayment-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
                margin-top: 24px;
            }}

            .prepayment-card {{
                padding: 20px;
                border-radius: 12px;
                background: white;
                border: 1px solid #d1fae5;
            }}

            .prepayment-card span {{
                display: block;
                color: #6b7280;
                margin-bottom: 8px;
            }}

            .prepayment-card strong {{
                color: #087443;
                font-size: 25px;
            }}

            .best-option {{
                margin-top: 24px;
                padding: 22px;
                border-radius: 12px;
                background: #087443;
                color: white;
                text-align: center;
                font-size: 22px;
                font-weight: bold;
            }}

            .best-row {{
                background: #dcfce7 !important;
                color: #065f46;
                font-weight: bold;
            }}

            .strategy-optimizer {{
                margin-top: 40px;
                padding: 30px;
                border-radius: 20px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
            }}

            .strategy-optimizer h2 {{
                margin: 0 0 8px;
                color: #243c8f;
            }}

            .strategy-optimizer > p {{
                margin: 0;
                color: #64748b;
            }}

            .strategy-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
                margin-top: 24px;
            }}

            .strategy-card {{
                padding: 22px;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background: white;
            }}

            .strategy-card span,
            .strategy-card small {{
                display: block;
                color: #64748b;
            }}

            .strategy-card strong {{
                display: block;
                margin: 10px 0 6px;
                color: #243c8f;
                font-size: 27px;
            }}

            .strategy-winner {{
                border: 2px solid #16a34a;
                background: #f0fdf4;
            }}

            .strategy-winner::before {{
                content: "Best Strategy";
                display: inline-block;
                margin-bottom: 12px;
                padding: 5px 10px;
                border-radius: 999px;
                background: #16a34a;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }}

            .optimizer-result {{
                margin-top: 22px;
                padding: 22px;
                border-radius: 12px;
                background: #243c8f;
                color: white;
                text-align: center;
                font-size: 21px;
                font-weight: bold;
            }}

            .savings-pill {{
                display: inline-block;
                min-width: 90px;
                padding: 6px 10px;
                border-radius: 999px;
                text-align: center;
                font-weight: bold;
                white-space: nowrap;
            }}

            .savings-green {{
                color: #166534;
                background: #dcfce7;
            }}

            .savings-blue {{
                color: #1e40af;
                background: #dbeafe;
            }}

            .savings-orange {{
                color: #9a3412;
                background: #ffedd5;
            }}

            .savings-grey {{
                color: #475569;
                background: #e2e8f0;
            }}

            .timeline {{
                margin-top: 40px;
                padding: 30px;
                border-radius: 20px;
                background: white;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}

            .timeline h2 {{
                margin: 0 0 24px;
                color: #243c8f;
            }}

            .timeline-item {{
                position: relative;
                margin-left: 12px;
                padding: 0 0 26px 32px;
                border-left: 3px solid #c7d2fe;
            }}

            .timeline-item:last-child {{
                padding-bottom: 0;
                border-left-color: transparent;
            }}

            .timeline-item::before {{
                content: "";
                position: absolute;
                top: 0;
                left: -9px;
                width: 15px;
                height: 15px;
                border-radius: 50%;
                background: #243c8f;
            }}

            .timeline-item strong {{
                display: block;
                margin-bottom: 5px;
            }}

            .timeline-item span {{
                color: #64748b;
            }}

            .assumptions {{
                margin-top: 40px;
                padding: 26px 30px;
                border-radius: 16px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
            }}

            .assumptions h2 {{
                margin: 0 0 16px;
                color: #243c8f;
            }}

            .assumptions ul {{
                margin: 0;
                padding-left: 22px;
                color: #475569;
                line-height: 1.8;
            }}

            .decision-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                min-width: 0;
                margin-top: 40px;
            }}

            .health-box,
            .wait-box {{
                min-width: 0;
                overflow: hidden;
                padding: 28px;
                border-radius: 20px;
                border: 1px solid #e2e8f0;
                background: white;
                box-shadow: 0 4px 18px rgba(0,0,0,0.06);
            }}

            .health-box h2,
            .wait-box h2 {{
                margin: 0 0 16px;
                color: #243c8f;
            }}

            .health-score {{
                display: flex;
                align-items: baseline;
                gap: 8px;
                margin-bottom: 20px;
            }}

            .health-score strong {{
                color: #243c8f;
                font-size: 42px;
            }}

            .health-score span {{
                color: #64748b;
                font-size: 18px;
            }}

            .health-row {{
                display: flex;
                justify-content: space-between;
                gap: 20px;
                padding: 10px 0;
                border-top: 1px solid #eef2f7;
            }}

            .health-row strong {{
                color: #087443;
                text-align: right;
            }}

            .confidence {{
                margin-top: 20px;
                padding: 16px;
                border-radius: 12px;
                background: #f7f9ff;
            }}

            .confidence strong {{
                display: block;
                color: #243c8f;
                font-size: 26px;
            }}

            .confidence-track {{
                height: 10px;
                margin-top: 10px;
                overflow: hidden;
                border-radius: 999px;
                background: #dbe3f5;
            }}

            .confidence-fill {{
                height: 100%;
                border-radius: 999px;
                background: #243c8f;
            }}

            .wait-answer {{
                display: inline-block;
                margin-bottom: 18px;
                padding: 10px 14px;
                border-radius: 999px;
                color: white;
                background: #087443;
                font-size: 20px;
                font-weight: bold;
            }}

            .wait-box p {{
                color: #475569;
                font-size: 17px;
                line-height: 1.7;
            }}

            .disclaimer {{
                margin: 10px 0 0;
                color: #64748b;
                font-size: 12px;
            }}

            @media (max-width: 620px) {{
                body {{
                    padding: 12px;
                }}

                .report {{
                    padding: 24px 18px;
                    border-radius: 0;
                }}

                .cards {{
                    grid-template-columns: 1fr;
                    margin-top: 28px;
                    margin-bottom: 28px;
                }}

                h1 {{
                    font-size: 28px;
                    line-height: 1.15;
                }}

                .row {{
                    align-items: start;
                }}

                .customer-details {{
                    grid-template-columns: 1fr;
                }}

                .advisor-box {{
                    padding: 22px;
                }}

                .advisor-box p {{
                    font-size: 17px;
                }}

                .recommendation {{
                    padding: 24px 16px;
                    font-size: 22px;
                    overflow-wrap: anywhere;
                }}

                .transfer-score {{
                    grid-template-columns: 1fr;
                    padding: 22px;
                }}

                .score-number {{
                    width: 112px;
                    height: 112px;
                    border-width: 10px;
                    font-size: 25px;
                }}

                .prepayment-grid {{
                    grid-template-columns: 1fr;
                }}

                .strategy-grid {{
                    grid-template-columns: 1fr;
                }}

                .decision-grid {{
                    grid-template-columns: 1fr;
                }}

                .report-section h2 {{
                    font-size: 25px;
                    line-height: 1.2;
                    overflow-wrap: anywhere;
                }}

                .advisor-box h2,
                .prepayment-box h2,
                .strategy-optimizer h2,
                .timeline h2,
                .assumptions h2,
                .health-box h2,
                .wait-box h2 {{
                    overflow-wrap: anywhere;
                }}

                .comparison-table {{
                    min-width: 620px;
                }}

                .comparison-table th,
                .comparison-table td {{
                    padding: 12px;
                }}

                .health-row {{
                    align-items: start;
                }}

                .health-row strong {{
                    max-width: 50%;
                    overflow-wrap: anywhere;
                }}

                .chart-frame {{
                    min-width: 0;
                    height: 360px;
                }}
            }}

            @page {{
                size: A4;
                margin: 14mm;
            }}

            @media print {{
                html,
                body {{
                    width: auto;
                    background: white;
                    padding: 0;
                    overflow: visible;
                    font-family: Arial, sans-serif;
                    color: #111827;
                }}

                .report {{
                    width: 100%;
                    max-width: none;
                    margin: 0;
                    padding: 0;
                    overflow: visible;
                    border-radius: 0;
                    box-shadow: none;
                }}

                h1 {{
                    font-size: 26px;
                    margin-bottom: 16px;
                }}

                .customer-details {{
                    border-radius: 8px;
                    margin-bottom: 18px;
                }}

                .customer-detail {{
                    padding: 10px;
                }}

                .customer-details {{
                    grid-template-columns: 1fr 0.85fr 1.35fr;
                }}

                .customer-detail strong {{
                    font-size: 12px;
                    line-height: 1.25;
                }}

                .cards,
                .decision-grid,
                .prepayment-grid,
                .strategy-grid {{
                    gap: 10px;
                }}

                .cards {{
                    margin-top: 18px;
                    margin-bottom: 18px;
                }}

                .card,
                .advisor-box,
                .prepayment-box,
                .strategy-optimizer,
                .timeline,
                .assumptions,
                .health-box,
                .wait-box,
                .transfer-score {{
                    padding: 14px;
                    border-radius: 8px;
                    box-shadow: none;
                    break-inside: avoid;
                }}

                .card p {{
                    font-size: 20px;
                }}

                .recommendation {{
                    margin-top: 18px;
                    padding: 16px;
                    border-radius: 8px;
                    font-size: 22px;
                    box-shadow: none;
                    break-inside: avoid;
                }}

                .score-number {{
                    width: 86px;
                    height: 86px;
                    border-width: 8px;
                    font-size: 20px;
                }}

                .advisor-box {{
                    margin-top: 18px;
                    line-height: 1.5;
                }}

                .advisor-box p,
                .wait-box p {{
                    font-size: 13px;
                }}

                .report-section,
                .prepayment-box,
                .strategy-optimizer,
                .timeline,
                .assumptions,
                .decision-grid {{
                    margin-top: 20px;
                    overflow: visible;
                }}

                .report-section h2,
                .prepayment-box h2,
                .strategy-optimizer h2,
                .timeline h2,
                .assumptions h2,
                .health-box h2,
                .wait-box h2 {{
                    margin-bottom: 10px;
                    font-size: 18px;
                }}

                .chart-frame {{
                    display: none;
                }}

                .pdf-chart {{
                    display: block;
                    padding: 12px;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    background: #ffffff;
                    break-inside: avoid;
                }}

                .comparison-table {{
                    min-width: 0;
                    width: 100%;
                    table-layout: fixed;
                    font-size: 10px;
                    box-shadow: none;
                    break-inside: avoid;
                }}

                .comparison-table th,
                .comparison-table td {{
                    padding: 7px;
                    overflow-wrap: anywhere;
                }}

                .savings-pill {{
                    min-width: 0;
                    padding: 4px 6px;
                    white-space: normal;
                }}

                .prepayment-card,
                .strategy-card {{
                    padding: 12px;
                    border-radius: 8px;
                }}

                .prepayment-card strong,
                .strategy-card strong {{
                    font-size: 16px;
                }}

                .strategy-card strong {{
                    margin: 4px 0 2px;
                }}

                .strategy-card span,
                .strategy-card small {{
                    line-height: 1.25;
                    font-size: 10px;
                }}

                .best-option,
                .optimizer-result {{
                    padding: 12px;
                    font-size: 15px;
                    border-radius: 8px;
                }}
            }}
        </style>

    </head>

    <body>

        <div class="report">

            <h1>Loan Advisor Report</h1>

            <section class="customer-details">
                <div class="customer-detail">
                    <span>Customer Name</span>
                    <strong>{customer_name}</strong>
                </div>
                <div class="customer-detail">
                    <span>Phone Number</span>
                    <strong>{customer_phone}</strong>
                </div>
                <div class="customer-detail">
                    <span>Email Address</span>
                    <strong>{customer_email}</strong>
                </div>
            </section>

            <div class="row">
                <div>Loan Amount</div>
                <div>{format_money(loan_amount)}</div>
            </div>

            <div class="row">
                <div>Current Rate</div>
                <div>{current_rate}%</div>
            </div>

            <div class="row">
                <div>New Rate</div>
                <div>{new_rate}%</div>
            </div>

            <div class="cards">
                <div class="card">
                     <h3>Monthly Saving</h3>
                    <p>{format_money(monthly_saving)}</p>
                </div>

                <div class="card">
                    <h3>Net Saving</h3>
                     <p>{format_money(net_savings)}</p>
                </div>

                <div class="card">
                    <h3>Break Even</h3>
                    <p>{break_even_display}</p>
                </div>

                <div class="card">
                     <h3>ROI</h3>
                    <p>{roi_display}</p>
                </div>
            </div>

            <div class="recommendation {recommendation_class}">
                {recommendation}
            </div>

            <div class="transfer-score">
                <div class="score-number">{transfer_score}/100</div>
                <div class="score-copy">
                    <h2>Optimize Transfer Score™</h2>
                    <div class="stars">{transfer_stars}</div>
                    <p>
                        Based on rate reduction, net savings,
                        break-even period, and transfer ROI.
                    </p>
                </div>
            </div>

            <div class="advisor-box">
                <h2>AI Loan Advisor</h2>

                <p>
                    Because the interest rate drops by
                    <b>{rate_drop:.1f}%</b>, switching your home loan
                    from <b>{current_rate:.1f}%</b> to
                    <b>{new_rate:.1f}%</b> could save approximately
                    <b>{net_savings_lakh}</b> over the remaining tenure.
                </p>

                <p>
                    The transfer cost of <b>{format_money(transfer_cost)}</b>
                    is <b>{recovery_text}</b>,
                    making this a refinancing opportunity
                    with an ROI of <b>{roi_display}</b>.
                </p>

                <p>
                    Recommendation:
                    <b>{recommendation}</b>
                </p>
            </div>

            <section class="report-section">
                <h2>Savings Chart</h2>
                <iframe
                    class="chart-frame"
                    src="savings_chart.html"
                    title="Balance Transfer Savings Chart"
                ></iframe>
                <div class="pdf-chart">
                    {pdf_savings_bars}
                </div>
            </section>

            <section class="report-section">
                <h2>Bank Comparison</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Current Bank</th>
                            <th>New Bank</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Interest Rate</td>
                            <td>{current_rate:.1f}%</td>
                            <td>{new_rate:.1f}%</td>
                        </tr>
                        <tr>
                            <td>EMI</td>
                            <td>{format_money(current_emi)}</td>
                            <td>{format_money(new_emi)}</td>
                        </tr>
                        <tr>
                            <td>Monthly Saving</td>
                            <td>—</td>
                            <td>{format_money(monthly_saving)}</td>
                        </tr>
                        <tr>
                            <td>Net Saving</td>
                            <td>—</td>
                            <td>{net_savings_lakh}</td>
                        </tr>
                    </tbody>
                </table>
            </section>

            <section class="report-section">
                <h2>Indicative Lender Recommendations</h2>
                <p class="disclaimer">
                    These are manually configured scenarios based on the entered
                    target rate, not live lender offers.
                </p>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Lender</th>
                            <th>Rate</th>
                            <th>Estimated EMI</th>
                            <th>Estimated Savings</th>
                            <th>Break-even</th>
                        </tr>
                    </thead>
                    <tbody>
                        {lender_rows}
                    </tbody>
                </table>
            </section>

            <section class="report-section">
                <h2>Rate Sensitivity Analysis</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>New Rate</th>
                            <th>Estimated EMI</th>
                            <th>Monthly Saving</th>
                            <th>Net Saving</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sensitivity_rows}
                    </tbody>
                </table>
            </section>

            <section class="report-section">
                <h2>Break-even Timeline</h2>
                <iframe
                    class="chart-frame"
                    src="break_even_chart.html"
                    title="Break-even Timeline Chart"
                ></iframe>
                <div class="pdf-chart">
                    {pdf_break_even_rows}
                </div>
            </section>

            <section class="decision-grid">
                <div class="health-box">
                    <h2>Loan Health Score™</h2>
                    <div class="health-score">
                        <strong>{loan_health_score}</strong>
                        <span>/ 100</span>
                    </div>
                    {health_rows}
                    <div class="confidence">
                        <span>Recommendation confidence</span>
                        <strong>{confidence_score}%</strong>
                        <div class="confidence-track">
                            <div
                                class="confidence-fill"
                                style="width: {confidence_score}%;"
                            ></div>
                        </div>
                    </div>
                </div>

                <div class="wait-box">
                    <h2>Should I Wait?</h2>
                    <div class="wait-answer">{wait_recommendation}</div>
                    <p>{wait_reason}</p>
                </div>
            </section>

            <section class="prepayment-box">
                <h2>Micro Prepayment Simulator</h2>
                <p>
                    See what happens when you add
                    <b>{format_money(extra_monthly_payment)}</b>
                    to the monthly payment after transferring the loan.
                </p>

                <div class="prepayment-grid">
                    <div class="prepayment-card">
                        <span>Original Tenure</span>
                        <strong>{prepayment_result["original_months"] / 12:.1f} years</strong>
                    </div>
                    <div class="prepayment-card">
                        <span>New Tenure</span>
                        <strong>{prepayment_result["new_tenure_years"]:.1f} years</strong>
                    </div>
                    <div class="prepayment-card">
                        <span>Interest Saved</span>
                        <strong>{interest_saved_lakh}</strong>
                    </div>
                    <div class="prepayment-card">
                        <span>EMIs Saved</span>
                        <strong>{prepayment_result["emis_saved"]} months</strong>
                    </div>
                </div>

                <div class="best-option">
                    Best Option: {best_option}
                </div>
            </section>

            <section class="strategy-optimizer">
                <h2>Strategy Optimizer</h2>
                <p>
                    Every option is compared against continuing the existing loan.
                </p>

                <div class="strategy-grid">
                    {strategy_cards}
                </div>

                <div class="optimizer-result">
                    Best Strategy: {best_option}
                    - Save {format_lakh(best_savings)}
                </div>
            </section>

            <section class="report-section">
                <h2>Strategy Comparison</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Strategy</th>
                            <th>Monthly Payment</th>
                            <th>Payoff Time</th>
                            <th>Interest + Transfer Cost</th>
                            <th>Total Savings</th>
                        </tr>
                    </thead>
                    <tbody>
                        {strategy_rows}
                    </tbody>
                </table>
            </section>

            <section class="timeline">
                <h2>Transfer Timeline</h2>
                <div class="timeline-item">
                    <strong>Today</strong>
                    <span>Pay transfer costs of {format_money(transfer_cost)}</span>
                </div>
                <div class="timeline-item">
                    <strong>Break-even: {break_even_display}</strong>
                    <span>Monthly savings recover the transfer cost.</span>
                </div>
                <div class="timeline-item">
                    <strong>Loan closes in {prepayment_result["new_tenure_years"]:.1f} years</strong>
                    <span>
                        Transfer plus {format_money(extra_monthly_payment)} monthly prepayment
                        removes {prepayment_result["emis_saved"]} EMIs.
                    </span>
                </div>
                <div class="timeline-item">
                    <strong>Total optimized savings: {format_lakh(best_savings)}</strong>
                    <span>Compared with continuing the existing loan unchanged.</span>
                </div>
            </section>

            <section class="assumptions">
                <h2>Assumptions</h2>
                <ul>
                    <li>Interest rates remain constant throughout the remaining tenure.</li>
                    <li>No foreclosure or prepayment penalties are applied.</li>
                    <li>Transfer costs include the processing and legal fees entered.</li>
                    <li>Regular EMI remains unchanged unless an extra payment is added.</li>
                    <li>Extra monthly payments are applied directly to principal.</li>
                    <li>Actual lender calculations may vary due to dates, rounding, and fees.</li>
                </ul>
            </section>

        </div>

    </body>
    </html>
    """

    with open(BASE_DIR / "report.html", "w", encoding="utf-8") as file:
        file.write(html)
