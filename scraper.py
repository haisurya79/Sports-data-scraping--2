import pandas as pd
from playwright.sync_api import sync_playwright
import time
import sys

# The Main Calendar Page
CALENDAR_URL = "https://www.motogp.com/en/calendar?view=list"

def run_deep_scrape():
    all_races = []

    print("🚀 Launching High-Performance Scraper...")
    
    with sync_playwright() as p:
        # Launch invisible browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        # Step 1: Get the List of all Race URLs
        print(f"📡 Navigating to {CALENDAR_URL}...")
        page.goto(CALENDAR_URL, timeout=60000)
        
        try:
            # Wait for race cards to load
            page.wait_for_selector('a.calendar-listing__event-container', timeout=30000)
        except:
            print("⚠️ Could not load main list. Retrying...")
            time.sleep(2)

        # Grab all links to individual events
        # We look for links that look like "/en/event/..."
        race_links = page.locator('a.calendar-listing__event-container').evaluate_all("els => els.map(e => e.href)")
        
        print(f"✅ Found {len(race_links)} races. Starting deep dive...")

        # Step 2: Loop through every single race link
        for index, link in enumerate(race_links):
            # initialize our data structure with "NA"
            race_data = {
                "Tournament": "MotoGP 2026", # Or current season
                "Round": index + 1,
                "Event Name": "NA",
                "Location": "NA",
                "FP1": "NA",
                "Practice": "NA",
                "FP2": "NA",
                "Q1": "NA",
                "Q2": "NA",
                "Sprint": "NA",
                "Warm Up": "NA",
                "Race": "NA"
            }

            try:
                print(f"   👉 Scraping Race {index+1}/{len(race_links)}: {link}")
                page.goto(link, timeout=45000)
                
                # Wait for the specific "Session" table to appear
                # We wait briefly; if not found, it likely means schedule isn't out yet
                try:
                    page.wait_for_selector('.c-schedule-table__row', timeout=5000)
                except:
                    print("      ⚠️ No schedule table found (likely TBD). Keeping as NA.")
                    all_races.append(race_data)
                    continue

                # 2A. Get Basic Info (Name/Location) from the header
                try:
                    race_data["Event Name"] = page.locator('h1.event-hero__title').inner_text().strip()
                    race_data["Location"] = page.locator('.event-hero__location').first.inner_text().strip()
                except:
                    race_data["Event Name"] = "Unknown GP"

                # 2B. Scrape the Session Table (The screenshot part)
                # We find all rows in the schedule table
                rows = page.locator('.c-schedule-table__row')
                count = rows.count()

                for i in range(count):
                    row_text = rows.nth(i).inner_text()
                    # row_text usually looks like: "FRI 09:15 \n Free Practice Nr. 1"
                    
                    # Clean up text
                    lines = [l.strip() for l in row_text.split('\n') if l.strip()]
                    if len(lines) < 2: continue
                    
                    time_info = lines[0] # e.g., "FRI / 09:15"
                    session_name = lines[1].lower() # e.g., "free practice nr. 1"

                    # Map to our columns based on keywords
                    if "free practice nr. 1" in session_name:
                        race_data["FP1"] = time_info
                    elif "practice" in session_name and "nr" not in session_name:
                        race_data["Practice"] = time_info
                    elif "free practice nr. 2" in session_name:
                        race_data["FP2"] = time_info
                    elif "qualifying nr. 1" in session_name:
                        race_data["Q1"] = time_info
                    elif "qualifying nr. 2" in session_name:
                        race_data["Q2"] = time_info
                    elif "sprint" in session_name:
                        race_data["Sprint"] = time_info
                    elif "warm up" in session_name:
                        race_data["Warm Up"] = time_info
                    elif "grand prix" in session_name and "race" not in session_name:
                        # Sometimes listed as just "Grand Prix" or "MotoGP Race"
                        race_data["Race"] = time_info

                print(f"      ✅ Success! Found schedule for {race_data['Event Name']}")

            except Exception as e:
                print(f"      ❌ Error on this page: {e}")
            
            all_races.append(race_data)
            
            # small pause to be polite to the server
            time.sleep(1)

        browser.close()

    # Step 3: Save to CSV
    if not all_races:
        print("CRITICAL: No data collected.")
        sys.exit(1)

    df = pd.DataFrame(all_races)
    
    # Reorder columns specifically for your view
    cols = ["Round", "Event Name", "Location", "FP1", "Practice", "FP2", "Q1", "Q2", "Sprint", "Warm Up", "Race"]
    # Ensure all cols exist even if empty
    for c in cols:
        if c not in df.columns: df[c] = "NA"
            
    df = df[cols]
    df.to_csv("sports_update.csv", index=False)
    print("DONE! File saved.")

if __name__ == "__main__":
    run_deep_scrape()
