import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Running Final Precision Scraper. Chronology Locked...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 2000})
        page = context.new_page()

        # 1. Load and wait for the framework to be fully ready
        page.goto(URL, wait_until="networkidle", timeout=90000)
        
        # 2. Force the data to load by scrolling 
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(5000)

        # 3. Targeted extraction: Use strict indices for Round 1 to 22
        cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(cards)} events. Processing Round by Round...")

        for i, card in enumerate(cards):
            # Extract basic text and clean it
            card_text = card.inner_text()
            lines = [l.strip() for l in card_text.split('\n') if l.strip()]

            # Default Row (NA by default)
            row = {
                "Sr. No": i + 1, "City": "NA", "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # --- PART A: RELIABLE CITY & DATE (Based on 2026 Layout) ---
            # Search for the Date Range first (e.g. 27 FEB - 01 MAR)
            date_match = re.search(r'(\d{1,2}\s[A-Z]{3}\s-\s\d{1,2}\s[A-Z]{3})', card_text)
            if date_match:
                row["Dates"] = date_match.group(1)
            
            # City is always the first uppercase block after the Round Number
            for line in lines:
                if line.isupper() and "GRAND PRIX" not in line and not re.search(r'\d{2}\s[A-Z]{3}', line):
                    row["City"] = line
                    break

            # --- PART B: SESSION DATE CALCULATION ---
            try:
                # We anchor to the Sunday (e.g., 01 MAR)
                end_str = row["Dates"].split('-')[-1].strip()
                anchor_dt = datetime.strptime(f"{end_str} 2026", "%d %b %Y")
            except:
                anchor_dt = None

            def get_session_info(label, blob, anchor):
                # Pattern: Day / Time followed by Session Name
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(label)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and anchor:
                    day_code, time_val = match.group(1).upper(), match.group(2)
                    offset = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}.get(day_code, 0)
                    session_date = anchor + timedelta(days=offset)
                    return f"{session_date.strftime('%d %b')} {day_code} / {time_val}"
                return "NA"

            # --- PART C: FILL SESSIONS ---
            if "session times" in card_text.lower():
                row["FP1"] = get_session_info("Free Practice Nr. 1", card_text, anchor_dt)
                row["Practice"] = get_session_info("Practice", card_text, anchor_dt)
                row["FP2"] = get_session_info("Free Practice Nr. 2", card_text, anchor_dt)
                row["Q1"] = get_session_info("Qualifying Nr. 1", card_text, anchor_dt)
                row["Q2"] = get_session_info("Qualifying Nr. 2", card_text, anchor_dt)
                row["Sprint"] = get_session_info("Tissot Sprint", card_text, anchor_dt)
                row["Warm Up"] = get_session_info("Warm Up", card_text, anchor_dt)
                row["Race"] = get_session_info("Grand Prix", card_text, anchor_dt)

            results.append(row)

        browser.close()

    # Step 4: Final Format (Chronology Locked)
    df = pd.DataFrame(results)
    cols = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[cols].to_csv("sports_update.csv", index=False)
    print("✨ Process Complete. sports_update.csv is ready.")

if __name__ == "__main__":
    run_scraper()
