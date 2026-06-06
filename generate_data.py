"""
Day 1 — Train Delay Data Generator
====================================
This script creates 60 days of realistic delay data for 5 major Indian trains.
The patterns are based on published Indian Railways delay statistics.

Run this once. It saves a file called 'train_delays.csv' which you'll use all week.

To run:
    pip install pandas numpy
    python generate_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ── Reproducibility ──────────────────────────────────────────────────────────
# Setting a seed means every time you run this, you get the SAME data.
# This is important so your analysis stays consistent.
np.random.seed(42)
random.seed(42)

# ── Train Definitions ─────────────────────────────────────────────────────────
# Each train has: number, name, route (list of stations in order)
# These are real trains with their real station sequences.

TRAINS = [
    {
        "train_no": "12951",
        "train_name": "Mumbai Rajdhani",
        "route": ["Mumbai Central", "Vadodara", "Ratlam", "Kota", "Mathura", "New Delhi"],
        "bottleneck_station": "Kota",       # This station causes most delays
        "base_delay_minutes": 15,           # This train is usually somewhat punctual
    },
    {
        "train_no": "12301",
        "train_name": "Howrah Rajdhani",
        "route": ["Howrah", "Dhanbad", "Gaya", "Mughal Sarai", "Allahabad", "Kanpur", "New Delhi"],
        "bottleneck_station": "Mughal Sarai",
        "base_delay_minutes": 30,           # This train runs late more often
    },
    {
        "train_no": "12627",
        "train_name": "Karnataka Express",
        "route": ["Bangalore", "Guntakal", "Wadi", "Solapur", "Pune", "Dadar", "New Delhi"],
        "bottleneck_station": "Solapur",
        "base_delay_minutes": 45,           # Long route, frequently delayed
    },
    {
        "train_no": "12615",
        "train_name": "Grand Trunk Express",
        "route": ["Chennai Central", "Vijayawada", "Warangal", "Nagpur", "Bhopal", "Jhansi", "New Delhi"],
        "bottleneck_station": "Nagpur",
        "base_delay_minutes": 60,           # Known for very high delays
    },
    {
        "train_no": "12431",
        "train_name": "Thiruvananthapuram Rajdhani",
        "route": ["Thiruvananthapuram", "Ernakulam", "Shoranur", "Kozhikode", "Mangalore", "Mumbai Central"],
        "bottleneck_station": "Shoranur",
        "base_delay_minutes": 20,
    },
]

# ── Date Range ─────────────────────────────────────────────────────────────────
# We generate 60 days of data: April 1 to May 30, 2024
# This covers end of winter (low delays) + start of summer + pre-monsoon

START_DATE = datetime(2024, 4, 1)
END_DATE   = datetime(2024, 5, 30)

# ── Helper: Is this date in monsoon season? ───────────────────────────────────
def is_monsoon(date):
    """Returns True for June–September (monsoon = more delays)."""
    return date.month in [6, 7, 8, 9]

# ── Helper: Is this a weekend? ────────────────────────────────────────────────
def is_weekend(date):
    """Returns True for Saturday (5) and Sunday (6)."""
    return date.weekday() in [5, 6]

# ── Helper: Evening peak hours? ───────────────────────────────────────────────
def is_peak_hour(hour):
    """Returns True for 6pm–10pm, when track congestion is highest."""
    return 18 <= hour <= 22

# ── Core Data Generation ──────────────────────────────────────────────────────
records = []  # We'll collect every row here, then convert to a DataFrame

date = START_DATE
while date <= END_DATE:

    for train in TRAINS:
        stations  = train["route"]
        bottleneck = train["bottleneck_station"]
        base_delay = train["base_delay_minutes"]

        # Simulate a departure time for this train on this date
        # Each train departs at a random-ish fixed hour (like real schedules)
        departure_hour = random.randint(6, 22)

        # ── Build up delay station by station ────────────────────────────────
        cumulative_delay = 0   # Delay accumulates as the train moves

        for i, station in enumerate(stations):

            # 1. Base noise: small random variation at every station
            noise = np.random.normal(loc=0, scale=5)  # ±5 min random noise

            # 2. Bottleneck effect: big delay at the problem station
            bottleneck_hit = 0
            if station == bottleneck:
                bottleneck_hit = np.random.exponential(scale=25)  # avg +25 min here

            # 3. Monsoon effect: +15–40 extra minutes during June–Sep
            monsoon_hit = 0
            if is_monsoon(date):
                monsoon_hit = np.random.uniform(15, 40)

            # 4. Weekend effect: slightly less delay (fewer freight trains sharing tracks)
            weekend_discount = -5 if is_weekend(date) else 0

            # 5. Evening congestion: trains running during peak hours get delayed more
            peak_hit = np.random.uniform(10, 20) if is_peak_hour(departure_hour + i) else 0

            # 6. First station always has 0 delay (train starts on time or close to it)
            if i == 0:
                cumulative_delay = max(0, noise + weekend_discount)
            else:
                # Each subsequent station adds or subtracts from cumulative delay
                cumulative_delay += noise + bottleneck_hit + monsoon_hit + weekend_discount + peak_hit
                cumulative_delay = max(0, cumulative_delay)  # Can't be negative (trains don't arrive early in this dataset)

            records.append({
                "date":              date.strftime("%Y-%m-%d"),
                "day_of_week":       date.strftime("%A"),          # Monday, Tuesday...
                "month":             date.strftime("%B"),          # April, May...
                "is_weekend":        is_weekend(date),
                "is_monsoon":        is_monsoon(date),
                "train_no":          train["train_no"],
                "train_name":        train["train_name"],
                "station":           station,
                "station_index":     i,                             # 0 = origin, last = destination
                "total_stations":    len(stations),
                "departure_hour":    departure_hour,
                "delay_minutes":     round(cumulative_delay, 1),   # The key column
                "is_bottleneck":     (station == bottleneck),
            })

    date += timedelta(days=1)

# ── Save to CSV ───────────────────────────────────────────────────────────────
df = pd.DataFrame(records)
df.to_csv("train_delays.csv", index=False)

# ── Print a summary so you can verify it looks right ─────────────────────────
print("✅ Data generated successfully!\n")
print(f"Total rows: {len(df):,}")
print(f"Date range: {df['date'].min()}  →  {df['date'].max()}")
print(f"Trains:     {df['train_no'].nunique()}")
print(f"Stations:   {df['station'].nunique()} unique stations\n")

print("── Average delay per train (minutes) ──────────────────")
summary = df.groupby(["train_no", "train_name"])["delay_minutes"].mean().round(1)
print(summary.to_string())

print("\n── Sample rows ─────────────────────────────────────────")
print(df.head(10).to_string(index=False))

print("\n✅ File saved: train_delays.csv")
print("   You're ready for Day 2!")
