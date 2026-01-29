import pandas as pd

# 1. Targeted URL (Example: a world sports calendar or specific tournament)
url = "https://www.motogp.com/en/calendar?view=list"

# 2. Extract tables
tables = pd.read_html(url)
df = tables[0] # Usually the first table is the schedule

# 3. Format as per your requirement
# (Tournament Name, Teams, Fixtures, Results)
df['Tournament'] = "T20 World Cup"
df.to_csv("daily_schedule.csv", index=False)
