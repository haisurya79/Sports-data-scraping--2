import pandas as pd
from playwright.sync_api import sync_playwright
import re
import sys

# The Official URL
MOTOGP_URL = "https://www.motogp.com/en/calendar?view=list"

def run_official_scrape():
    data = []
    
    print("Launching Headless Browser...")
    with sync_playwright() as p:
        # Launch Chromium (headless means invisible)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Navigating to {MOTOGP_URL}...")
        page.goto(MOTOGP_URL)
        
        # 1. Wait for the site to load the events
        # We wait until the text "Grand Prix" appears on screen
        try:
            page.wait_for_selector('text=Grand Prix', timeout=60000)
            print("Page loaded successfully.")
        except:
            print("Error: Page took too long or content is blocked.")
            browser.close()
            sys.exit(1)

        # 2. Extract specific event containers
        # Strategy: We look for the main container or list items.
        # Since class names change, we grab all text and parse it with Regex
        # or we find elements that look like race cards.
        
        # This selector targets the list items in the 'list' view
        # We assume they are list items (li) or divs inside the calendar wrapper
        events = page.locator('.calendar-listing__event-container')
        
        # Fallback: If specific class not found, grab all links containing 'calendar'
        if events.count() == 0:
            print("Using fallback selector...")
            events = page.locator('a[href*="/calendar/"]:has-text("Grand Prix")')

        count = events.count()
        print(f"Found {count} potential events.")

        for i in range(count):
            try:
                # Get the text of the entire event card
                text_content = events.nth(i).inner_text()
                
                # Use standard splitting to separate lines
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                # Basic parsing logic (adjust based on actual site output)
                # Usually: Date is near top, Title contains "Grand Prix", Location is capitalized
                
                # Finding the "Grand Prix" name
                gp_name = next((line for line in lines if "Grand Prix" in line), "Unknown GP")
                
                # Finding the Date (Regex looks for patterns like '27 Feb - 01 Mar')
                date_match = re.search(r'\d{1,2}\s+[A-Za-z]{3}\s*-\s*\d{1,2}\s+[A-Za-z]{3}', text_content)
                date = date_match.group(0) if date_match else "Date TBD"
                
                # Finding Location (Usually the line before or after the GP Name)
                # This is a heuristic; might need tweaking after first run
                location = "Unknown Location"
                for line in lines:
                    if line.isupper() and len(line) > 3 and "GRAND PRIX" not in line:
                        location = line
                        break

                entry = {
                    "Tournament": "MotoGP 2026",
                    "Event Name": gp_name,
                    "Date": date,
                    "Location": location,
                    "Source": "Official MotoGP.com"
                }
                
                # Avoid duplicates
                if entry not in data:
                    data.append(entry)

            except Exception as e:
                print(f"Skipping an item due to error: {e}")
                continue

        browser.close()

    if not data:
        print("CRITICAL: No data scraped. The website structure might have changed.")
        sys.exit(1)

    # 3. Save
    df = pd.DataFrame(data)
    
    # Clean up: Remove rows where Date is TBD if you only want confirmed ones
    df = df[df['Date'] != "Date TBD"]
    
    df.to_csv("sports_update.csv", index=False)
    print(f"Success! Saved {len(df)} races to sports_update.csv")

if __name__ == "__main__":
    run_official_scrape()
