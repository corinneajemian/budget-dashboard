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
    col2.metric("📊 Balance + Incoming", f"${projected_balance:,.2f}")
    col3.metric("📅 Projected Through", latest_due_date_text)

    st.dataframe(incoming_filtered, use_container_width=True, hide_index=True)

    fig2 = px.bar(
        incoming_filtered,
        x="Due Date",
        y="Total",
        color="Owner",
        title="Incoming Transactions"
    )

    st.plotly_chart(fig2, use_container_width=True)
