import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from monthlyBudget import show_monthly_person
from incoming import show_incoming_tab
from householdHealth import show_household_health


st.set_page_config(page_title="Budget App", layout="wide")

st.title("💸 Budget App")
# =========================
# 👤 User Setup
# =========================

num_people = st.radio(
    "How many people are using this budget sheet?",
    [1, 2],
    horizontal=True
)

person1_name = st.text_input("Person 1 Name", value="Person 1")

if num_people == 2:
    person2_name = st.text_input("Person 2 Name", value="Person 2")
else:
    person2_name = None

data_source = st.text_input(
    "Excel file name",
    value="BudgetFinances_template.xlsx",
    help="Enter the Excel file name exactly as it appears in this folder."
)

person1_sheet = "Spending" + person1_name

person2_sheet = "Spending" + person2_name

# ---- Load Excel ----
try:
    budget = pd.read_excel(data_source, sheet_name="MonthlyBudget")
    accounts = pd.read_excel(data_source, sheet_name="BudgetFinances")
    incoming = pd.read_excel(data_source, sheet_name="Incoming")

    transactions1 = pd.read_excel(data_source, sheet_name=person1_sheet)

    if num_people == 2:
        transactions2 = pd.read_excel(data_source, sheet_name=person2_sheet)

    transactionsJoint = pd.read_excel(data_source, sheet_name="SpendingJoint")
    wishlist = pd.read_excel(data_source, sheet_name="Wishlist")

except FileNotFoundError:
    st.error(f"Could not find `{data_source}`.")
    st.stop()

except ValueError as e:
    st.error(f"Excel sheet error: {e}")
    st.stop()

wishlist["Cost"] = pd.to_numeric(wishlist["Cost"], errors="coerce")

# ---- Clean Accounts ----
accounts["Total"] = pd.to_numeric(accounts["Total"], errors="coerce")
accounts["Last Statement balance"] = pd.to_numeric(accounts["Last Statement balance"], errors="coerce")

# ---- Clean incoming ----
incoming["Due Date"] = pd.to_datetime(incoming["Due Date"], errors="coerce")
incoming["Total"] = pd.to_numeric(incoming["Total"], errors="coerce")

tab_names = [
    f"🥧 {person1_name}'s Monthly Budget"
]

if num_people == 2:
    tab_names.append(f"🥧 {person2_name}'s Monthly Budget")

tab_names.extend([
    "🥧 Joint Monthly Budget",
    "💳 Accounts",
    "📅 Incoming",
    "🏡 Household Health",
    "✨ Wishlist"
])

tabs = st.tabs(tab_names)
tab1 = tabs[0]

if num_people == 2:
    tab2 = tabs[1]
    tab3 = tabs[2]
    tab4 = tabs[3]
    tab5 = tabs[4]
    tab6 = tabs[5]
    tab7 = tabs[6]
else:
    tab3 = tabs[1]
    tab4 = tabs[2]
    tab5 = tabs[3]
    tab6 = tabs[4]
    tab7 = tabs[5]

with tab1:
    show_monthly_person(person1_name, accounts, incoming, transactions1, budget)

if num_people == 2:
    with tab2:
        show_monthly_person(person2_name, accounts, incoming, transactions2, budget)
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
    monthly_budget = 1000  # fallback if Joint is missing

    if budget is not None:
        budget = budget.copy()
        budget.columns = budget.columns.str.strip()
        budget["Owner"] = budget["Owner"].astype(str).str.strip()
        budget["Budget"] = pd.to_numeric(budget["Budget"], errors="coerce")

        matching_budget = budget.loc[
            budget["Owner"] == "Joint",
            "Budget"
        ]

        if not matching_budget.empty:
            monthly_budget = matching_budget.iloc[0]

    total_spent = tx_filtered["Total"].sum()
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

with tab5:
    show_incoming_tab(accounts, incoming)
# =========================
# 💳 ACCOUNTS TAB
# =========================
with tab6:
    show_household_health("Household", accounts, incoming, transactions1, budget)
    if num_people == 2:
        show_household_health("Household", accounts, incoming, transactions2, budget)
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