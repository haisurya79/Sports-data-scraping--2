import pandas as pd
from playwright.sync_api import sync_playwright
import re
import sys

CALENDAR_URL = "https://www.motogp.com/en/calendar?view=list"

def run_motogp_scraper():
    all_data = []

    print("🚀 Launching MotoGP 2026 Scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        print(f"📡 Loading {CALENDAR_URL}...")
        page.goto(CALENDAR_URL, wait_until="domcontentloaded", timeout=60000)
        
        # We know from your error log that this class exists. 
        # We'll use a more relaxed wait.
        page.wait_for_load_state("networkidle")
        
        # Locate all race cards
        cards_locator = page.locator('.calendar-listing__event-container')
        count = cards_locator.count()
        
        if count == 0:
            print("❌ No cards found. The website structure might have changed.")
            sys.exit(1)
            
        print(f"✅ Found {count} race cards. Extracting data...")

        for i in range(count):
            card = cards_locator.nth(i)
            card_text = card.inner_text()
            
            # Default structure
            row = {
                "Sr. No": i + 1,
                "City": "NA",
                "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # --- Extract City & Dates ---
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            
            # Regex for Dates (e.g., 27 FEB - 01 MAR)
            date_match = re.search(r'\d{2}\s[A-Z]{3}\s-\s\d{2}\s[A-Z]{3}', card_text)
            if date_match:
                row["Dates"] = date_match.group(0)
            
            # The City is usually the line that contains the GP Name or is capitalized
            # We'll look for the line that doesn't look like a date or a number
            for line in lines:
                if "GRAND PRIX" in line.upper():
                    row["City"] = line
                    break

            # --- Extract Session Times ---
            def extract_time(label, text):
                # This pattern looks for "FRI / 09:15" appearing before the Session Name
                pattern = rf"([A-Z]{{3}}\s/\s\d{{2}}:\d{{2}})\s+{re.escape(label)}"
                match = re.search(pattern, text, re.IGNORECASE)
                return match.group(1) if match else "NA"

            if "session times" in card_text.lower():
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

    # Create DataFrame and Reorder Columns to match your Reference Image
    df = pd.DataFrame(all_data)
    column_order = [
        "Sr. No", "City", "Dates", 
        "FP1", "Practice", "FP2", 
        "Q1", "Q2", "Sprint", 
        "Warm Up", "Race"
    ]
    df = df[column_order]

    # Save
    df.to_csv("sports_update.csv", index=False)
    print("📊 Successfully generated sports_update.csv")

if __name__ == "__main__":
    run_motogp_scraper()
