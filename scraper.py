import requests
import csv
from datetime import datetime

# API Endpoints
BASE_URL = "https://api.motogp.pulselive.com/motogp/v1"
# Season UUID for 2026 (Retrieved via /results/seasons)
SEASON_UUID = "60742f56-6f7d-410a-85d8-41716301362e" # Standard 2026 ID
CATEGORY_UUID = "e8c110ad-64aa-4e8e-8a86-f2f152f6a942" # MotoGP category

def format_session_date(iso_date_str):
    """Converts ISO date to 'Day Name DDMMYY HH:MM'"""
    if not iso_date_str:
        return "NA"
    dt = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
    return dt.strftime("%A %d%m%y %H:%M")

def get_calendar_data():
    print("Fetching calendar events...")
    events_resp = requests.get(f"{BASE_URL}/results/events?seasonUuid={SEASON_UUID}")
    events = events_resp.json()
    
    # Define columns requested by user
    headers = [
        "Sl. No", "Country", "city", "period", "free practice nr1", 
        "Practice", "Free practice NR2", "Qualifiying NR1", 
        "Qualifying NR2", "TISSOT Sprint", "Warm Up", "Grand prix"
    ]
    
    rows = []
    
    for idx, event in enumerate(events, 1):
        event_name = event.get("short_name", "")
        country = event.get("country", {}).get("name", "")
        city = event.get("location", "")
        
        # Format Period (e.g., 27 Feb - 01 Mar)
        start_date = datetime.fromisoformat(event['start_date'].split('T')[0])
        end_date = datetime.fromisoformat(event['end_date'].split('T')[0])
        period = f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b')}"
        
        row = {
            "Sl. No": idx,
            "Country": country,
            "city": city,
            "period": period,
            "free practice nr1": "NA",
            "Practice": "NA",
            "Free practice NR2": "NA",
            "Qualifiying NR1": "NA",
            "Qualifying NR2": "NA",
            "TISSOT Sprint": "NA",
            "Warm Up": "NA",
            "Grand prix": "NA"
        }
        
        # Fetch detailed sessions for this event
        event_id = event['id']
        sessions_url = f"{BASE_URL}/results/sessions?eventUuid={event_id}&categoryUuid={CATEGORY_UUID}"
        sessions_resp = requests.get(sessions_url)
        
        if sessions_resp.status_code == 200:
            sessions = sessions_resp.json()
            for s in sessions:
                # Mapping API session names to your specific column headers
                s_name = s['type'] # e.g., FP1, PR, FP2, Q1, Q2, SPR, WUP, RAC
                s_date = format_session_date(s.get('date'))
                
                if s_name == "FP1": row["free practice nr1"] = s_date
                elif s_name == "PR": row["Practice"] = s_date
                elif s_name == "FP2": row["Free practice NR2"] = s_date
                elif s_name == "Q1": row["Qualifiying NR1"] = s_date
                elif s_name == "Q2": row["Qualifying NR2"] = s_date
                elif s_name == "SPR": row["TISSOT Sprint"] = s_date
                elif s_name == "WUP": row["Warm Up"] = s_date
                elif s_name == "RAC": row["Grand prix"] = s_date
        
        rows.append(row)
        print(f"Processed: {country} ({city})")

    # Save to CSV
    with open('motogp_calendar_2026.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    
    print("\nSuccess! Data saved to 'motogp_calendar_2026.csv'")

if __name__ == "__main__":
    get_calendar_data()
