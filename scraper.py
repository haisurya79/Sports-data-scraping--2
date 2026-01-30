import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Initializing Chronological Scraper (2026 Edition)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Load and wait for the Thailand GP container
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector('.calendar-listing__event-container', timeout=30000)

        # Scroll slowly to force all 22 rounds to render their text
        for _ in range(8):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        # Grab all containers (Round 1 to 22)
        cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(cards)} rounds. Starting deep extraction...")

        for i, card in enumerate(cards):
            # 1. Get ALL text inside the card to avoid selector misses
            raw_text = card.inner_text()
            # Clean out the "up next" and "today" noise
            clean_text = re.sub(r'(up next|today|march|february)', '', raw_text, flags=re.IGNORECASE).strip()
            lines = [l.strip() for l in clean_text.split('\n') if l.strip()]

            row = {
                "Sr. No": i + 1, "City": "NA", "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # 2. Extract City & Dates (Chronology Check: Round 1 must be Thailand)
            # Date pattern: 27 Feb - 01 Mar
            date_match = re.search(r'(\d{1,2}\s[A-Z]{3}\s-\s\d{1,2}\s[A-Z]{3})', clean_text)
            if date_match:
                row["Dates"] = date_match.group(1)
            
            # City logic: The first all-caps word after the round number
            for line in lines:
                if line.isupper() and len(line) > 3 and "GRAND PRIX" not in line:
                    row["City"] = line
                    break

            # 3. Session Time Calculation (Mapped to Calendar)
            try:
                end_str = row["Dates"].split('-')[-1].strip()
                anchor_dt = datetime.strptime(f"{end_str} 2026", "%d %b %Y")
            except:
                anchor_dt = None

            def get_time(label, blob, anchor):
                # Pattern: Looks for "FRI / 09:15 Free Practice Nr. 1"
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(label)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and anchor:
                    day, time_val = match.group(1).upper(), match.group(2)
                    offset = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}.get(day, 0)
                    session_dt = anchor + timedelta(days=offset)
                    return f"{session_dt.strftime('%d %b')} {day} / {time_val}"
                return "NA"

            # 4. Populate Session Columns
            if "session times" in raw_text.lower():
                row["FP1"] = get_time("Free Practice Nr. 1", raw_text, anchor_dt)
                row["Practice"] = get_time("Practice", raw_text, anchor_dt)
                row["FP2"] = get_time("Free Practice Nr. 2", raw_text, anchor_dt)
                row["Q1"] = get_time("Qualifying Nr. 1", raw_text, anchor_dt)
                row["Q2"] = get_time("Qualifying Nr. 2", raw_text, anchor_dt)
                row["Sprint"] = get_time("Tissot Sprint", raw_text, anchor_dt)
                row["
        
