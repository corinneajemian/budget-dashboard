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
    [2, 1],
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

except PermissionError:
    st.error(
        f"Could not open `{data_source}` because it is being used by another program. "
        "Close the Excel file, wait a moment for OneDrive to finish syncing, then refresh this page."
    )
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
        budget["Bucket"] = budget["Bucket"].astype(str).str.strip()
        budget["Budget"] = pd.to_numeric(budget["Budget"], errors="coerce")

        matching_budget = budget.loc[
            budget["Bucket"] == "Joint",
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

with tab6:
    show_household_health(
        accounts,
        incoming,
        transactions1,
        transactions2,
        transactionsJoint,
        budget,
        person1_name,
        person2_name
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

    st.markdown("### 💸 Wishlist vs Budget by Category")

    budget_by_category = budget.copy()
    budget_by_category.columns = budget_by_category.columns.str.strip()
    budget_by_category["Bucket"] = budget_by_category["Bucket"].astype(str).str.strip()
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
            "Budget": "How much we budgeted for each category"
        })
    )

    wishlist_budget_table = (
        category_totals.rename(
            columns={"Cost": "How much we wish to spend in each category"}
        )
        .merge(budget_by_category, on="Category", how="outer")
        .fillna(0)
    )

    wishlist_budget_table["Amount left to spend"] = (
        wishlist_budget_table["How much we budgeted for each category"]
        - wishlist_budget_table["How much we wish to spend in each category"]
    )

    adjustment_exempt_categories = ["Groceries"]

    total_over_budget = abs(
        wishlist_budget_table.loc[
            wishlist_budget_table["Amount left to spend"] < 0,
            "Amount left to spend"
        ].sum()
    )

    total_available_room = wishlist_budget_table.loc[
        (
            wishlist_budget_table["Amount left to spend"] > 0
        ) & (
            ~wishlist_budget_table["Category"].isin(adjustment_exempt_categories)
        ),
        "Amount left to spend"
    ].sum()

    wishlist_budget_table["Adjustment amount"] = 0.0

    if total_over_budget > 0 and total_available_room > 0:
        has_room = (
            wishlist_budget_table["Amount left to spend"] > 0
        ) & (
            ~wishlist_budget_table["Category"].isin(adjustment_exempt_categories)
        )
        wishlist_budget_table.loc[has_room, "Adjustment amount"] = (
            wishlist_budget_table.loc[has_room, "Amount left to spend"]
            / total_available_room
            * total_over_budget
            * -1
        )

    wishlist_budget_table["Amount left after adjustment"] = (
        wishlist_budget_table["Amount left to spend"]
        + wishlist_budget_table["Adjustment amount"]
    ).round(2)

    money_columns = [
        "How much we budgeted for each category",
        "How much we wish to spend in each category",
        "Amount left to spend"
    ]

    wishlist_budget_table[money_columns] = wishlist_budget_table[money_columns].round(2)

    wishlist_budget_table = wishlist_budget_table.sort_values(
        "How much we wish to spend in each category",
        ascending=False
    ).set_index("Category")

    wishlist_budget_table = wishlist_budget_table[
        [
            "How much we budgeted for each category",
            "How much we wish to spend in each category",
            "Amount left to spend",
            "Amount left after adjustment"
        ]
    ]

    total_values = wishlist_budget_table.sum(numeric_only=True)
    total_values["Amount left to spend"] = wishlist_budget_table[
        "Amount left to spend"
    ].clip(lower=0).sum()
    total_values["Amount left after adjustment"] = wishlist_budget_table[
        "Amount left after adjustment"
    ].clip(lower=0).sum()

    total_row = pd.DataFrame([total_values], index=["Total"])

    wishlist_budget_table = pd.concat([wishlist_budget_table, total_row])

    def highlight_wishlist_difference(row):
        budgeted = row["How much we budgeted for each category"]
        wished = row["How much we wish to spend in each category"]
        difference = row["Amount left to spend"]

        if budgeted == 0:
            color = "#c62828" if wished > 0 else "#616161"
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
                "How much we budgeted for each category": "${:,.2f}",
                "How much we wish to spend in each category": "${:,.2f}",
                "Amount left to spend": lambda value: (
                    f"${value:,.2f}" if value >= 0 else f"-${abs(value):,.2f}"
                ),
                "Amount left after adjustment": lambda value: (
                    f"${value:,.2f}" if value >= 0 else f"-${abs(value):,.2f}"
                )
            }),
            use_container_width=True
        )
    else:
        st.info("No wishlist items match your filters.")

    st.markdown("### 🧾 Wishlist Items")

    st.dataframe(
        wishlist_filtered.sort_values("Cost", ascending=False),
        use_container_width=True,
        hide_index=True
    )
