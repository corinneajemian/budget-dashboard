import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from paychecks import get_paychecks
from monthlyBudget import show_monthly_person
from incoming import show_incoming_tab


st.set_page_config(page_title="Budget App", layout="wide")

st.title("💸 Budget App")

# ---- Load Excel ----
accounts = pd.read_excel("BudgetFinances.xlsx", sheet_name="BudgetFinances")
incoming = pd.read_excel("BudgetFinances.xlsx", sheet_name="Incoming")
transactionsCorinne = pd.read_excel("BudgetFinances.xlsx", sheet_name="SpendingCorinne")
transactionsJoint = pd.read_excel("BudgetFinances.xlsx", sheet_name="SpendingJoint")
transactionsJohn = pd.read_excel("BudgetFinances.xlsx", sheet_name="SpendingJohn")
wishlist = pd.read_excel("BudgetFinances.xlsx", sheet_name="Wishlist")

wishlist["Cost"] = pd.to_numeric(wishlist["Cost"], errors="coerce")

# ---- Clean Accounts ----
accounts["Total"] = pd.to_numeric(accounts["Total"], errors="coerce")
accounts["Last Statement balance"] = pd.to_numeric(accounts["Last Statement balance"], errors="coerce")

# ---- Clean incoming ----
incoming["Due Date"] = pd.to_datetime(incoming["Due Date"], errors="coerce")
incoming["Total"] = pd.to_numeric(incoming["Total"], errors="coerce")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🥧 Corinne's Monthly Budget",
    "🥧 John's Monthly Budget",
    "🥧 Joint Monthly Budget",
    "💳 Accounts",
    "📅 Incoming",
    "🏡 Household Health",
    "✨ Wishlist"
])

with tab1:
    show_monthly_person("Corinne", accounts, transactionsCorinne, monthly_budget=1380)

with tab2:
    show_monthly_person("John", accounts, transactionsJohn, monthly_budget=1380)
# =========================
# 📅 Monthly Budget Joint
# =========================
with tab3:
    st.subheader("🥧 Joint Monthly Spending by Category")

    transactionsJoint["Date"] = pd.to_datetime(transactionsJoint["Date"], errors="coerce")
    transactionsJoint["Total"] = pd.to_numeric(transactionsJoint["Total"], errors="coerce")

    # Optional: month filter
    transactionsJoint["Month"] = transactionsJoint["Date"].dt.to_period("M").astype(str)
    month_options = ["All"] + sorted(transactionsJoint["Month"].dropna().unique().tolist())
    selected_month = st.selectbox(
        "Filter by month",
        month_options,
        key="joint_month_filter"
    )

    if selected_month != "All":
        tx_filtered = transactionsJoint[transactionsJoint["Month"] == selected_month]
    else:
        tx_filtered = transactionsJoint

    # --- Budget Setup ---
    monthly_budget = 2800

    total_spent = tx_filtered["Total"].sum()

    # New remaining calculation
    remaining = monthly_budget - total_spent

    # --- Days left in month ---
    today = datetime.date.today()
    end_of_month = datetime.date(today.year, today.month, 1)

    # move to next month then subtract 1 day
    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)

    end_of_month = next_month - datetime.timedelta(days=1)
    days_left = (end_of_month - today).days

    # --- Display ---
    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Total Spent", f"${total_spent:,.2f}")
    delta_color = "normal" if remaining >= 0 else "inverse"
    col2.metric(
        "💰 Remaining to Save",
        f"${remaining:,.2f}",
        delta=f"{remaining:,.2f}",
        delta_color=delta_color
    )
    col3.metric("📅 Days Left", f"{days_left} days")

    # ---- Pie Data ----
    category_totals = (
        tx_filtered
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    # ---- PIE CHART ----
    st.markdown("### 💸 Spending Breakdown")

    if not category_totals.empty:
        total_spent = tx_filtered["Total"].sum()

        fig3 = px.pie(
            category_totals,
            names="Category",
            values="Total",
            title=f"Spending by Category (Total: ${total_spent:,.2f})"
        )

        # 👇 THIS is the key part
        fig3.update_traces(
            textinfo="percent+label+value",   # shows % + category + $
            texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
        )

        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.info("No data available for selected month")

    # ---- TRANSACTION TABLE ----
    st.markdown("### 🧾 Transactions")

    st.dataframe(
        tx_filtered.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    st.metric("Total Spent", f"${tx_filtered['Total'].sum():,.2f}")

with tab5:
    show_incoming_tab(accounts, incoming)
# =========================
# 💳 ACCOUNTS TAB
# =========================
with tab4:
    st.subheader("Accounts")

    st.dataframe(accounts, use_container_width=True, hide_index=True)

    # Summary
    total_balance = accounts["Total"].sum()
    total_statement = accounts["Last Statement balance"].sum()

    col1, col2 = st.columns(2)
    col1.metric("💳 Total Balance", f"${total_balance:,.2f}")
    col2.metric("📄 Statement Balance", f"${total_statement:,.2f}")

    # Chart
    st.subheader("Balances by Account")

    accounts["Label"] = (
        accounts["Provider"] + " (" + accounts["Type"] + ")"
    )

    accounts = accounts.sort_values("Total", ascending=False)

    fig = px.bar(
        accounts,
        x="Label",
        y="Total",
        color="Owner",
        barmode="group",
        title="Balances by Account"
    )

    fig.update_layout(xaxis_tickangle=-30)

    st.plotly_chart(fig, use_container_width=True)
# =========================
# 🏡 Household Health Dashboard
# =========================
with tab6:
    st.subheader("🏡 Household Health Dashboard")

    # ---- Budgets ----
    corinne_budget = 1380
    john_budget = 1380
    joint_budget = 2800
    total_budget = corinne_budget + john_budget + joint_budget

    # ---- Clean spending data ----
    transactionsCorinne["Date"] = pd.to_datetime(transactionsCorinne["Date"], errors="coerce")
    transactionsCorinne["Total"] = pd.to_numeric(transactionsCorinne["Total"], errors="coerce")

    transactionsJohn["Date"] = pd.to_datetime(transactionsJohn["Date"], errors="coerce")
    transactionsJohn["Total"] = pd.to_numeric(transactionsJohn["Total"], errors="coerce")

    transactionsJoint["Date"] = pd.to_datetime(transactionsJoint["Date"], errors="coerce")
    transactionsJoint["Total"] = pd.to_numeric(transactionsJoint["Total"], errors="coerce")

    # ---- Month filter ----
    all_months = sorted(
        set(transactionsCorinne["Date"].dt.to_period("M").astype(str).dropna()) |
        set(transactionsJohn["Date"].dt.to_period("M").astype(str).dropna()) |
        set(transactionsJoint["Date"].dt.to_period("M").astype(str).dropna())
    )

    selected_month = st.selectbox(
        "Filter by month",
        ["All"] + all_months,
        key="household_month_filter"
    )

    def filter_by_month(df, selected_month):
        df = df.copy()
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        if selected_month != "All":
            return df[df["Month"] == selected_month]

        return df

    corinne_filtered = filter_by_month(transactionsCorinne, selected_month)
    john_filtered = filter_by_month(transactionsJohn, selected_month)
    joint_filtered = filter_by_month(transactionsJoint, selected_month)

    # ---- Totals ----
    corinne_spent = corinne_filtered["Total"].sum()
    john_spent = john_filtered["Total"].sum()
    joint_spent = joint_filtered["Total"].sum()

    total_spent = corinne_spent + john_spent + joint_spent
    remaining_budget = total_budget - total_spent

    # ---- Days left ----
    today = datetime.date.today()

    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)

    end_of_month = next_month - datetime.timedelta(days=1)
    days_left = max((end_of_month - today).days, 0)
    days_elapsed = today.day

    burn_rate = (total_spent-1000) / max(days_elapsed, 1)
    projected_month_end_spend = burn_rate * end_of_month.day
    projected_savings = total_budget - projected_month_end_spend

    daily_budget_remaining = remaining_budget / max(days_left, 1)

    # ---- Incoming paychecks ----
    paychecks = get_paychecks()

    paychecks["Due Date"] = pd.to_datetime(paychecks["Due Date"], errors="coerce")
    paychecks["Total"] = pd.to_numeric(paychecks["Total"], errors="coerce")

    future_paychecks = paychecks[paychecks["Due Date"] >= pd.Timestamp.today()]
    future_income = future_paychecks["Total"].sum()

    # ---- Debt ----
    total_debt = accounts["Total"].sum()

    projected_after_income = future_income - total_debt

    # ---- Top Metrics ----
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💸 Spent This Month", f"${total_spent:,.2f}")
    col2.metric("🎯 Monthly Budget", f"${total_budget:,.2f}")
    col3.metric("💰 Budget Remaining", f"${remaining_budget:,.2f}")
    col4.metric("📅 Days Left", f"{days_left} days")

    # ---- Burn / Savings Row ----
    col5, col6, col7, col8 = st.columns(4)

    col5.metric("🔥 Daily Burn Rate", f"${burn_rate:,.2f}/day")
    col6.metric("📊 Projected Month-End Spend", f"${projected_month_end_spend:,.2f}")
    col7.metric("✅ Projected Savings", f"${projected_savings:,.2f}")
    col8.metric("🧮 Daily Budget Left", f"${daily_budget_remaining:,.2f}/day")

    # ---- Household status ----
    st.markdown("### 🧠 Are we saving money this month?")

    if projected_savings > 0:
        st.success(f"Yes — at the current pace, you are projected to save about ${projected_savings:,.2f} this month.")
    elif projected_savings < 0:
        st.error(f"Not quite — at the current pace, you are projected to overspend by about ${abs(projected_savings):,.2f}.")
    else:
        st.info("You are projected to break even exactly this month.")

    # ---- Spending comparison chart ----
    spending_by_bucket = pd.DataFrame([
        {"Bucket": "Corinne", "Spent": corinne_spent, "Budget": corinne_budget},
        {"Bucket": "John", "Spent": john_spent, "Budget": john_budget},
        {"Bucket": "Joint", "Spent": joint_spent, "Budget": joint_budget},
    ])

    st.markdown("### 📊 Spending vs Budget")

    fig_health = px.bar(
        spending_by_bucket,
        x="Bucket",
        y=["Spent", "Budget"],
        barmode="group",
        title="Spending vs Budget by Bucket"
    )

    st.plotly_chart(fig_health, use_container_width=True)

    # ---- Combined transaction table ----
    st.markdown("### 🧾 Combined Transactions")

    corinne_table = corinne_filtered.copy()
    corinne_table["Budget Bucket"] = "Corinne"

    john_table = john_filtered.copy()
    john_table["Budget Bucket"] = "John"

    joint_table = joint_filtered.copy()
    joint_table["Budget Bucket"] = "Joint"

    combined_transactions = pd.concat(
        [corinne_table, john_table, joint_table],
        ignore_index=True
    )

    st.dataframe(
        combined_transactions.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )
# =========================
# ✨ Wishlist
# =========================
with tab7:
    st.subheader("✨ Wishlist")

    wishlist["Cost"] = pd.to_numeric(wishlist["Cost"], errors="coerce")

    owner_options = ["All"] + sorted(wishlist["Owner"].dropna().unique().tolist())
    selected_owner = st.selectbox(
        "Filter by owner",
        owner_options,
        key="wishlist_owner_filter"
    )

    priority_options = ["All"] + sorted(wishlist["Priority"].dropna().unique().tolist())
    selected_priority = st.selectbox(
        "Filter by priority",
        priority_options,
        key="wishlist_priority_filter"
    )

    wishlist_filtered = wishlist.copy()

    if selected_owner != "All":
        wishlist_filtered = wishlist_filtered[wishlist_filtered["Owner"] == selected_owner]

    if selected_priority != "All":
        wishlist_filtered = wishlist_filtered[wishlist_filtered["Priority"] == selected_priority]

    total_wishlist = wishlist_filtered["Cost"].sum()

    col1, col2 = st.columns(2)
    col1.metric("🛍️ Wishlist Total", f"${total_wishlist:,.2f}")
    col2.metric("📌 Items", len(wishlist_filtered))

    category_totals = (
        wishlist_filtered
        .groupby("Category")["Cost"]
        .sum()
        .reset_index()
        .sort_values("Cost", ascending=False)
    )

    st.markdown("### 💸 Wishlist by Category")

    if not category_totals.empty:
        fig_wishlist = px.pie(
            category_totals,
            names="Category",
            values="Cost",
            title=f"Wishlist by Category (Total: ${total_wishlist:,.2f})"
        )

        fig_wishlist.update_traces(
            textinfo="percent+label+value",
            texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
        )

        st.plotly_chart(fig_wishlist, use_container_width=True)
    else:
        st.info("No wishlist items match your filters.")

    st.markdown("### 🧾 Wishlist Items")

    st.dataframe(
        wishlist_filtered.sort_values("Cost", ascending=False),
        use_container_width=True,
        hide_index=True
    )