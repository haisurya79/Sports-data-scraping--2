import pandas as pd
from playwright.sync_api import sync_playwright
import re
import sys

CALENDAR_URL = "https://www.motogp.com/en/calendar"

def run_motogp_scraper():
    all_data = []

    print("🚀 Launching MotoGP 2026 Deep Scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        print(f"📡 Loading {CALENDAR_URL}...")
        page.goto(CALENDAR_URL, wait_until="networkidle", timeout=60000)
        
        # Wait for the main list items to appear
        page.wait_for_selector('.calendar-listing__event-container', timeout=30000)

        # 1. Capture all race cards (even those without schedules)
        race_cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(race_cards)} scheduled events on the page.")

        for index, card in enumerate(race_cards):
            card_text = card.inner_text()
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]

            # Default Row Structure (Matching your reference image sequence)
            row = {
                "Sr. No": index + 1,
                "City": "NA",
                "Dates": "NA",
                "FP1": "NA",
                "Practice": "NA",
                "FP2": "NA",
                "Q1": "NA",
                "Q2": "NA",
                "Sprint": "NA",
                "Warm Up": "NA",
                "Race": "NA"
            }

            # Basic parsing of City and Dates
            # Usually: Line 0 = Date, Line 1 = Sr No, Line 2 = City
            if len(lines) >= 3:
                row["Dates"] = lines[0]
                row["City"] = lines[2]

            # 2. Extract Session Times if they exist in the card
            # Using Regex to find time patterns (e.g., "09:15") associated with labels
            def extract_time(label, text):
                # Look for a time (XX:XX) followed by or preceded by the label
                # This handles variations in how the site displays the 'Session Times' block
                pattern = rf"([A-Z][a-z]{{2}}\s/\s\d{{2}}:\d{{2}})\s*{re.escape(label)}"
                match = re.search(pattern, text, re.IGNORECASE)
                return match.group(1) if match else "NA"

            # Check if this card contains the "MotoGP session times" section
            if "MotoGP™ session times" in card_text:
                row["FP1"] = extract_time("Free Practice Nr. 1", card_text)
                row["Practice"] = extract_time("Practice", card_text)
                row["FP2"] = extract_time("Free Practice Nr. 2", card_text)
                row["Q1"] = extract_time("Qualifying Nr. 1", card_text)
                row["Q2"] = extract_time("Qualifying Nr. 2", card_text)
                row["Sprint"] = extract_time("Tissot Sprint", card_text)
                row["Warm Up"] = extract_time("Warm Up", card_text)
                row["Race"] = extract_time("Grand Prix", card_text)
            
            all_data.append(row)

        browser.close()

    # Step 3: Final Data Formatting
    if not all_data:
        print("❌ Error: No data found.")
        sys.exit(1)

    df = pd.DataFrame(all_data)

    # Force the exact column sequence from your image
    column_order = [
        "Sr. No", "City", "Dates", 
        "FP1", "Practice", "FP2", 
        "Q1", "Q2", "Sprint", 
        "Warm Up", "Race"
    ]
    df = df[column_order]

    # Save to CSV
    df.to_csv("sports_update.csv", index=False)
    print(f"📊 Success! File 'sports_update.csv' generated with {len(df)} entries.")

if __name__ == "__main__":
    run_motogp_scraper()
        
