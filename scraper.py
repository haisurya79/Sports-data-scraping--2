import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Launching Fail-Safe Scraper...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 1. Load and wait for the cards to exist
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_selector('.calendar-listing__event-container', timeout=30000)
        
        # Force a scroll to trigger all lazy-loaded text
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        # 2. Grab all cards
        cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(cards)} events. Extracting...")

        for i, card in enumerate(cards):
            # Capture the raw text of the whole card immediately
            full_card_text = card.inner_text()
            lines = [line.strip() for line in full_card_text.split('\n') if line.strip()]

            # --- PART A: RELIABLE CITY & DATE EXTRACTION ---
            # We look for specific patterns in the lines
            city = "NA"
            date_range = "NA"
            
            for line in lines:
                # Date Pattern: "27 FEB - 01 MAR"
                if re.search(r'\d{1,2}\s[A-Z]{3}\s-\s\d{1,2}\s[A-Z]{3}', line):
                    date_range = line
                # City Pattern: Usually the first line that is all UPPERCASE and not a date
                elif line.isupper() and len(line) > 3 and "GRAND PRIX" not in line and city == "NA":
                    city = line

            # --- PART B: DATE CALCULATOR ---
            try:
                # Get the ending date (e.g., "01 MAR") to use as the Sunday anchor
                end_date_str = date_range.split('-')[-1].strip()
                anchor_date = datetime.strptime(f"{end_date_str} 2026", "%d %b %Y")
            except:
                anchor_date = None

            row = {
                "Sr. No": i + 1,
                "City": city,
                "Dates": date_range,
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # --- PART C: SESSION TIMES ---
            def get_dated_time(label, blob, dt):
                # Pattern: "FRI / 09:00 Free Practice Nr. 1"
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(label)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and dt:
                    day_code = match.group(1).upper() # "FRI"
                    time_val = match.group(2)        # "09:00"
                    
                    # Offset logic relative to Sunday (0)
                    offsets = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}
                    session_date = dt + timedelta(days=offsets.get(day_code, 0))
                    
                    # Return formatted: "01 Mar SUN / 09:00"
                    return f"{session_date.strftime('%d %b')} {day_code} / {time_val}"
                return "NA"

            if "session times" in full_card_text.lower():
                row["FP1"] = get_dated_time("Free Practice Nr. 1", full_card_text, anchor_date)
                row["Practice"] = get_dated_time("Practice", full_card_text, anchor_date)
                row["FP2"] = get_dated_time("Free Practice Nr. 2", full_card_text, anchor_date)
                row["Q1"] = get_dated_time("Qualifying Nr. 1", full_card_text, anchor_date)
                row["Q2"] = get_dated_time("Qualifying Nr. 2", full_card_text, anchor_date)
                row["Sprint"] = get_dated_time("Tissot Sprint", full_card_text, anchor_date)
                row["Warm Up"] = get_dated_time("Warm Up", full_card_text, anchor_date)
                row["Race"] = get_dated_time("Grand Prix", full_card_text, anchor_date)

            results.append(row)

        browser.close()

    # Step 3: Save results
    df = pd.DataFrame(results)
    cols = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[cols].to_csv("sports_update.csv", index=False)
    print(f"📊 Done! Extracted {len(results)} events to sports_update.csv")

if __name__ == "__main__":
    run_scraper()
