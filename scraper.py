import pandas as pd
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

URL = "https://www.motogp.com/en/calendar?view=list"

def run_scraper():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 3000})
        page.goto(URL, wait_until="networkidle")
        
        # Human-mimic scroll to load all 22 rounds
        for _ in range(10):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1000)

        cards = page.locator('.calendar-listing__event-container').all()
        for i, card in enumerate(cards):
            text = card.inner_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            row = {"Sr. No": i + 1, "City": "NA", "Dates": "NA", "FP1": "NA", "Practice": "NA", 
                   "FP2": "NA", "Q1": "NA", "Q2": "NA", "Sprint": "NA", "Warm Up": "NA", "Race": "NA"}

            # Extract City/Dates
            date_match = re.search(r'(\d{1,2}\s[A-Z]{3}\s-\s\d{1,2}\s[A-Z]{3})', text)
            row["Dates"] = date_match.group(1) if date_match else "NA"
            for line in lines:
                if line.isupper() and "GRAND PRIX" not in line and len(line) > 3:
                    row["City"] = line
                    break
            
            # Map Sunday date for calculation
            try:
                anchor = datetime.strptime(f"{row['Dates'].split('-')[-1].strip()} 2026", "%d %b %Y")
            except: anchor = None

            def get_time(label, blob, dt):
                match = re.search(rf"([A-Z]{{3}})\s/\s(\d{{2}}:\d{{2}})\s+{re.escape(label)}", blob)
                if match and dt:
                    day, time = match.group(1).upper(), match.group(2)
                    offset = {"THU":-3, "FRI":-2, "SAT":-1, "SUN":0}.get(day, 0)
                    return f"{(dt + timedelta(days=offset)).strftime('%d %b')} {day} / {time}"
                return "NA"

            if "session times" in text.lower():
                labels = ["Free Practice Nr. 1", "Practice", "Free Practice Nr. 2", "Qualifying Nr. 1", 
                          "Qualifying Nr. 2", "Tissot Sprint", "Warm Up", "Grand Prix"]
                keys = ["FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
                for k, l in zip(keys, labels): row[k] = get_time(l, text, anchor)

            results.append(row)
        browser.close()

    df = pd.DataFrame(results)
    df.to_csv("motogp_2026_schedule.csv", index=False)

if __name__ == "__main__":
    run_scraper()
