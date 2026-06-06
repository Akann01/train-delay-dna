"""
Day 4 — AI Report Card Generator (Groq Version)
====================================
Uses Groq API (free tier) with Llama 3 to generate plain-English
report cards explaining each train's delay pattern.

This gets imported into dashboard.py — you don't run this file directly.
"""

import os
from groq import Groq
import pandas as pd


def generate_report_card(train_summary: pd.Series, station_stats: pd.DataFrame) -> str:

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "GROQ_API_KEY not found. Please set it in your terminal with: set GROQ_API_KEY=your_key_here"

    client = Groq(api_key=api_key)

    # Build station breakdown text
    station_lines = []
    for _, row in station_stats.iterrows():
        marker = " <- BOTTLENECK" if row["is_bottleneck"] else ""
        station_lines.append(f"  {row['station']}: {row['delay_minutes']} min avg delay{marker}")
    station_text = "\n".join(station_lines)

    prompt = f"""You are a data analyst writing a report card for an Indian Railways train.
Explain the delay pattern in plain English that any passenger can understand.
Be specific, use the numbers given, and give one practical travel tip at the end.
Write in 4-5 sentences. Do not use bullet points. Do not use headers.

Train: {train_summary['train_name']} (No. {train_summary['train_no']})
Delay Personality: {train_summary['personality']}
Reason: {train_summary['reason']}
Overall Average Delay: {train_summary['overall_avg_delay']} minutes
Worst Station: {train_summary['worst_station']} ({train_summary['worst_station_avg_delay']} min avg delay)
Weekday Average: {train_summary['weekday_avg']} min | Weekend Average: {train_summary['weekend_avg']} min
Weekend saves: {train_summary['weekend_saves']} minutes

Station breakdown:
{station_text}

Write the report card now:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )

    return response.choices[0].message.content
