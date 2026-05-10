import streamlit as st
import pandas as pd
import plotly.express as px
import datetime


def show_household_health(
    accounts,
    incoming,
    transactions1,
    transactions2,
    transactionsJoint,
    budget_df=None,
    person1_name="Person 1",
    person2_name="Person 2"
):

    st.subheader("🏡 Household Health Dashboard")

    # ---- Budget setup ----
    budget_df = budget_df.copy()
    budget_df.columns = budget_df.columns.str.strip()

    def get_budget(owner_name, fallback):
        match = budget_df.loc[
            budget_df["Owner"] == owner_name,
            "Budget"
        ]

        if not match.empty:
            return pd.to_numeric(match.iloc[0], errors="coerce")

        return fallback

    person1_budget = get_budget(person1_name, 1380)
    person2_budget = get_budget(person2_name, 1380)
    joint_budget = get_budget("Joint", 2800)

    total_budget = person1_budget + person2_budget + joint_budget

    # ---- Clean transactions ----
    for df in [transactions1, transactions2, transactionsJoint]:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Total"] = pd.to_numeric(df["Total"], errors="coerce")

    # ---- Month filter ----
    all_months = sorted(
        set(transactions1["Date"].dt.to_period("M").astype(str).dropna()) |
        set(transactions2["Date"].dt.to_period("M").astype(str).dropna()) |
        set(transactionsJoint["Date"].dt.to_period("M").astype(str).dropna())
    )

    selected_month = st.selectbox(
        "Filter by month",
        ["All"] + all_months,
        key="household_month_filter"
    )

    def filter_by_month(df):
        df = df.copy()
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        if selected_month != "All":
            return df[df["Month"] == selected_month]

        return df

    person1_filtered = filter_by_month(transactions1)
    person2_filtered = filter_by_month(transactions2)
    joint_filtered = filter_by_month(transactionsJoint)

    # ---- Totals ----
    person1_spent = person1_filtered["Total"].sum()
    person2_spent = person2_filtered["Total"].sum()
    joint_spent = joint_filtered["Total"].sum()

    total_spent = person1_spent + person2_spent + joint_spent

    remaining_budget = total_budget - total_spent

    # ---- Date math ----
    today = datetime.date.today()

    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)

    end_of_month = next_month - datetime.timedelta(days=1)

    days_left = max((end_of_month - today).days, 0)
    days_elapsed = max(today.day, 1)

    # ---- Burn rate ----
    burn_rate = total_spent / days_elapsed

    projected_month_end_spend = burn_rate * end_of_month.day

    projected_savings = total_budget - projected_month_end_spend

    daily_budget_remaining = remaining_budget / max(days_left, 1)

    # ---- Incoming ----
    incoming["Due Date"] = pd.to_datetime(incoming["Due Date"], errors="coerce")
    incoming["Total"] = pd.to_numeric(incoming["Total"], errors="coerce")

    future_income = incoming[
        incoming["Due Date"] >= pd.Timestamp.today()
    ]["Total"].sum()

    # ---- Debt ----
    total_debt = accounts["Total"].sum()

    projected_after_income = future_income - total_debt

    # ---- Metrics row 1 ----
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💸 Spent This Month", f"${total_spent:,.2f}")
    col2.metric("🎯 Monthly Budget", f"${total_budget:,.2f}")
    col3.metric("💰 Budget Remaining", f"${remaining_budget:,.2f}")
    col4.metric("📅 Days Left", f"{days_left} days")

    # ---- Metrics row 2 ----
    col5, col6, col7, col8 = st.columns(4)

    col5.metric("🔥 Daily Burn Rate", f"${burn_rate:,.2f}/day")
    col6.metric("📊 Projected Month-End Spend", f"${projected_month_end_spend:,.2f}")
    col7.metric("✅ Projected Savings", f"${projected_savings:,.2f}")
    col8.metric("🧮 Daily Budget Left", f"${daily_budget_remaining:,.2f}/day")

    # ---- Status ----
    st.markdown("### 🧠 Are we saving money this month?")

    if projected_savings > 0:
        st.success(
            f"Yes — at the current pace, you are projected to save about "
            f"${projected_savings:,.2f} this month."
        )

    elif projected_savings < 0:
        st.error(
            f"At the current pace, you are projected to overspend by about "
            f"${abs(projected_savings):,.2f}."
        )

    else:
        st.info("You are projected to break even this month.")

    # ---- Comparison chart ----
    spending_by_bucket = pd.DataFrame([
        {
            "Bucket": person1_name,
            "Spent": person1_spent,
            "Budget": person1_budget
        },
        {
            "Bucket": person2_name,
            "Spent": person2_spent,
            "Budget": person2_budget
        },
        {
            "Bucket": "Joint",
            "Spent": joint_spent,
            "Budget": joint_budget
        },
    ])

    st.markdown("### 📊 Spending vs Budget")

    fig_health = px.bar(
        spending_by_bucket,
        x="Bucket",
        y=["Spent", "Budget"],
        barmode="group",
        title="Spending vs Budget by Bucket"
    )

    st.plotly_chart(
        fig_health,
        use_container_width=True,
        key="household_spending_chart"
    )

    # ---- Combined table ----
    st.markdown("### 🧾 Combined Transactions")

    person1_table = person1_filtered.copy()
    person1_table["Budget Bucket"] = person1_name

    person2_table = person2_filtered.copy()
    person2_table["Budget Bucket"] = person2_name

    joint_table = joint_filtered.copy()
    joint_table["Budget Bucket"] = "Joint"

    combined_transactions = pd.concat(
        [person1_table, person2_table, joint_table],
        ignore_index=True
    )
    # ---- Pie Chart ----
    category_totals = (
        combined_transactions
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
            key=f"Combined_spending_pie_chart"
        )
    else:
        st.info("No data available for selected month")

    st.dataframe(
        combined_transactions.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )