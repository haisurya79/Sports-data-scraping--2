import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Launching Chronological Scraper (Human-Mimic Mode)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 1. Load the page and wait for the framework
        page.goto(URL, wait_until="networkidle", timeout=90000)
        
        # 2. THE HUMAN SCROLL: 
        # MotoGP lazy-loads race cards. We scroll 1000px at a time to "wake up" the data.
        for _ in range(10):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1000)

        # 3. Targeted Extraction
        # We find every container and extract text purely by position to keep chronology
        containers = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(containers)} events. Processing in order...")

        for i, card in enumerate(containers):
            # Extract card text
            text = card.inner_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            # Default Row
            row = {
                "Sr. No": i + 1, "City": "NA", "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # CITY & DATE: Based on 2026 site structure
            # Thailand (Round 1) should be: lines[0]=Dates, lines[2]=City
            if len(lines) >= 3:
                # Look for date pattern: 27 FEB - 01 MAR
                date_match = re.search(r'\d{1,2}\s[A-Z]{3}\s-\s\d{1,2}\s[A-Z]{3}', text)
                row["Dates"] = date_match.group(0) if date_match else lines[0]
                
                # City is usually the large uppercase line
                for line in lines:
                    if line.isupper() and "GRAND PRIX" not in line and len(line) > 3:
                        row["City"] = line
                        break

            # SESSION TIMES: We extract "FRI / 09:15" and attach the correct Date
            try:
                # Use the end date (Sunday) as our anchor
                end_str = row["Dates"].split('-')[-1].strip()
                anchor_dt = datetime.strptime(f"{end_str} 2026", "%d %b %Y")
            except:
                anchor_dt = None

            def parse_time(keyword, blob, anchor):
                # Pattern: Day / Time followed by Session Name
                pattern = rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(keyword)}"
                match = re.search(pattern, blob, re.IGNORECASE)
                if match and anchor:
                    day_code = match.group(1).upper()
                    time_val = match.group(2)
                    # Offset based on Sunday (0)
                    offsets = {"THU": -3, "FRI": -2, "SAT": -1, "SUN": 0}
                    session_dt = anchor + timedelta(days=offsets.get(day_code, 0))
                    return f"{session_dt.strftime('%d %b')} {day_code} / {time_val}"
                return "NA"

            if "session times" in text.lower():
                row["FP1"] = parse_time("Free Practice Nr. 1", text, anchor_dt)
                row["Practice"] = parse_time("Practice", text, anchor_dt)
                row["FP2"] = parse_time("Free Practice Nr. 2", text, anchor_dt)
                row["Q1"] = parse_time("Qualifying Nr. 1", text, anchor_dt)
                row["Q2"] = parse_time("Qualifying Nr. 2", text, anchor_dt)
                row["Sprint"] = parse_time("Tissot Sprint", text, anchor_dt)
                row["Warm Up"] = parse_time("Warm Up", text, anchor_dt)
                row["Race"] = parse_time("Grand Prix", text, anchor_dt)

            results.append(row)

        browser.close()

    # Step 4: Export with strictly ordered columns
    df = pd.DataFrame(results)
    df = df[["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]]
    
    # Validation: Ensure Thailand is first
    if not df.empty and "THAILAND" not in df.iloc[0]['City'].upper():
        print("⚠️ Warning: Chronology might be off. Sorting by Sr. No...")
        df = df.sort_values(by="Sr. No")

    df.to_csv("sports_update.csv", index=False)
    print("✨ Successfully generated 'sports_update.csv' with chronological data.")

if __name__ == "__main__":
    run_scraper()
