import pandas as pd
from playwright.sync_api import sync_playwright
import re
import sys

CALENDAR_URL = "https://www.motogp.com/en/calendar?view=list"

def run_direct_list_scrape():
    all_races = []

    print("🚀 Launching Direct List Scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set a realistic user agent
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        print(f"📡 Navigating to {CALENDAR_URL}...")
        page.goto(CALENDAR_URL, wait_until="networkidle")
        
        # Wait for the main calendar container to load
        page.wait_for_selector('.calendar-listing__event-container', timeout=30000)

        # Grab all race cards on the page
        race_cards = page.locator('.calendar-listing__event-container').all()
        print(f"✅ Found {len(race_cards)} race cards.")

        for index, card in enumerate(race_cards):
            # Extract raw text from the entire card
            card_text = card.inner_text()
            
            # Initialize with NA
            race_entry = {
                "Round": index + 1,
                "Event Name": "NA",
                "Location": "NA",
                "Dates": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA",
                "Q1": "NA", "Q2": "NA", "Sprint": "NA",
                "Warm Up": "NA", "Race": "NA"
            }

            # Basic Info Extraction using text patterns
            lines = [l.strip() for l in card_text.split('\n') if l.strip()]
            
            # Find Event Name (usually has numbers or is the first big title)
            # Find Date (Pattern: 27 FEB - 01 MAR)
            date_match = re.search(r'\d{2}\s[A-Z]{3}\s-\s\d{2}\s[A-Z]{3}', card_text)
            if date_match:
                race_entry["Dates"] = date_match.group(0)

            # Look for specific session keywords and grab the time before them
            # Format usually: "FRI / 09:15 Free Practice Nr. 1"
            def get_time(keyword, blob):
                match = re.search(r'([A-Z]{3}\s/\s\d{2}:\d{2})\s+' + re.escape(keyword), blob, re.IGNORECASE)
                return match.group(1) if match else "NA"

            if "No data currently available" not in card_text:
                race_entry["Event Name"] = lines[2] if len(lines) > 2 else "NA"
                race_entry["Location"] = lines[3] if len(lines) > 3 else "NA"
                
                # Extract Times
                race_entry["FP1"] = get_time("Free Practice Nr. 1", card_text)
                race_entry["Practice"] = get_time("Practice", card_text)
                race_entry["FP2"] = get_time("Free Practice Nr. 2", card_text)
                race_entry["Q1"] = get_time("Qualifying Nr. 1", card_text)
                race_entry["Q2"] = get_time("Qualifying Nr. 2", card_text)
                race_entry["Sprint"] = get_time("Tissot Sprint", card_text)
                race_entry["Warm Up"] = get_time("Warm Up", card_text)
                race_entry["Race"] = get_time("Grand Prix", card_text)
            else:
                # If no data, we still try to get Name/Location from top lines
                race_entry["Event Name"] = lines[1] if len(lines) > 1 else "NA"
                print(f"   ℹ️ {race_entry['Event Name']}: No schedule yet.")

            all_races.append(race_entry)

        browser.close()

    # Save to CSV
    if all_races:
        df = pd.DataFrame(all_races)
        df.to_csv("sports_update.csv", index=False)
        print(f"📊 Success! Saved {len(df)} rounds to sports_update.csv")
    else:
        print("❌ Error: No data could be parsed.")
        sys.exit(1)

if __name__ == "__main__":
    run_direct_list_scrape()
        
