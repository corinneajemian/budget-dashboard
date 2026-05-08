import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# 📅 Incoming TAB
# =========================

def show_incoming_tab(accounts, incoming):
   
    st.subheader("Incoming Transactions")

    # Clean incoming columns
    incoming["Due Date"] = pd.to_datetime(incoming["Due Date"], errors="coerce")
    incoming["Total"] = pd.to_numeric(incoming["Total"], errors="coerce")

    # Create week grouping
    incoming["Week"] = incoming["Due Date"].dt.to_period("W").astype(str)

    week_options = ["All"] + sorted(incoming["Week"].dropna().unique().tolist())
    selected_week = st.selectbox("Filter by week", week_options)

    if selected_week != "All":
        incoming_filtered = incoming[incoming["Week"] == selected_week]
    else:
        incoming_filtered = incoming

    total_incoming = incoming_filtered["Total"].sum()

    # Account balance total
    total_balance = accounts["Total"].sum()

    # Projection
    projected_balance =  total_incoming - total_balance

    # Latest incoming charge date in current filter
    latest_due_date = incoming_filtered["Due Date"].max()

    if pd.notna(latest_due_date):
        latest_due_date_text = latest_due_date.strftime("%b %d, %Y")
    else:
        latest_due_date_text = "No date"

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Total Incoming", f"${total_incoming:,.2f}")
    col2.metric("📊 Credit Card Debt + Incoming", f"${projected_balance:,.2f}")
    col3.metric("📅 Projected Through", latest_due_date_text)

    st.dataframe(incoming_filtered, use_container_width=True, hide_index=True)

    # ---- Cash Flow Projection ----

    projection_df = incoming_filtered.copy()

    projection_df = projection_df.sort_values("Due Date")

    # Start at credit card debt and accumulate incoming transactions
    projection_df["Running Balance"] = (-total_balance + projection_df["Total"].cumsum())

    fig2 = px.line(
        projection_df,
        x="Due Date",
        y="Running Balance",
        markers=True,
        title="Projected Cash Flow Over Time"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        key="incoming_projection_chart"
    )
