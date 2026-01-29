import pandas as pd
from playwright.sync_api import sync_playwright
import re
import sys
from datetime import datetime, timedelta

CALENDAR_URL = "https://www.motogp.com/en/calendar?view=list"

def run_motogp_scraper():
    all_data = []

    print("🚀 Launching Precision Scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print(f"📡 Loading {CALENDAR_URL}...")
        page.goto(CALENDAR_URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(5000) # Safety wait for JS rendering

        cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(cards)} race cards.")

        for i, card in enumerate(cards):
            # 1. Direct Class Extraction for City/Dates
            try:
                city = card.locator('.calendar-listing__title').inner_text().strip()
                date_range = card.locator('.calendar-listing__date').inner_text().strip()
            except:
                city = "NA"
                date_range = "NA"

            row = {
                "Sr. No": i + 1,
                "City": city,
                "Dates": date_range,
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # 2. Extract Session Times with Exact Dates
            # Example date_range: "27 FEB - 01 MAR"
            start_date_str = date_range.split('-')[0].strip() + " 2026" # "27 FEB 2026"
            try:
                friday_date = datetime.strptime(start_date_str, "%d %b %Y")
            except:
                friday_date = None

            card_text = card.inner_text()
            
            def get_full_session_info(label, text, friday):
                # Regex for "FRI / 09:15"
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(label)}"
                match = re.search(pattern, text, re.IGNORECASE)
                if match and friday:
                    day_name = match.group(1).upper() # "FRI"
                    time_val = match.group(2) # "09:15"
                    
                    # Map offset based on day
                    offset = {"THU": -1, "FRI": 0, "SAT": 1, "SUN": 2}
                    session_date = friday + timedelta(days=offset.get(day_name, 0))
                    
                    # Result: "27 FEB FRI / 09:15"
                    return f"{session_date.strftime('%d %b')} {day_name} / {time_val}"
                return "NA"

            if "session times" in card_text.lower():
                row["FP1"] = get_full_session_info("Free Practice Nr. 1", card_text, friday_date)
                row["Practice"] = get_full_session_info("Practice", card_text, friday_date)
                row["FP2"] = get_full_session_info("Free Practice Nr. 2", card_text, friday_date)
                row["Q1"] = get_full_session_info("Qualifying Nr. 1", card_text, friday_date)
                row["Q2"] = get_full_session_info("Qualifying Nr. 2", card_text, friday_date)
                row["Sprint"] = get_full_session_info("Tissot Sprint", card_text, friday_date)
                row["Warm Up"] = get_full_session_info("Warm Up", card_text, friday_date)
                row["Race"] = get_full_session_info("Grand Prix", card_text, friday_date)

            all_data.append(row)

        browser.close()

    # Step 3: Export with Sequence
    df = pd.DataFrame(all_data)
    cols = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[cols].to_csv("sports_update.csv", index=False)
    print("📊 Done! Check 'sports_update.csv' for the dated schedule.")

if __name__ == "__main__":
    run_motogp_scraper()
