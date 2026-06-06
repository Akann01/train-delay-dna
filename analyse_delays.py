"""
Day 2 — Delay Pattern Analysis
================================
This script reads train_delays.csv and extracts meaningful patterns.

What it does:
1. Finds which station causes the most delay per train
2. Calculates how delay builds up across the journey
3. Checks if weekends/evenings affect delay
4. Labels each train with a "delay personality"
5. Saves a summary file: train_analysis.csv

Run:
    pip install pandas numpy
    python analyse_delays.py
"""

import pandas as pd
import numpy as np

# ── Load the data we created on Day 1 ────────────────────────────────────────
print("📂 Loading train_delays.csv...")
df = pd.read_csv("train_delays.csv")
print(f"   Loaded {len(df):,} rows\n")

# ── ANALYSIS 1: Average delay at each station per train ──────────────────────
# This tells us WHERE each train loses the most time
print("=" * 60)
print("ANALYSIS 1 — Which station causes the most delay?")
print("=" * 60)

# Group by train + station, calculate average delay
station_delays = (
    df.groupby(["train_no", "train_name", "station", "station_index", "is_bottleneck"])
    ["delay_minutes"]
    .mean()
    .round(1)
    .reset_index()
)

# For each train, find the single worst station
worst_stations = (
    station_delays
    .sort_values("delay_minutes", ascending=False)
    .groupby("train_no")
    .first()
    .reset_index()
    [["train_no", "train_name", "station", "delay_minutes"]]
    .rename(columns={"station": "worst_station", "delay_minutes": "worst_station_avg_delay"})
)

print(worst_stations.to_string(index=False))

# ── ANALYSIS 2: Delay build-up across the journey ────────────────────────────
# This shows the "delay personality" — does the train get worse and worse,
# or does it recover after the bottleneck?
print("\n" + "=" * 60)
print("ANALYSIS 2 — How does delay build up across the journey?")
print("=" * 60)

journey_profile = (
    df.groupby(["train_no", "train_name", "station_index"])
    ["delay_minutes"]
    .mean()
    .round(1)
    .reset_index()
)

for train_no in df["train_no"].unique():
    train_name = df[df["train_no"] == train_no]["train_name"].iloc[0]
    profile = journey_profile[journey_profile["train_no"] == train_no]

    first_delay = profile["delay_minutes"].iloc[0]   # Delay at origin
    last_delay  = profile["delay_minutes"].iloc[-1]  # Delay at destination
    max_delay   = profile["delay_minutes"].max()
    max_station_idx = profile["delay_minutes"].idxmax()
    max_station = df[
        (df["train_no"] == train_no) &
        (df["station_index"] == profile.loc[max_station_idx, "station_index"])
    ]["station"].iloc[0]

    delay_gained    = last_delay - first_delay   # Total delay added during journey
    delay_recovered = max_delay - last_delay     # How much it recovered after peak

    print(f"\n  {train_name} ({train_no})")
    print(f"    Start delay : {first_delay} min")
    print(f"    Peak delay  : {max_delay} min  @ {max_station}")
    print(f"    End delay   : {last_delay} min")
    print(f"    Total gained: +{delay_gained:.1f} min across journey")
    print(f"    Recovered   : {delay_recovered:.1f} min after peak")

# ── ANALYSIS 3: Weekday vs Weekend delay ─────────────────────────────────────
print("\n" + "=" * 60)
print("ANALYSIS 3 — Do weekends have less delay?")
print("=" * 60)

weekend_effect = (
    df.groupby(["train_no", "train_name", "is_weekend"])
    ["delay_minutes"]
    .mean()
    .round(1)
    .unstack("is_weekend")
    .reset_index()
)
weekend_effect.columns = ["train_no", "train_name", "weekday_avg", "weekend_avg"]
weekend_effect["weekend_saves"] = (weekend_effect["weekday_avg"] - weekend_effect["weekend_avg"]).round(1)

print(weekend_effect[["train_name", "weekday_avg", "weekend_avg", "weekend_saves"]].to_string(index=False))

# ── ANALYSIS 4: Evening vs Morning delay ─────────────────────────────────────
print("\n" + "=" * 60)
print("ANALYSIS 4 — Is evening travel worse?")
print("=" * 60)

# Create a simple time bucket: Morning (6-12), Afternoon (12-18), Evening (18-22)
def time_bucket(hour):
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    else:
        return "Evening"

df["time_of_day"] = df["departure_hour"].apply(time_bucket)

time_effect = (
    df.groupby("time_of_day")["delay_minutes"]
    .mean()
    .round(1)
    .reset_index()
    .rename(columns={"delay_minutes": "avg_delay_minutes"})
)
print(time_effect.to_string(index=False))

# ── ANALYSIS 5: Assign a Delay Personality to each train ─────────────────────
# This is the KEY output — a label that summarizes each train's behavior.
# This is what your AI report card will explain in plain English.
print("\n" + "=" * 60)
print("ANALYSIS 5 — Delay Personality Labels")
print("=" * 60)

def assign_personality(train_no, journey_profile_df, station_delays_df):
    """
    Looks at a train's delay pattern and assigns one of four personalities:

    BOTTLENECK-HEAVY   → One station is responsible for most of the delay
    CONSISTENTLY LATE  → Delay builds steadily across every station (no single culprit)
    EVENING-SENSITIVE  → Delay is much higher for evening departures
    RECOVERY CHAMPION  → Delay peaks mid-journey but the train makes up time later
    """
    profile = journey_profile_df[journey_profile_df["train_no"] == train_no]
    stations = station_delays_df[station_delays_df["train_no"] == train_no]

    # Metric 1: What % of total delay happens AT the bottleneck station?
    total_delay_range = profile["delay_minutes"].max() - profile["delay_minutes"].min()
    bottleneck_jump   = stations[stations["is_bottleneck"] == True]["delay_minutes"].max()
    bottleneck_share  = bottleneck_jump / total_delay_range if total_delay_range > 0 else 0

    # Metric 2: Does the train recover after its peak?
    peak_idx      = profile["delay_minutes"].idxmax()
    peak_position = profile.loc[peak_idx, "station_index"]
    total_stations = profile["station_index"].max()
    last_delay    = profile["delay_minutes"].iloc[-1]
    peak_delay    = profile["delay_minutes"].max()
    recovery      = peak_delay - last_delay   # Higher = more recovery

    # Metric 3: How steady is the delay growth? (std dev of differences)
    delay_diffs = profile["delay_minutes"].diff().dropna()
    steadiness  = delay_diffs.std()   # Low std = very steady/consistent growth

    # ── Decision logic ───────────────────────────────────────────────────────
    if bottleneck_share > 0.5:
        # More than 50% of delay happens at one station
        personality = "BOTTLENECK-HEAVY"
        reason = f"Over {bottleneck_share*100:.0f}% of delay concentrated at one station"

    elif recovery > 15 and peak_position < total_stations * 0.6:
        # Peaks early and recovers significantly
        personality = "RECOVERY CHAMPION"
        reason = f"Peaks mid-journey but recovers {recovery:.0f} min by destination"

    elif steadiness < 8:
        # Very steady, even delay growth — no single culprit
        personality = "CONSISTENTLY LATE"
        reason = "Delay builds evenly across every station, no single cause"

    else:
        personality = "EVENING-SENSITIVE"
        reason = "Delay pattern varies significantly by time of departure"

    return personality, reason


personalities = []
for train_no in df["train_no"].unique():
    train_name = df[df["train_no"] == train_no]["train_name"].iloc[0]
    personality, reason = assign_personality(train_no, journey_profile, station_delays)
    personalities.append({
        "train_no":    train_no,
        "train_name":  train_name,
        "personality": personality,
        "reason":      reason,
    })
    print(f"\n  {train_name} ({train_no})")
    print(f"    Personality : {personality}")
    print(f"    Because     : {reason}")

# ── Save everything to a summary CSV ─────────────────────────────────────────
print("\n" + "=" * 60)
print("SAVING RESULTS")
print("=" * 60)

# Merge all analysis results into one summary table
personalities_df = pd.DataFrame(personalities)

summary = (
    personalities_df
    .merge(worst_stations, on=["train_no", "train_name"])
    .merge(weekend_effect[["train_no", "weekday_avg", "weekend_avg", "weekend_saves"]], on="train_no")
)

# Also add overall average delay per train
avg_delays = df.groupby("train_no")["delay_minutes"].mean().round(1).reset_index()
avg_delays.columns = ["train_no", "overall_avg_delay"]
summary = summary.merge(avg_delays, on="train_no")

summary.to_csv("train_analysis.csv", index=False)
print(f"\n✅ Saved: train_analysis.csv")
print(f"   Rows: {len(summary)}")
print("\nFull summary table:")
print(summary.to_string(index=False))

print("\n✅ Day 2 complete! You now have:")
print("   train_delays.csv    → raw data (from Day 1)")
print("   train_analysis.csv  → patterns + personality labels (from today)")
print("\n   You're ready for Day 3 — charts and visualisation!")