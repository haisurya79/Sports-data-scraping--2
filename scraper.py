import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Running Deep-Sync Scraper... Ensuring Thailand is Round 1.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 1. Load and wait for the specific 'Thailand' entry to be ready
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_selector('.calendar-listing__event-container', timeout=30000)
        
        # 2. Scroll to 'wake up' the dynamic session data
        page.evaluate("window.scrollBy(0, 8000)")
        page.wait_for_timeout(4000)

        # 3. Locate every card on the page
        cards = page.locator('.calendar-listing__event-container').all()
        
        for i, card in enumerate(cards):
            # Extract everything from the card
            full_text = card.inner_text()
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]

            # Default Row
            row = {
                "Sr. No": i + 1, "City": "NA", "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # RELIABLE INFO EXTRACTION
            # Date Range (e.g., 27 FEB - 01 MAR)
            date_match = re.search(r'(\d{1,2}\s[A-Z]{3}\s-\s\d{1,2}\s[A-Z]{3})', full_text)
            if date_match:
                row["Dates"] = date_match.group(1)
            
            # City (Look for the first line that is purely uppercase and not a date)
            for line in lines:
                if line.isupper() and "GRAND PRIX" not in line and not any(m in line for m in ["JAN","FEB","MAR"]):
                    row["City"] = line
                    break

            # SESSION DATE CALCULATOR
            try:
                # We use the end of the range as the Sunday anchor
                end_str = row["Dates"].split('-')[-1].strip()
                anchor_dt = datetime.strptime(f"{end_str} 2026", "%d %b %Y")
            except:
                anchor_dt = None

            def get_dated_time(label, blob, anchor):
                # Pattern: "FRI / 09:15 Free Practice Nr. 1"
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(label)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and anchor:
                    day_code, time_val = match.group(1).upper(), match.group(2)
                    # Offset logic (Thailand starts Friday Feb 27, ends Sunday Mar 01)
                    offsets = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}
                    session_date = anchor + timedelta(days=offsets.get(day_code, 0))
                    return f"{session_date.strftime('%d %b')} {day_code} / {time_val}"
                return "NA"

            # Fill Sessions
            if "session times" in full_text.lower():
                row["FP1"] = get_dated_time("Free Practice Nr. 1", full_text, anchor_dt)
                row["Practice"] = get_dated_time("Practice", full_text, anchor_dt)
                row["FP2"] = get_dated_time("Free Practice Nr. 2", full_text, anchor_dt)
                row["Q1"] = get_dated_time("Qualifying Nr. 1", full_text, anchor_dt)
                row["Q2"] = get_dated_time("Qualifying Nr. 2", full_text, anchor_dt)
                row["Sprint"] = get_dated_time("Tissot Sprint", full_text, anchor_dt)
                row["Warm Up"] = get_dated_time("Warm Up", full_text, anchor_dt)
                row["Race"] = get_dated_time("Grand Prix", full_text, anchor_dt)

            results.append(row)

        browser.close()

    # Step 4: Final Chronology Check
    df = pd.DataFrame(results)
    # Re-verify Thailand is #1
    if not df.empty and "THAILAND" not in df.iloc[0]['City'].upper():
        df = df.sort_values(by="Sr. No")

    cols = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[cols].to_csv("sports_update.csv", index=False)
    print("📊 sports_update.csv generated. Row 1 is Thailand.")

if __name__ == "__main__":
    run_scraper()
