import pandas as pd


def get_sp500_info():
    try:
        # Read the Wikipedia table, This is a table, fetch the required columns and save it in CSV.
        sp500_info = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]
        sp500_info = sp500_info[
            ["Symbol", "Security", "GICS Sector", "GICS Sub-Industry", "CIK"]
        ]
        sp500_info["Symbol"] = sp500_info["Symbol"].str.replace(".", "-")
        return sp500_info
    except Exception as e:
        print(f"Error getting S&P 500 information: {e}")
        return None


# Get and save S&P 500 information
def save_sp500_info(output_file):
    sp500_info = get_sp500_info()
    if sp500_info is not None:
        print(f"Retrieved information for {len(sp500_info)} companies")
        sp500_info.to_csv(output_file)
        print(f"Data saved to {output_file}")
        return sp500_info

    return None


sp500_info = save_sp500_info("sp500_security_master.csv")
