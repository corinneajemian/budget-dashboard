import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

CATEGORY_COLORS = {
    "Loans": "#1f77b4",
    "Groceries": "#2ca02c",
    "Bills": "#ff7f0e",
    "House": "#8c564b",
    "Restaurants/Takeout": "#d62728",
    "Shopping": "#e377c2",
    "Health/Beauty": "#9467bd",
    "Alcohol": "#bcbd22",
    "Freya": "#17becf",
    "Coffee/Snacks": "#7f7f7f",
    "Gift": "#f781bf",
    "Transportation": "#aec7e8",
    "Auto": "#ffbb78",
    "Work Commuting": "#98df8a",
    "Savings": "#c5b0d5",
}

def make_budget_goal_pie(budget_df, person1_name, person2_name):

    top_level_buckets = [person1_name, person2_name, "Joint"]

    budget_df = budget_df.copy()
    budget_df.columns = budget_df.columns.str.strip()

    budget_df["Budget"] = pd.to_numeric(
        budget_df["Budget"],
        errors="coerce"
    )

    # Remove personal/joint total rows
    goal_category_totals = budget_df[
        ~budget_df["Bucket"].isin(top_level_buckets)
    ]

    fig_goal = px.pie(
        goal_category_totals,
        names="Bucket",
        values="Budget",
        title="Budget Goals by Category",
        color="Bucket",
        color_discrete_map=CATEGORY_COLORS
    )

    fig_goal.update_traces(
        textinfo="percent+label+value",
        texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
    )

    return fig_goal

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

    def get_budget(Bucket_name, fallback):
        match = budget_df.loc[
            budget_df["Bucket"] == Bucket_name,
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
    current_month = pd.Timestamp.today().to_period("M").strftime("%Y-%m")
    historical_months = [
        month
        for month in all_months
        if month != current_month
    ]

    selected_month = st.selectbox(
        "Filter by month",
        ["Current month", "All"] + historical_months,
        key="household_current_month_filter"
    )

    selected_month_value = (
        current_month if selected_month == "Current month" else selected_month
    )

    def filter_by_month(df):
        df = df.copy()
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        if selected_month_value != "All":
            return df[df["Month"] == selected_month_value]

        return df

    def without_credit_card_payoffs(df):
        if "Category" not in df.columns:
            return df

        is_credit_card_payoff = (
            df["Category"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "pay off credit cards"
        )

        return df[~is_credit_card_payoff]

    person1_filtered = filter_by_month(transactions1)
    person2_filtered = filter_by_month(transactions2)
    joint_filtered = filter_by_month(transactionsJoint)

    person1_spending = without_credit_card_payoffs(person1_filtered)
    person2_spending = without_credit_card_payoffs(person2_filtered)
    joint_spending = without_credit_card_payoffs(joint_filtered)

    # ---- Totals ----
    person1_spent = person1_spending["Total"].sum()
    person2_spent = person2_spending["Total"].sum()
    joint_spent = joint_spending["Total"].sum()

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

    # ---- Daily Household Spending ----
    st.markdown("### 📅 Household Spending by Day")

    combined_transactions["Date"] = pd.to_datetime(
        combined_transactions["Date"],
        errors="coerce"
    )

    if "Plan Ahead" in combined_transactions.columns:
        plan_ahead_values = (
            combined_transactions["Plan Ahead"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        combined_transactions["Is Plan Ahead"] = plan_ahead_values.isin(
            ["yes", "y", "true", "1"]
        )
    else:
        combined_transactions["Is Plan Ahead"] = False

    if "Category" in combined_transactions.columns:
        category_values = (
            combined_transactions["Category"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        combined_transactions["Is Pay Off Credit Cards"] = (
            category_values == "pay off credit cards"
        )
    else:
        combined_transactions["Is Pay Off Credit Cards"] = False

    spending_transactions = combined_transactions[
        ~combined_transactions["Is Pay Off Credit Cards"]
    ].copy()

    daily_spending = (
        spending_transactions
        .copy()
        .groupby(spending_transactions["Date"].dt.date)["Total"]
        .sum()
    )

    daily_spending_without_plan_ahead = (
        spending_transactions[~spending_transactions["Is Plan Ahead"]]
        .copy()
        .groupby(spending_transactions.loc[
            ~spending_transactions["Is Plan Ahead"],
            "Date"
        ].dt.date)["Total"]
        .sum()
    )

    # Create full date range for selected month
    if selected_month_value != "All":
        month_start = pd.to_datetime(f"{selected_month_value}-01")
        month_end = month_start + pd.offsets.MonthEnd(0)

        full_dates = pd.date_range(
            start=month_start,
            end=month_end,
            freq="D"
        )
    else:
        min_date = combined_transactions["Date"].min()
        max_date = combined_transactions["Date"].max()

        full_dates = pd.date_range(
            start=min_date,
            end=max_date,
            freq="D"
        )

    daily_spending = (
        daily_spending
        .reindex(full_dates.date, fill_value=0)
        .reset_index()
    )

    daily_spending.columns = ["Date", "Total"]

    daily_spending["Total Without Plan Ahead"] = (
        daily_spending_without_plan_ahead
        .reindex(full_dates.date, fill_value=0)
        .to_numpy()
    )

    daily_spending["Label"] = pd.to_datetime(
        daily_spending["Date"]
    ).dt.strftime("%a %b %d")

    daily_spending["Cumulative Total"] = daily_spending["Total"].cumsum()
    daily_spending["Cumulative Without Plan Ahead"] = (
        daily_spending["Total Without Plan Ahead"].cumsum()
    )

    daily_dates = pd.to_datetime(daily_spending["Date"])
    known_first_day_expenses = 0
    days_in_month = daily_dates.dt.days_in_month
    remaining_budget_after_known_expenses = total_budget - known_first_day_expenses

    daily_spending["Budget Pace"] = (
        known_first_day_expenses
        + (
            remaining_budget_after_known_expenses
            / (days_in_month - 1).clip(lower=1)
            * (daily_dates.dt.day - 1)
        )
    )

    average_daily_spend = daily_spending["Total"].mean()

    fig_daily_household = px.bar(
        daily_spending,
        x="Label",
        y="Total",
        title=f"Daily Household Spending (Avg: ${average_daily_spend:,.2f}/day)",
        text="Total"
    )

    fig_daily_household.update_traces(
        texttemplate="$%{text:,.2f}",
        textposition="outside"
    )

    fig_daily_household.add_scatter(
        x=daily_spending["Label"],
        y=daily_spending["Cumulative Total"],
        mode="lines+markers",
        name="Cumulative Month-to-Date",
        line={"color": "#c62828", "width": 3},
        marker={"size": 7},
        hovertemplate="Cumulative: $%{y:,.2f}<extra></extra>"
    )

    fig_daily_household.add_scatter(
        x=daily_spending["Label"],
        y=daily_spending["Cumulative Without Plan Ahead"],
        mode="lines+markers",
        name="Cumulative Without Plan Ahead",
        line={"color": "#7b1fa2", "width": 3},
        marker={"size": 7},
        hovertemplate="Without Plan Ahead: $%{y:,.2f}<extra></extra>"
    )

    fig_daily_household.add_scatter(
        x=daily_spending["Label"],
        y=daily_spending["Budget Pace"],
        mode="lines",
        name="Budget Pace",
        line={"color": "#2e7d32", "width": 3, "dash": "dash"},
        hovertemplate="Budget pace: $%{y:,.2f}<extra></extra>"
    )

    fig_daily_household.update_layout(
        yaxis_title="Amount Spent",
        xaxis_title="Day",
        legend_title_text=""
    )

    st.plotly_chart(
        fig_daily_household,
        use_container_width=True,
        key="household_daily_spending_chart"
    )

    top_level_buckets = [person1_name, person2_name, "Joint"]

    # Actual spending by category
    actual_category_totals = (
        spending_transactions
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    # Goal spending by category
    budget_df = budget_df.copy()
    budget_df.columns = budget_df.columns.str.strip()

    goal_category_totals = budget_df[
        ~budget_df["Bucket"].isin(top_level_buckets)
    ].copy()

    goal_category_totals["Budget"] = pd.to_numeric(
        goal_category_totals["Budget"],
        errors="coerce"
    )

    # ---- Pie Chart ----
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_actual = px.pie(
            actual_category_totals,
            names="Category",
            values="Total",
            title="Actual Spending by Category",
            color="Category",
            color_discrete_map=CATEGORY_COLORS
        )

        fig_actual.update_traces(
            texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
        )

        st.plotly_chart(
            fig_actual,
            use_container_width=True,
            key="household_actual_category_pie"
        )

    with col_chart2:
        st.markdown("### 🎯 Budget Goals")
        fig_goal = make_budget_goal_pie(budget_df, person1_name, person2_name)

        st.plotly_chart(
            fig_goal,
            use_container_width=True,
            key="household_budget_goal_pie"
        )
