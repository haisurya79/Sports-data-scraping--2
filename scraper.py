import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

# Official URL
URL = "https://www.motogp.com/en/calendar"

def run_scraper():
    results = []
    print("🚀 Launching Chronological Recovery Scraper...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Load and wait for the calendar container
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector('.calendar-listing__event-container', timeout=30000)

        # 1. Grab all event containers
        # These are the 22 cards from Thailand to Valencia
        containers = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(containers)} events. Matching Round by Round...")

        for i, card in enumerate(containers):
            # Capture the raw text and clean out the "Up Next" or "Finished" labels
            raw_text = card.inner_text()
            clean_text = raw_text.replace("up next", "").replace("today", "").strip()
            lines = [l.strip() for l in clean_text.split('\n') if l.strip()]

            # Default Row Structure (Exactly matching your image)
            row = {
                "Sr. No": i + 1, "City": "NA", "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # 2. Extract City & Date Range using strict indices
            # In the 2026 site:
            # line[0] is usually the date (e.g., 27 Feb - 01 Mar)
            # line[1] is the Round Number (e.g., 1)
            # line[2] is the City (e.g., THAILAND)
            if len(lines) >= 3:
                row["Dates"] = lines[0]
                row["City"] = lines[2]
            
            # 3. Session Date Logic
            # We calculate the calendar date for each session based on the weekend
            try:
                # Get the Sunday date as an anchor (e.g., "01 Mar")
                end_str = row["Dates"].split('-')[-1].strip()
                anchor_dt = datetime.strptime(f"{end_str} 2026", "%d %b %Y")
            except:
                anchor_dt = None

            def format_session_time(keyword, blob, anchor):
                # Look for "FRI / 09:15" followed by the session name
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(keyword)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and anchor:
                    day_code, time_val = match.group(1).upper(), match.group(2)
                    offsets = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}
                    session_date = anchor + timedelta(days=offsets.get(day_code, 0))
                    # Format: 01 Mar SUN / 13:30
                    return f"{session_date.strftime('%d %b')} {day_code} / {time_val}"
                return "NA"

            # 4. Fill Columns
            if "session times" in clean_text.lower():
                row["FP1"] = format_session_time("Free Practice Nr. 1", clean_text, anchor_dt)
                row["Practice"] = format_session_time("Practice", clean_text, anchor_dt)
                row["FP2"] = format_session_time("Free Practice Nr. 2", clean_text, anchor_dt)
                row["Q1"] = format_session_time("Qualifying Nr. 1", clean_text, anchor_dt)
                row["Q2"] = format_session_time("Qualifying Nr. 2", clean_text, anchor_dt)
                row["Sprint"] = format_session_time("Tissot Sprint", clean_text, anchor_dt)
                row["Warm Up"] = format_session_time("Warm Up", clean_text, anchor_dt)
                row["Race"] = format_session_time("Grand Prix", clean_text, anchor_dt)

            results.append(row)

        browser.close()

    # Step 5: Final DataFrame Creation
    df = pd.DataFrame(results)
    
    # Ensure correct column order from your reference image
    cols = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[cols].to_csv("sports_update.csv", index=False)
    
    print(f"✨ Success! Thailand is Round 1. Brazil is Round 2. Total Rounds: {len(df)}")

if __name__ == "__main__":
    run_scraper()
