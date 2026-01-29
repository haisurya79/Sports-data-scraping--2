import pandas as pd
import requests
from io import StringIO
import sys

# Stronger Browser Identity (User-Agent) to prevent Wikipedia blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Source 1: The Master Calendar for ALL sports in 2026
# Source 2: The T20 World Cup specific page
SOURCES = [
    {"name": "Global Calendar", "url": "https://www.motogp.com/en/calendar?view=list"},
    {"name": "T20 World Cup", "url": "https://www.motogp.com/en/calendar?view=list"}
]

def run_manual_update():
    combined_results = []

    for source in SOURCES:
        try:
            print(f"Accessing {source['name']}...")
            response = requests.get(source['url'], headers=HEADERS, timeout=20)
            response.raise_for_status()

            # FIX: Using StringIO solves the 'FutureWarning' and ensures tables are read
            html_content = StringIO(response.text)
            tables = pd.read_html(html_content)

            if not tables:
                print(f"Warning: No tables found at {source['url']}")
                continue

            # Logic to find the most relevant table
            # For '2026 in sports', the tables usually start from index 1 or 2
            for i, df in enumerate(tables):
                # We look for tables that have 'Sport' or 'Event' in the headers
                if any(col in str(df.columns) for col in ['Sport', 'Event', 'Team', 'Venue']):
                    df['Source_Origin'] = source['name']
                    combined_results.append(df)
                    break # Grab the main one and move to next source

        except Exception as e:
            print(f"Failed to fetch {source['name']}: {e}")

    if not combined_results:
        print("CRITICAL ERROR: No data could be scraped from any source.")
        sys.exit(1)

    # Combine all found data into one Master Schedule
    final_df = pd.concat(combined_results, ignore_index=True)
    
    # Save to your CSV
    final_df.to_csv("sports_update.csv", index=False)
    print(f"Successfully updated 'sports_update.csv' with {len(final_df)} entries.")

if __name__ == "__main__":
    run_manual_update()
            
