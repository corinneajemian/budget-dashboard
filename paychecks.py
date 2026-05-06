import pandas as pd

def get_paychecks():
    data = [
        {
            "Provider": "Chase",
            "Type": "Checking",
            "Account": "1234",
            "Transaction": "Company Paycheck",
            "Total": 1000,
            "Owner": "Me",
            "Due Date": "7-May",
        },
        # Add more enteries of your incoming paychecks...
        #{
        #    "Provider": "Add Banking Company",
        #    "Type": "Checking or Savings",
        #    "Account": "Last 4 digits",
        #    "Transaction": "Company of Paycheck",
        #    "Total": 1000,
        #    "Owner": "Your Name",
        #    "Due Date": "Date Received",
        #},

        
    ]

    df = pd.DataFrame(data)

    # Clean it here once so you never worry again
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce")
    df["Due Date"] = pd.to_datetime(df["Due Date"] + "-2026", format="%d-%b-%Y", errors="coerce")
    df["Account"] = df["Account"].astype(str)

    return df