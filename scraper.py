import pandas as pd
from playwright.sync_api import sync_playwright
import time
import sys

# The Official URL
CALENDAR_URL = "https://www.motogp.com/en/calendar"

def run_deep_scrape():
    all_races = []

    print("🚀 Launching Robust Scraper...")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"📡 Navigating to {CALENDAR_URL}...")
        try:
            page.goto(CALENDAR_URL, timeout=60000, wait_until="domcontentloaded")
            # Wait a moment for the dynamic list to populate
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Warning during load: {e}")

        # --- FIX: ROBUST LINK FINDER ---
        # Instead of looking for one specific class, we grab ALL links 
        # and filter for the ones that go to an 'event' page.
        print("🔍 Scanning for race links...")
        
        # Get all anchor tags with an href attribute
        links = page.locator("a[href]").evaluate_all("els => els.map(e => e.href)")
        
        # Filter: Keep only links that contain '/event/' or '/calendar/' AND seem to be specific races
        # We assume 2026 links might look like .../calendar/2026/event/...
        race_links = sorted(list(set([
            l for l in links 
            if ("/event/" in l) and ("calendar" in l) and (l != CALENDAR_URL)
        ])))

        print(f"✅ Found {len(race_links)} potential race pages.")

        if len(race_links) == 0:
            print("❌ No links found. Dumping page content for debug (first 500 chars):")
            print(page.content()[:500])
            sys.exit(1)

        # Step 2: Loop through every race link
        for index, link in enumerate(race_links):
            # Default empty data
            race_data = {
                "Round": index + 1,
                "Event Name": "NA",
                "Location": "NA",
                "FP1": "NA", "Practice": "NA", "FP2": "NA", 
                "Q1": "NA", "Q2": "NA", 
                "Sprint": "NA", "Warm Up": "NA", "Race": "NA"
            }

            try:
                print(f"   👉 Visiting ({index+1}/{len(race_links)}): {link}")
                page.goto(link, timeout=45000, wait_until="domcontentloaded")
                
                # Try to get the Event Name (it's usually the biggest header)
                try:
                    race_data["Event Name"] = page.locator("h1").first.inner_text().strip()
                except:
                    race_data["Event Name"] = "Unknown GP"

                # Try to find the Schedule Table
                # We look for text "Session Times" or table rows
                try:
                    # Generic waiter for any table-like element
                    page.wait_for_selector('div, table', state="attached")
                    
                    # Grab all text that looks like a schedule row
                    # We search for the container that holds the schedule
                    rows = page.locator("div").filter(has_text="Free Practice").all()
                    
                    # If the specific div filter fails, try a broader text search
                    if len(rows) < 3:
                        # Fallback: Get all text on page and parse lines
                        content_text = page.locator("body").inner_text()
                        lines = content_text.split('\n')
                    else:
                        lines = [r.inner_text() for r in rows]

                    # Parse the found text for times
                    # This is a 'greedy' parser: it looks for the keyword and grabs the time near it
                    full_text = page.locator("body").inner_text().lower()
                    
                    # Helper to find time near a keyword in the text blob
                    def find_time_for(keyword, text_blob):
                        # Simple logic: Find keyword, look at 20 chars before it for a time pattern (XX:XX)
                        try:
                            idx = text_blob.find(keyword)
                            if idx == -1: return "NA"
                            # Look at the snippet around the keyword
                            snippet = text_blob[max(0, idx-50):idx+50]
                            import re
                            # Find XX:XX time pattern
                            match = re.search(r'\d{2}:\d{2}', snippet)
                            return match.group(0) if match else "NA"
                        except:
                            return "NA"

                    # Map keywords to columns
                    race_data["FP1"] = find_time_for("free practice nr. 1", full_text)
                    race_data["Practice"] = find_time_for("practice", full_text)
                    # Avoid confusion between Practice and Free Practice 2
                    if race_data["Practice"] == race_data["FP1"]: race_data["Practice"] = "NA"
                    
                    race_data["FP2"] = find_time_for("free practice nr. 2", full_text)
                    race_data["Q1"] = find_time_for("qualifying nr. 1", full_text)
                    race_data["Q2"] = find_time_for("qualifying nr. 2", full_text)
                    race_data["Sprint"] = find_time_for("sprint", full_text)
                    race_data["Warm Up"] = find_time_for("warm up", full_text)
                    race_data["Race"] = find_time_for("grand prix", full_text)
                    
                    # If specific "Race" extraction failed, try finding the MAIN race time
                    if race_data["Race"] == "NA":
                        race_data["Race"] = find_time_for("motogp™ race", full_text)

                except Exception as e:
                    print(f"      ⚠️ Could not parse schedule: {e}")

            except Exception as e:
                print(f"      ❌ Error on page {link}: {e}")
            
            all_races.append(race_data)
            time.sleep(1) # Be polite

        browser.close()

    # Step 3: Save
    if not all_races:
        print("CRITICAL: No data collected.")
        sys.exit(1)

    df = pd.DataFrame(all_races)
    df.to_csv("sports_update.csv", index=False)
    print("DONE! File saved.")

if __name__ == "__main__":
    run_deep_scrape()
