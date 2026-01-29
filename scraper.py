import pandas as pd
from playwright.sync_api import sync_playwright
import re
import sys
import time

CALENDAR_URL = "https://www.motogp.com/en/calendar?view=list"

def run_motogp_scraper():
    all_data = []

    print("🚀 Launching Anti-NA Scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print(f"📡 Loading {CALENDAR_URL}...")
        page.goto(CALENDAR_URL, wait_until="networkidle", timeout=90000)
        
        # Give the JS extra time to "paint" the text on the screen
        time.sleep(10)

        # Grab all race containers
        cards = page.locator('.calendar-listing__event-container').all()
        
        if not cards:
            print("❌ Error: No race cards found on page.")
            sys.exit(1)

        print(f"✅ Found {len(cards)} race cards. Analyzing...")

        for i, card in enumerate(cards):
            # This captures EVERYTHING inside the card, including hidden text
            raw_text_list = card.locator('span, div, p').all_inner_texts()
            full_text = " ".join(raw_text_list)
            
            # 1. Start with NAs
            row = {
                "Sr. No": i + 1,
                "City": "NA", "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # 2. Extract City & Dates (using patterns found in 2026 site)
            # Date pattern: e.g., 27 Feb - 01 Mar
            date_match = re.search(r'(\d{1,2}\s[A-Za-z]{3}\s-\s\d{1,2}\s[A-Za-z]{3})', full_text)
            if date_match:
                row["Dates"] = date_match.group(1)
            
            # City is usually the first uppercase block or after the number
            # We'll pull the city/country from specific classes if possible
            try:
                city_el = card.locator('.calendar-listing__title')
                if city_el.count() > 0:
                    row["City"] = city_el.first.inner_text().strip()
            except:
                pass

            # 3. Session Time Logic
            # We look for the exact labels from your image
            def find_time(label):
                # Pattern: Find "FRI / 09:15" appearing near the label
                # We search in a window around the label index
                match = re.search(r'([A-Z]{3}\s/\s\d{2}:\d{2})\s+' + re.escape(label), full_text, re.IGNORECASE)
                if match:
                    return match.group(1)
                return "NA"

            if "session times" in full_text.lower():
                row["FP1"] = find_time("Free Practice Nr. 1")
                row["Practice"] = find_time("Practice")
                row["FP2"] = find_time("Free Practice Nr. 2")
                row["Q1"] = find_time("Qualifying Nr. 1")
                row["Q2"] = find_time("Qualifying Nr. 2")
                row["Sprint"] = find_time("Tissot Sprint")
                row["Warm Up"] = find_time("Warm Up")
                row["Race"] = find_time("Grand Prix")

            all_data.append(row)

        browser.close()

    # Step 4: Final Format
    df = pd.DataFrame(all_data)
    column_order = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df = df[column_order]
    
    df.to_csv("sports_update.csv", index=False)
    print(f"📊 Success! Exported to sports_update.csv")

if __name__ == "__main__":
    run_motogp_scraper()
