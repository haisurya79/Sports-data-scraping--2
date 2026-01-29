import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

# Official 2026 Calendar
URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    print("🚀 Starting Deep-Data Extraction...")

    with sync_playwright() as p:
        # Launching with a real-user fingerprint to avoid being blocked
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        # Scroll down to force all images/data to load
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(5000)

        # Target the event cards
        cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(cards)} events. Processing details...")

        for i, card in enumerate(cards):
            # 1. Extract the Header Data
            # We use multiple fallbacks for the City Name
            raw_text = card.inner_text()
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            
            city = "NA"
            date_range = "NA"
            
            # Pattern matching for City (usually the first uppercase word after the number)
            for line in lines:
                if any(month in line.upper() for month in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]):
                    date_range = line # e.g. "27 FEB - 01 MAR"
                elif line.isupper() and len(line) > 3 and "GRAND PRIX" not in line:
                    city = line # e.g. "THAILAND"

            # 2. Setup the Date Calculator
            # If date_range is "27 FEB - 01 MAR", start_day is 27 Feb
            try:
                start_part = date_range.split('-')[0].strip()
                base_date = datetime.strptime(f"{start_part} 2026", "%d %b %Y")
            except:
                base_date = None

            row = {
                "Sr. No": i + 1, "City": city, "Dates": date_range,
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # 3. Helper to find time and add the correct date
            def extract_session(keyword, full_text, start_dt):
                # Look for "FRI / 09:00" near the session name
                match = re.search(r'([A-Z]{3})\s/\s(\d{2}:\d{2})\s+' + re.escape(keyword), full_text, re.IGNORECASE)
                if match and start_dt:
                    day_name = match.group(1).upper()
                    time_val = match.group(2)
                    
                    # Calculate actual calendar date
                    days_plus = {"FRI": 0, "SAT": 1, "SUN": 2}.get(day_name, 0)
                    actual_date = start_dt + timedelta(days=days_plus)
                    
                    # Return formatted: "01 Mar SUN / 13:30"
                    return f"{actual_date.strftime('%d %b')} {day_name} / {time_val}"
                return "NA"

            # 4. Map the columns precisely
            if "session times" in raw_text.lower():
                row["FP1"] = extract_session("Free Practice Nr. 1", raw_text, base_date)
                row["Practice"] = extract_session("Practice", raw_text, base_date)
                row["FP2"] = extract_session("Free Practice Nr. 2", raw_text, base_date)
                row["Q1"] = extract_session("Qualifying Nr. 1", raw_text, base_date)
                row["Q2"] = extract_session("Qualifying Nr. 2", raw_text, base_date)
                row["Sprint"] = extract_session("Tissot Sprint", raw_text, base_date)
                row["Warm Up"] = extract_session("Warm Up", raw_text, base_date)
                row["Race"] = extract_session("Grand Prix", raw_text, base_date)

            results.append(row)
        
        browser.close()

    # Create CSV
    df = pd.DataFrame(results)
    column_order = ["Sr. No", "City", "Dates", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    df[column_order].to_csv("sports_update.csv", index=False)
    print("✨ Process Complete. File 'sports_update.csv' is ready.")

if __name__ == "__main__":
    run_scraper()
