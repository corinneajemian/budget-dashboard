import streamlit as st
import pandas as pd
import plotly.express as px
import datetime


def show_monthly_person(name, accounts, incoming, transactions, budget_df = None):
    st.subheader(f"🥧 {name}'s Monthly Spending by Category")

    # If budget sheet was provided, override it
    if budget_df is not None:
        budget_df.columns = budget_df.columns.str.strip()
        budget_df["Owner"] = budget_df["Owner"].astype(str).str.strip()

        matching_budget = budget_df.loc[
            budget_df["Owner"] == name,
            "Budget"
        ]

    if not matching_budget.empty:
        monthly_budget = matching_budget.iloc[0]
    transactions = transactions.copy()
    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")
    transactions["Total"] = pd.to_numeric(transactions["Total"], errors="coerce")

    transactions["Month"] = transactions["Date"].dt.to_period("M").astype(str)
    month_options = ["All"] + sorted(transactions["Month"].dropna().unique().tolist())

    selected_month = st.selectbox(
        "Filter by month",
        month_options,
        key=f"{name.lower()}_month_filter"
    )

    if selected_month != "All":
        tx_filtered = transactions[transactions["Month"] == selected_month]
    else:
        tx_filtered = transactions

    total_spent = tx_filtered["Total"].sum()
    remaining = monthly_budget - total_spent

    today = datetime.date.today()

    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)

    end_of_month = next_month - datetime.timedelta(days=1)
    days_left = (end_of_month - today).days

    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Total Spent", f"${total_spent:,.2f}")

    delta_color = "normal" if remaining >= 0 else "inverse"
    col2.metric(
        "💰 Remaining in Budget",
        f"${remaining:,.2f}",
        delta=f"${remaining:,.2f}",
        delta_color=delta_color
    )

    col3.metric("📅 Days Left", f"{days_left} days")

    # ---- Debt / Monthly Spend Room ----
    person_accounts = accounts[accounts["Owner"] == name]
    amount_owed = person_accounts["Total"].sum()

    today = pd.Timestamp.today()
    start_of_month = today.replace(day=1).normalize()
    start_of_next_month = (start_of_month + pd.offsets.MonthBegin(1)).normalize()

    incoming["Due Date"] = pd.to_datetime(incoming["Due Date"], errors="coerce")
    incoming["Total"] = pd.to_numeric(incoming["Total"], errors="coerce")

    person_paychecks = incoming[
        (incoming["Owner"] == name) &
        (incoming["Type"] == "Personal Checking") &
        (incoming["Due Date"] >= today.normalize()) &
        (incoming["Due Date"] < start_of_next_month)
    ]

    incoming_paychecks_total = person_paychecks["Total"].sum()

    # Your favorite formula:
    # Debt - Remaining Budget - Incoming Paychecks
    spend_room = amount_owed - remaining - incoming_paychecks_total

    col4, col5 = st.columns(2)

    col4.metric(f"💳 {name} Debt", f"${amount_owed:,.2f}")

    if spend_room > 0:
        label = "❌ Still Need to Cover"
        value = spend_room

    elif spend_room > -200:
        label = "⚠️ Left to Spend - Around Breakeven"
        value = min(abs(spend_room), remaining)

    else:
        label = "✅ Left to Spend This Month"
        value = min(abs(spend_room), remaining)

    col5.metric(label, f"${value:,.2f}")
    # ---- Pie Chart ----
    category_totals = (
        tx_filtered
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    st.markdown("### 💸 Spending Breakdown")

    if not category_totals.empty:
        fig = px.pie(
            category_totals,
            names="Category",
            values="Total",
            title=f"Spending by Category (Total: ${total_spent:,.2f})"
        )

        fig.update_traces(
            textinfo="percent+label+value",
            texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"{name.lower()}_spending_pie_chart"
        )
    else:
        st.info("No data available for selected month")

    st.markdown("### 🧾 Transactions")

    st.dataframe(
        tx_filtered.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )