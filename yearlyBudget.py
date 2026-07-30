import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# Categories that should be tracked yearly instead of monthly
YEARLY_CATEGORIES = ["Travel", "Insurance", "Gifts", "Loans", "Ski", "Credit Card Annual Fees", "Mortgage"]

def filter_yearly_categories(transactions):
    """Filter transactions to only include yearly categories"""
    if "Category" not in transactions.columns:
        return pd.DataFrame()
    return transactions[transactions["Category"].isin(YEARLY_CATEGORIES)].copy()

def filter_monthly_categories(transactions):
    """Filter transactions to exclude yearly categories"""
    if "Category" not in transactions.columns:
        return transactions.copy()
    return transactions[~transactions["Category"].isin(YEARLY_CATEGORIES)].copy()

def show_yearly_budget(name, transactions, budget_df=None):
    """Display yearly budget for a person"""
    st.subheader(f"📅 {name}'s Yearly Spending")

    yearly_tx = filter_yearly_categories(transactions).copy()
    
    if yearly_tx.empty:
        st.info(f"No yearly category transactions found for {name}")
        return

    yearly_tx["Date"] = pd.to_datetime(yearly_tx["Date"], errors="coerce")
    yearly_tx["Total"] = pd.to_numeric(yearly_tx["Total"], errors="coerce")
    yearly_tx["Year"] = yearly_tx["Date"].dt.year.astype(str)

    # Get available years
    years = sorted(yearly_tx["Year"].dropna().unique().tolist(), reverse=True)
    current_year = str(pd.Timestamp.today().year)
    
    year_options = [current_year] + [y for y in years if y != current_year]
    
    selected_year = st.selectbox(
        "Filter by year",
        year_options,
        key=f"{name.lower()}_yearly_filter"
    )

    if selected_year == current_year:
        tx_filtered = yearly_tx[yearly_tx["Year"] == current_year]
    else:
        tx_filtered = yearly_tx[yearly_tx["Year"] == selected_year]

    total_spent = tx_filtered["Total"].sum()

    # Display metrics
    col1, col2 = st.columns(2)
    col1.metric("💸 Total Spent (Yearly Categories)", f"${total_spent:,.2f}")
    
    # Calculate days remaining in year
    today = datetime.date.today()
    end_of_year = datetime.date(today.year, 12, 31)
    days_left = (end_of_year - today).days
    col2.metric("📅 Days Left in Year", f"{days_left} days")

    # Pie Chart
    st.markdown("### 💸 Yearly Spending Breakdown")
    
    category_totals = (
        tx_filtered
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    if not category_totals.empty:
        fig = px.pie(
            category_totals,
            names="Category",
            values="Total",
            title=f"Yearly Spending by Category ({selected_year})"
        )
        
        fig.update_traces(
            textinfo="percent+label+value",
            texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Monthly breakdown
    st.markdown("### 📅 Spending by Month (Selected Year)")
    
    tx_filtered["Month"] = tx_filtered["Date"].dt.to_period("M").astype(str)
    monthly_totals = (
        tx_filtered
        .groupby("Month")["Total"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    if not monthly_totals.empty:
        fig_monthly = px.bar(
            monthly_totals,
            x="Month",
            y="Total",
            title=f"Yearly Categories Spending by Month ({selected_year})",
            labels={"Total": "Amount ($)", "Month": "Month"}
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    # Transactions table
    st.markdown("### 🧾 Transactions")
    
    # Normalize column names (strip whitespace)
    tx_filtered.columns = tx_filtered.columns.str.strip()
    
    # Check which columns are available
    available_cols = ["Date", "Category", "Total"]
    if "Transaction" in tx_filtered.columns:
        available_cols.insert(1, "Transaction")
    
    display_df = tx_filtered[available_cols].copy()
    display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d")
    
    st.dataframe(
        display_df.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )


def show_joint_yearly_budget(transactions):
    """Display yearly budget for joint spending"""
    st.subheader("📅 Joint Yearly Spending")

    yearly_tx = filter_yearly_categories(transactions).copy()
    
    if yearly_tx.empty:
        st.info("No yearly category transactions found for joint spending")
        return

    yearly_tx["Date"] = pd.to_datetime(yearly_tx["Date"], errors="coerce")
    yearly_tx["Total"] = pd.to_numeric(yearly_tx["Total"], errors="coerce")
    yearly_tx["Year"] = yearly_tx["Date"].dt.year.astype(str)

    # Get available years
    years = sorted(yearly_tx["Year"].dropna().unique().tolist(), reverse=True)
    current_year = str(pd.Timestamp.today().year)
    
    year_options = [current_year] + [y for y in years if y != current_year]
    
    selected_year = st.selectbox(
        "Filter by year",
        year_options,
        key="joint_yearly_filter"
    )

    if selected_year == current_year:
        tx_filtered = yearly_tx[yearly_tx["Year"] == current_year]
    else:
        tx_filtered = yearly_tx[yearly_tx["Year"] == selected_year]

    total_spent = tx_filtered["Total"].sum()

    # Display metrics
    col1, col2 = st.columns(2)
    col1.metric("💸 Total Spent (Yearly Categories)", f"${total_spent:,.2f}")
    
    # Calculate days remaining in year
    today = datetime.date.today()
    end_of_year = datetime.date(today.year, 12, 31)
    days_left = (end_of_year - today).days
    col2.metric("📅 Days Left in Year", f"{days_left} days")

    # Pie Chart
    st.markdown("### 💸 Yearly Spending Breakdown")
    
    category_totals = (
        tx_filtered
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )

    if not category_totals.empty:
        fig = px.pie(
            category_totals,
            names="Category",
            values="Total",
            title=f"Yearly Spending by Category ({selected_year})"
        )
        
        fig.update_traces(
            textinfo="percent+label+value",
            texttemplate="%{label}<br>%{percent}<br>$%{value:,.2f}"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Monthly breakdown
    st.markdown("### 📅 Spending by Month (Selected Year)")
    
    tx_filtered["Month"] = tx_filtered["Date"].dt.to_period("M").astype(str)
    monthly_totals = (
        tx_filtered
        .groupby("Month")["Total"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    if not monthly_totals.empty:
        fig_monthly = px.bar(
            monthly_totals,
            x="Month",
            y="Total",
            title=f"Yearly Categories Spending by Month ({selected_year})",
            labels={"Total": "Amount ($)", "Month": "Month"}
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    # Transactions table
    st.markdown("### 🧾 Transactions")
    
    # Normalize column names (strip whitespace)
    tx_filtered.columns = tx_filtered.columns.str.strip()
    
    # Check which columns are available
    available_cols = ["Date", "Category", "Total"]
    if "Transaction" in tx_filtered.columns:
        available_cols.insert(1, "Transaction")
    
    display_df = tx_filtered[available_cols].copy()
    display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d")
    
    st.dataframe(
        display_df.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )


def show_annual_spending_progress(transactions, budget_df, incoming=None):
    """Display annual spending progress with progress bars for each category"""
    st.subheader("📈 Annual Spending Progress by Category")
    
    # Extract YTD Income from incoming sheet
    ytd_income = 0
    if incoming is not None:
        incoming_clean = incoming.copy()
        incoming_clean.columns = incoming_clean.columns.str.strip()
        if "Year to Date Income" in incoming_clean.columns:
            ytd_income = pd.to_numeric(incoming_clean["Year to Date Income"].iloc[0], errors="coerce") or 0
    
    # Hardcoded annual budgets for specific categories
    hardcoded_budgets = {
        "Travel": 8500,
        "Loans": 17000
    }
    
    # Clean transactions
    transactions = transactions.copy()
    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")
    transactions["Total"] = pd.to_numeric(transactions["Total"], errors="coerce")
    
    # Filter to current year only
    current_year = pd.Timestamp.today().year
    transactions["Year"] = transactions["Date"].dt.year
    tx_current_year = transactions[transactions["Year"] == current_year]
    
    if tx_current_year.empty:
        st.info("No transactions found for current year")
        return
    
    # Clean budget data
    budget_df = budget_df.copy()
    budget_df.columns = budget_df.columns.str.strip()
    budget_df["Bucket"] = budget_df["Bucket"].astype(str).str.strip()
    budget_df["Budget"] = pd.to_numeric(budget_df["Budget"], errors="coerce")
    
    # Group transactions by category and sum
    category_spending = (
        tx_current_year
        .groupby("Category")["Total"]
        .sum()
        .reset_index()
        .sort_values("Total", ascending=False)
    )
    
    # Create progress data
    progress_data = []
    for idx, row in category_spending.iterrows():
        category = row["Category"]
        ytd_spending = row["Total"]
        
        # Check hardcoded budgets first, then fall back to budget_df
        if category in hardcoded_budgets:
            annual_budget = hardcoded_budgets[category]
        else:
            # Get monthly budget for this category
            budget_row = budget_df[budget_df["Bucket"] == category]
            if not budget_row.empty:
                monthly_budget = budget_row.iloc[0]["Budget"]
                annual_budget = monthly_budget * 12
            else:
                annual_budget = ytd_spending  # If no budget, use spending as annual budget
        
        # Calculate percentage
        percentage = min((ytd_spending / annual_budget * 100), 100) if annual_budget > 0 else 0
        
        progress_data.append({
            "Category": category,
            "YTD Spending": ytd_spending,
            "Annual Budget": annual_budget,
            "Percentage": percentage,
            "Remaining": max(annual_budget - ytd_spending, 0)
        })
    
    progress_df = pd.DataFrame(progress_data)
    
    # Display progress bars
    for idx, row in progress_df.iterrows():
        progress_value = min(row["Percentage"] / 100, 1.0)
        progress_percent = progress_value * 100
        remaining = row["Remaining"]
        
        progress_html = f"""
        <div style='margin: 6px 0;'>
            <div style='display: flex; align-items: flex-start; gap: 12px; margin-bottom: 2px;'>
                <div style='min-width: 90px; font-size: 13px; font-weight: bold;'>{row['Category']}</div>
                <div style='flex: 1;'>
                    <div style='font-size: 11px; color: #555; margin-bottom: 2px;'>
                        YTD: ${row['YTD Spending']:,.2f} | Budget: ${row['Annual Budget']:,.2f} | Used: {progress_percent:.1f}%
                    </div>
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <div style='min-width: 90px;'></div>
                <div style='flex: 1; height: 12px; background-color: #e0e0e0; border-radius: 6px; overflow: hidden;'>
                    <div style='height: 100%; width: {progress_percent}%; background-color: #2ecc71; border-radius: 6px; transition: width 0.3s;'></div>
                </div>
                <span style='font-size: 11px; min-width: 90px; text-align: right;'>{progress_percent:.1f}% • ${remaining:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(progress_html, unsafe_allow_html=True)
    
    # Summary stats
    st.markdown("### 📊 Summary")
    
    total_ytd = progress_df["YTD Spending"].sum()
    total_annual_budget = progress_df["Annual Budget"].sum()
    overall_percentage = (total_ytd / total_annual_budget * 100) if total_annual_budget > 0 else 0
    net_position = ytd_income - total_ytd
    
    # Format income and net position with green styling for positive values
    income_color = "#2ecc71" if ytd_income >= 0 else "#e74c3c"
    net_color = "#2ecc71" if net_position >= 0 else "#e74c3c"
    income_prefix = "+" if ytd_income >= 0 else ""
    net_prefix = "+" if net_position >= 0 else ""
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<p style='font-size: 13px;'><b>YTD Income:</b><br/><span style='color: {income_color};'>{income_prefix}${ytd_income:,.2f}</span></p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='font-size: 13px;'><b>Total Spent:</b><br/>${total_ytd:,.2f}</p>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<p style='font-size: 13px;'><b>Net Position:</b><br/><span style='color: {net_color};'>{net_prefix}${net_position:,.2f}</span></p>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<p style='font-size: 13px;'><b>Overall %:</b><br/>{overall_percentage:.1f}%</p>", unsafe_allow_html=True)
