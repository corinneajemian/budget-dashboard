import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from monthlyBudget import show_monthly_person
from incoming import show_incoming_tab
from householdHealth import show_household_health
from yearlyBudget import show_joint_yearly_budget, filter_monthly_categories, show_annual_spending_progress


st.set_page_config(page_title="Budget App", layout="wide")

st.title("💸 Budget App")
# =========================
# 👤 User Setup
# =========================

num_people = st.radio(
    "How many people are using this budget sheet?",
    [2, 1],
    horizontal=True
)

person1_name = st.text_input("Person 1 Name", value="Corinne")

if num_people == 2:
    person2_name = st.text_input("Person 2 Name", value="John")
else:
    person2_name = None

data_source = st.text_input(
    "Excel file name",
    value="BudgetFinances.xlsx",
    help="Enter the Excel file name exactly as it appears in this folder."
)

person1_sheet = "Spending" + person1_name

person2_sheet = "Spending" + person2_name

# ---- Load Excel ----
try:
    budget = pd.read_excel(data_source, sheet_name="MonthlyBudget")
    accounts = pd.read_excel(data_source, sheet_name="Accounts")
    incoming = pd.read_excel(data_source, sheet_name="Incoming")

    transactions1 = pd.read_excel(data_source, sheet_name=person1_sheet)

    if num_people == 2:
        transactions2 = pd.read_excel(data_source, sheet_name=person2_sheet)

    transactionsJoint = pd.read_excel(data_source, sheet_name="SpendingJoint")

except FileNotFoundError:
    st.error(f"Could not find `{data_source}`.")
    st.stop()

except PermissionError:
    st.error(
        f"Could not open `{data_source}` because it is being used by another program. "
        "Close the Excel file, wait a moment for OneDrive to finish syncing, then refresh this page."
    )
    st.stop()

except ValueError as e:
    st.error(f"Excel sheet error: {e}")
    st.stop()

# ---- Clean Accounts ----
accounts["Total"] = pd.to_numeric(accounts["Total"], errors="coerce")
accounts["Last Statement balance"] = pd.to_numeric(accounts["Last Statement balance"], errors="coerce")

# ---- Clean incoming TODO might deleter this, seem unimportant ----
incoming["Due Date"] = pd.to_datetime(incoming["Due Date"], errors="coerce")
incoming["Total"] = pd.to_numeric(incoming["Total"], errors="coerce")

tab_names = [
    f"{'💑' if num_people == 2 else '💰'} {person1_name}'s Monthly Budget"
]

if num_people == 2:
    tab_names.append(f"💑 {person2_name}'s Monthly Budget")

tab_names.extend([
    f"{'💑' if num_people == 2 else '💰'} Joint Monthly Budget",
    "📅 Joint Yearly Budget",
    "Annual Spending Progress",
    "💳 Accounts",
    "🏡 Household Health",
    "✨ Wishlist"
])

tabs = st.tabs(tab_names)
tab1 = tabs[0]

if num_people == 2:
    tab2 = tabs[1]
    tab_joint_monthly = tabs[2]
    tab_joint_yearly = tabs[3]
    tab_annual_progress = tabs[4]
    tab_accounts = tabs[5]
    tab_household = tabs[6]
    tab_wishlist = tabs[7]
else:
    tab_joint_monthly = tabs[1]
    tab_joint_yearly = tabs[2]
    tab_annual_progress = tabs[3]
    tab_accounts = tabs[4]
    tab_household = tabs[5]
    tab_wishlist = tabs[6]

with tab1:
    show_monthly_person(person1_name, accounts, incoming, transactions1, budget)

if num_people == 2:
    with tab2:
        show_monthly_person(person2_name, accounts, incoming, transactions2, budget)

# =========================
# 📅 Monthly Budget Joint
# =========================
with tab_joint_monthly:
    st.subheader("🥧 Joint Monthly Spending by Category")

    transactionsJoint_monthly = filter_monthly_categories(transactionsJoint)
    transactionsJoint_monthly["Date"] = pd.to_datetime(transactionsJoint_monthly["Date"], errors="coerce")
    transactionsJoint_monthly["Total"] = pd.to_numeric(transactionsJoint_monthly["Total"], errors="coerce")

    # Optional: month filter
    transactionsJoint_monthly["Month"] = transactionsJoint_monthly["Date"].dt.to_period("M").astype(str)
    current_month = pd.Timestamp.today().to_period("M").strftime("%Y-%m")
    historical_months = [
        month
        for month in sorted(transactionsJoint_monthly["Month"].dropna().unique().tolist())
        if month != current_month
    ]
    month_options = ["Current month", "All"] + historical_months
    selected_month = st.selectbox(
        "Filter by month",
        month_options,
        key="joint_current_month_filter"
    )

    selected_month_value = (
        current_month if selected_month == "Current month" else selected_month
    )

    if selected_month_value != "All":
        tx_filtered = transactionsJoint_monthly[
            transactionsJoint_monthly["Month"] == selected_month_value
        ]
    else:
        tx_filtered = transactionsJoint_monthly

    # --- Budget Setup ---
    monthly_budget = 1000  # fallback if Joint is missing

    if budget is not None:
        budget = budget.copy()
        budget.columns = budget.columns.str.strip()
        budget["Bucket"] = budget["Bucket"].astype(str).str.strip()
        budget["Budget Monthly"] = pd.to_numeric(budget["Budget Monthly"], errors="coerce")

        matching_budget = budget.loc[
            budget["Bucket"] == "Joint",
            "Budget Monthly"
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

# =========================
# 📅 Yearly Budget Joint
# =========================
with tab_joint_yearly:
    # Combine all transactions for yearly budget
    all_transactions = pd.concat([transactions1, transactions2, transactionsJoint], ignore_index=True)
    show_joint_yearly_budget(all_transactions)

# =========================
# 📈 Annual Spending Progress
# =========================
with tab_annual_progress:
    # Combine all transactions for annual progress
    all_transactions = pd.concat([transactions1, transactions2, transactionsJoint], ignore_index=True)
    show_annual_spending_progress(all_transactions, budget, incoming)

with tab_accounts:
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

with tab_household:
    show_household_health(
        accounts,
        incoming,
        filter_monthly_categories(transactions1),
        filter_monthly_categories(transactions2),
        filter_monthly_categories(transactionsJoint),
        budget,
        person1_name,
        person2_name
    )
# =========================
# ✨ Wishlist
# =========================
with tab_wishlist:
    st.subheader("✨ Wishlist")

    wishlist_sources = []

    person1_wishlist = transactions1.copy()
    person1_wishlist["Budget Bucket"] = person1_name
    wishlist_sources.append(person1_wishlist)

    if num_people == 2:
        person2_wishlist = transactions2.copy()
        person2_wishlist["Budget Bucket"] = person2_name
        wishlist_sources.append(person2_wishlist)

    joint_wishlist = transactionsJoint.copy()
    joint_wishlist["Budget Bucket"] = "Joint"
    wishlist_sources.append(joint_wishlist)

    wishlist = pd.concat(wishlist_sources, ignore_index=True)
    wishlist.columns = wishlist.columns.str.strip()

    if "Plan Ahead" not in wishlist.columns:
        st.info(
            "Add a `Plan Ahead` column to the spending tabs and enter `Yes` "
            "for rows you want to include here."
        )
        st.stop()

    wishlist["Date"] = pd.to_datetime(wishlist["Date"], errors="coerce")
    wishlist["Total"] = pd.to_numeric(wishlist["Total"], errors="coerce").fillna(0)
    wishlist["Plan Ahead"] = wishlist["Plan Ahead"].astype(str).str.strip().str.lower()
    wishlist["Is Plan Ahead"] = wishlist["Plan Ahead"].isin(["yes", "y", "true", "1"])
    wishlist["Month"] = wishlist["Date"].dt.to_period("M").astype(str)

    current_month = pd.Timestamp.today().to_period("M").strftime("%Y-%m")
    historical_months = [
        month
        for month in sorted(wishlist["Month"].dropna().unique().tolist())
        if month not in [current_month, "NaT"]
    ]
    month_options = ["Current month", "All"] + historical_months
    selected_month = st.selectbox(
        "Filter by month",
        month_options,
        key="wishlist_current_month_filter"
    )

    selected_month_value = (
        current_month if selected_month == "Current month" else selected_month
    )

    if selected_month_value != "All":
        wishlist = wishlist[wishlist["Month"] == selected_month_value]

    owner_column = "Owner" if "Owner" in wishlist.columns else "Budget Bucket"
    owner_options = ["All"] + sorted(wishlist[owner_column].dropna().unique().tolist())
    selected_owner = st.selectbox(
        "Filter by owner",
        owner_options,
        key="wishlist_owner_filter"
    )

    wishlist_filtered = wishlist.copy()

    if selected_owner != "All":
        wishlist_filtered = wishlist_filtered[
            wishlist_filtered[owner_column] == selected_owner
        ]

    if "Priority" in wishlist.columns:
        priority_options = ["All"] + sorted(wishlist["Priority"].dropna().unique().tolist())
        selected_priority = st.selectbox(
            "Filter by priority",
            priority_options,
            key="wishlist_priority_filter"
        )

        if selected_priority != "All":
            wishlist_filtered = wishlist_filtered[
                wishlist_filtered["Priority"] == selected_priority
            ]

    spending_filtered = wishlist_filtered.copy()
    wishlist_filtered = spending_filtered[spending_filtered["Is Plan Ahead"]].copy()
    actual_spending_filtered = spending_filtered[
        ~spending_filtered["Is Plan Ahead"]
    ].copy()

    total_wishlist = wishlist_filtered["Total"].sum()

    col1, col2 = st.columns(2)
    col1.metric("🛍️ Wishlist Total", f"${total_wishlist:,.2f}")
    col2.metric("📌 Items", len(wishlist_filtered))

    category_totals = (
        wishlist_filtered
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    actual_category_totals = (
        actual_spending_filtered
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .rename(columns={"Total": "Spent this month"})
    )

    st.markdown("### 💸 Wishlist vs Budget by Category")

    budget_by_category = budget.copy()
    budget_by_category.columns = budget_by_category.columns.str.strip()
    budget_by_category["Bucket"] = budget_by_category["Bucket"].astype(str).str.strip()
    
    # Handle both Budget Monthly and Budget column names
    if "Budget Monthly" in budget_by_category.columns:
        budget_by_category["Budget"] = pd.to_numeric(
            budget_by_category["Budget Monthly"],
            errors="coerce"
        ).fillna(0)
    else:
        budget_by_category["Budget"] = pd.to_numeric(
            budget_by_category["Budget"],
            errors="coerce"
        ).fillna(0)

    top_level_buckets = [person1_name, "Joint"]

    if person2_name is not None:
        top_level_buckets.append(person2_name)

    budget_by_category = (
        budget_by_category[
            ~budget_by_category["Bucket"].isin(top_level_buckets)
        ]
        .groupby("Bucket")["Budget"]
        .sum()
        .reset_index()
        .rename(columns={
            "Bucket": "Category",
            "Budget": "Budget"
        })
    )

    wishlist_budget_table = (
        category_totals.rename(
            columns={"Total": "Planned"}
        )
        .merge(budget_by_category, on="Category", how="outer")
        .merge(actual_category_totals, on="Category", how="outer")
        .fillna(0)
        .rename(columns={"Spent this month": "Spent"})
    )

    wishlist_budget_table["Left"] = (
        wishlist_budget_table["Budget"]
        - wishlist_budget_table["Spent"]
        - wishlist_budget_table["Planned"]
    )

    adjustment_exempt_categories = ["Groceries"]

    total_over_budget = abs(
        wishlist_budget_table.loc[
            wishlist_budget_table["Left"] < 0,
            "Left"
        ].sum()
    )

    total_available_room = wishlist_budget_table.loc[
        (
            wishlist_budget_table["Left"] > 0
        ) & (
            ~wishlist_budget_table["Category"].isin(adjustment_exempt_categories)
        ),
        "Left"
    ].sum()

    wishlist_budget_table["Adjustment amount"] = 0.0

    if total_over_budget > 0 and total_available_room > 0:
        has_room = (
            wishlist_budget_table["Left"] > 0
        ) & (
            ~wishlist_budget_table["Category"].isin(adjustment_exempt_categories)
        )
        wishlist_budget_table.loc[has_room, "Adjustment amount"] = (
            wishlist_budget_table.loc[has_room, "Left"]
            / total_available_room
            * total_over_budget
            * -1
        )

    wishlist_budget_table["Adjusted Left"] = (
        wishlist_budget_table["Left"]
        + wishlist_budget_table["Adjustment amount"]
    ).round(2)

    money_columns = [
        "Budget",
        "Spent",
        "Planned",
        "Left"
    ]

    wishlist_budget_table[money_columns] = wishlist_budget_table[money_columns].round(2)

    wishlist_budget_table = wishlist_budget_table.sort_values(
        "Planned",
        ascending=False
    ).set_index("Category")

    wishlist_budget_table = wishlist_budget_table[
        [
            "Budget",
            "Spent",
            "Planned",
            "Left",
            "Adjusted Left"
        ]
    ]

    total_values = wishlist_budget_table.sum(numeric_only=True)
    total_values["Left"] = wishlist_budget_table[
        "Left"
    ].clip(lower=0).sum()
    total_values["Adjusted Left"] = wishlist_budget_table[
        "Adjusted Left"
    ].clip(lower=0).sum()

    total_row = pd.DataFrame([total_values], index=["Total"])

    wishlist_budget_table = pd.concat([wishlist_budget_table, total_row])

    def highlight_wishlist_difference(row):
        budgeted = row["Budget"]
        planned = row["Planned"]
        difference = row["Left"]

        if budgeted == 0:
            color = "#c62828" if planned > 0 else "#616161"
        elif difference >= 0:
            color = "#2e7d32"
        elif difference >= budgeted * -0.10:
            color = "#f57c00"
        else:
            color = "#c62828"

        return [f"color: {color}; font-weight: 600"] * len(row)

    if not wishlist_budget_table.empty:
        st.dataframe(
            wishlist_budget_table
            .style
            .apply(highlight_wishlist_difference, axis=1)
            .set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("white-space", "normal"),
                        ("word-wrap", "break-word"),
                        ("max-width", "120px")
                    ]
                }
            ])
            .format({
                "Budget": "${:,.2f}",
                "Spent": "${:,.2f}",
                "Planned": "${:,.2f}",
                "Left": lambda value: (
                    f"${value:,.2f}" if value >= 0 else f"-${abs(value):,.2f}"
                ),
                "Adjusted Left": lambda value: (
                    f"${value:,.2f}" if value >= 0 else f"-${abs(value):,.2f}"
                )
            }),
            use_container_width=True
        )
    else:
        st.info("No wishlist items match your filters.")

    st.markdown("### 🧾 Wishlist Items")

    wishlist_item_columns = [
        "Date",
        "Budget Bucket",
        "Owner",
        "Category",
        "Description",
        "Item",
        "Name",
        "Vendor",
        "Priority",
        "Notes",
        "Total"
    ]
    wishlist_item_columns = [
        column
        for column in wishlist_item_columns
        if column in wishlist_filtered.columns
    ]

    wishlist_items_display = (
        wishlist_filtered
        .sort_values("Total", ascending=False)
        .loc[:, wishlist_item_columns]
    )

    st.dataframe(
        wishlist_items_display,
        use_container_width=True,
        hide_index=True
    )
