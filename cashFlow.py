import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_cash_flow_table(accounts):
    """Display cash flow as a formatted table"""
    st.subheader("💰 Cash Flow Summary")
    
    accounts_clean = accounts.copy()
    accounts_clean.columns = accounts_clean.columns.str.strip()
    
    # Ensure numeric columns
    for col in ["Amount", "Paid/Due", "Still Due"]:
        if col in accounts_clean.columns:
            accounts_clean[col] = pd.to_numeric(accounts_clean[col], errors="coerce")
    
    # Display the table
    st.dataframe(accounts_clean, use_container_width=True, hide_index=True)
    
    # Calculate totals
    total_amount = accounts_clean["Amount"].sum()
    total_paid = accounts_clean["Paid/Due"].sum()
    total_still_due = accounts_clean["Still Due"].sum()
    net_cash = total_amount - total_still_due
    
    # Show summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Amount", f"${total_amount:,.2f}")
    with col2:
        st.metric("Total Paid", f"${total_paid:,.2f}")
    with col3:
        st.metric("Still Due", f"${total_still_due:,.2f}")
    with col4:
        color = "🟢" if net_cash >= 0 else "🔴"
        st.metric(f"{color} Net Cash", f"${net_cash:,.2f}")


def show_cash_flow_chart(accounts):
    """Display cash flow as a visual chart"""
    st.subheader("📊 Cash Flow Visualization")
    
    accounts_clean = accounts.copy()
    accounts_clean.columns = accounts_clean.columns.str.strip()
    
    # Ensure numeric columns
    for col in ["Amount", "Still Due"]:
        if col in accounts_clean.columns:
            accounts_clean[col] = pd.to_numeric(accounts_clean[col], errors="coerce")
    
    # Filter to only rows with data
    accounts_clean = accounts_clean.dropna(subset=["Amount"])
    
    # Create stacked bar chart: Amount vs Still Due
    chart_data = accounts_clean[["Amount", "Still Due"]].sum().reset_index()
    chart_data.columns = ["Category", "Amount"]
    
    fig = go.Figure(data=[
        go.Bar(name="Still Due", x=["Bills"], y=[accounts_clean["Still Due"].sum()], marker_color="#e74c3c"),
        go.Bar(name="Paid/Available", x=["Bills"], y=[accounts_clean["Amount"].sum() - accounts_clean["Still Due"].sum()], marker_color="#2ecc71")
    ])
    
    fig.update_layout(
        barmode="stack",
        title="Cash Available vs Bills Due",
        xaxis_title="",
        yaxis_title="Amount ($)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary
    total_amount = accounts_clean["Amount"].sum()
    total_still_due = accounts_clean["Still Due"].sum()
    net_cash = total_amount - total_still_due
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<p style='font-size: 16px; text-align: center;'><b>💵 Cash Available</b><br/><span style='color: #2ecc71; font-size: 20px;'>${total_amount - total_still_due:,.2f}</span></p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='font-size: 16px; text-align: center;'><b>📋 Bills Due</b><br/><span style='color: #e74c3c; font-size: 20px;'>${total_still_due:,.2f}</span></p>", unsafe_allow_html=True)
    with col3:
        color = "#2ecc71" if net_cash >= 0 else "#e74c3c"
        prefix = "+" if net_cash >= 0 else ""
        st.markdown(f"<p style='font-size: 16px; text-align: center;'><b>💎 Net Position</b><br/><span style='color: {color}; font-size: 20px;'>{prefix}${net_cash:,.2f}</span></p>", unsafe_allow_html=True)


def show_cash_flow_metrics(accounts):
    """Display cash flow as simple metrics"""
    st.subheader("🎯 Cash Position")
    
    accounts_clean = accounts.copy()
    accounts_clean.columns = accounts_clean.columns.str.strip()
    
    # Ensure numeric columns
    for col in ["Amount", "Paid/Due", "Still Due"]:
        if col in accounts_clean.columns:
            accounts_clean[col] = pd.to_numeric(accounts_clean[col], errors="coerce")
    
    total_amount = accounts_clean["Amount"].sum()
    total_paid = accounts_clean["Paid/Due"].sum()
    total_still_due = accounts_clean["Still Due"].sum()
    net_cash = total_amount - total_still_due
    
    # Display as large metrics
    col1, col2 = st.columns(2)
    
    with col1:
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            st.metric("💰 Cash on Hand", f"${total_amount:,.2f}")
        with col1_2:
            st.metric("✅ Already Paid", f"${total_paid:,.2f}")
    
    with col2:
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            st.metric("⏳ Still Due", f"${total_still_due:,.2f}")
        with col2_2:
            color = "green" if net_cash >= 0 else "red"
            st.metric("💎 Net Position", f"${net_cash:,.2f}", delta=f"Can pay bills: {'Yes ✓' if net_cash >= 0 else 'Need funds ⚠️'}")
    
    # Show breakdown by item if needed
    st.markdown("### Breakdown by Account")
    
    breakdown = accounts_clean[["Amount", "Paid/Due", "Still Due"]].copy()
    breakdown["Status"] = breakdown.apply(
        lambda row: "✅ Paid" if row["Still Due"] == 0 else f"⏳ ${row['Still Due']:,.2f} due",
        axis=1
    )
    
    st.dataframe(breakdown, use_container_width=True, hide_index=True)
