import pandas as pd
import requests

# Use a User-Agent so the website thinks a real person is visiting
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# The source URL
URL = "https://www.motogp.com/en/calendar?view=list"

def run_manual_update():
    try:
        # 1. Get the page content safely
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status() # Check if the site is down or blocking us

        # 2. Extract all tables
        tables = pd.read_html(response.text)
        print(f"Found {len(tables)} tables on the page.")

        if len(tables) == 0:
            print("No tables found! Check the URL.")
            return

        # 3. Look for the "Qualified Teams" table automatically
        # Instead of using [3], we search for a table that contains 'Method of qualification'
        target_table = None
        for t in tables:
            if 'Method of qualification' in str(t.columns) or 'Team' in str(t.columns):
                target_table = t
                break
        
        if target_table is None:
            target_table = tables[0] # Fallback to first table if search fails

        # 4. Format the data
        df = target_table.copy()
        df['Tournament Name'] = "T20 World Cup 2026"
        
        # Save it
        df.to_csv("sports_update.csv", index=False)
        print("Success: sports_update.csv has been refreshed.")

    except Exception as e:
        print(f"FAILED: {e}")
        exit(1) # This tells GitHub Action that it actually failed

if __name__ == "__main__":
    run_manual_update()
