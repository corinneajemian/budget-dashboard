import streamlit as st
import pandas as pd

def show_paycheck_editor(person1_name, person2_name=None):
    st.subheader("💰 Paycheck Setup")

    default_rows = [
        {
            "Provider": "",
            "Type": "Personal Checking",
            "Account": "",
            "Transaction": "Paycheck",
            "Total": 0.00,
            "Owner": person1_name,
            "Due Date": pd.Timestamp.today().date(),
        }
    ]

    if person2_name is not None:
        default_rows.append(
            {
                "Provider": "",
                "Type": "Personal Checking",
                "Account": "",
                "Transaction": "Paycheck",
                "Total": 0.00,
                "Owner": person2_name,
                "Due Date": pd.Timestamp.today().date(),
            }
        )

    default_paychecks = pd.DataFrame(default_rows)

    paychecks = st.data_editor(
        default_paychecks,
        num_rows="dynamic",
        use_container_width=True,
        key="paycheck_editor"
    )

    paychecks["Total"] = pd.to_numeric(paychecks["Total"], errors="coerce")
    paychecks["Due Date"] = pd.to_datetime(paychecks["Due Date"], errors="coerce")
    paychecks["Account"] = paychecks["Account"].astype(str)

    return paychecks