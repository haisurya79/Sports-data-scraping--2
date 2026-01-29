import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Running Precision Scraper...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a standard context to ensure text renders properly
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        # Gentle scroll to ensure dynamic session tables load
        page.evaluate("window.scrollBy(0, 5000)")
        page.wait_for_timeout(3000)

        # 1. Target every race card
        cards = page.locator('.calendar-listing__event-container').all()
        
        for i, card in enumerate(cards):
            # Extract basic text
            card_text = card.inner_text()
            
            # 2. Re-implementing the successful City/Date logic
            # These selectors are specific to the elements that worked for you originally
            try:
                city = card.locator('.calendar-listing__title').inner_text().strip()
                date_range = card.locator('.calendar-listing__date').inner_text().strip()
            except:
                # Fallback to parsing text if selectors fail
                city = "NA"
                date_range = "NA"

            # 3. Date Math for Session Formatting
            # We take the "01 Mar" part of the range to anchor the Sunday race
            try:
                # Example: "27 FEB - 01 MAR" -> end_date is "01 MAR 2026"
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

            # 4. Extract Sessions and append formatted date
            # Pattern looks for "SUN / 13:30 Grand Prix"
            def format_session(keyword, blob, dt):
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(keyword)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and dt:
                    day = match.group(1).upper()
                    time_val = match.group(2)
                    # Adjust date based on Day Name relative to the Sunday anchor
                    offsets = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}
                    session_dt = dt + timedelta(days=offsets.get(day, 0))
                    return f"{session_dt.strftime('%d %b')} {day} / {time_val}"
                return "NA"

            if "session times" in card_text.lower():
                row["FP1"] = format_session("Free Practice Nr. 1", card_text, anchor_date)
                row["Practice"] = format_session("Practice", card_text, anchor_date)
                row["FP2"] = format_session("Free Practice Nr. 2", card_text, anchor_date)
                row["Q1"] = format_session("Qualifying Nr. 1", card_text, anchor_date)
                row["Q2"] = format_session("Qualifying Nr. 2", card_text, anchor_date)
                row["Sprint"] = format_session("Tissot Sprint", card_text, anchor_date)
                row["Warm Up"] = format_session("Warm Up", card_text, anchor_date)
                row["Race"] = format_session("Grand Prix", card_text, anchor_date)

            results.append(row)

        browser.close()

    # Final Output
    df = pd.DataFrame(results)
    # Ensure columns match your request exactly
    cols = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[cols].to_csv("sports_update.csv", index=False)
    print("📊 File updated: sports_update.csv")

if __name__ == "__main__":
    run_scraper()
