#!/usr/bin/env python3
"""Fetch Shanwei tide data from tide-forecast.com and save as JSON."""
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

STATION = "Shanwei"
URL = f"https://www.tide-forecast.com/locations/{STATION}/tides/latest"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "tides.json"

MONTH_MAP = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12
}


def fetch_page(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_tides(html):
    tides = []
    # Split by day sections using tide-day__date
    sections = re.split(r'class="tide-day__date"', html)

    for sec in sections:
        # Parse date: "... Friday 27 March 2026"
        dm = re.search(
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+'
            r'(\d{1,2})\s+(\w+)\s+(\d{4})', sec
        )
        if not dm:
            continue
        day, month_str, year = dm.groups()
        month = MONTH_MAP.get(month_str)
        if not month:
            continue
        date_str = f"{year}-{month:02d}-{int(day):02d}"

        # Find all tide entries
        for tm in re.finditer(
            r'(High|Low)\s+Tide</td><td><b>\s*(\d{1,2}:\d{2})\s*(AM|PM)</b>'
            r'.*?length-value__primary">\s*(\d+\.?\d*)\s*m',
            sec, re.DOTALL | re.IGNORECASE
        ):
            ttype, time_str, ampm, height = tm.groups()
            hour, minute = map(int, time_str.split(':'))
            if ampm.upper() == 'PM' and hour != 12:
                hour += 12
            elif ampm.upper() == 'AM' and hour == 12:
                hour = 0
            tides.append({
                "date": date_str,
                "time": f"{hour:02d}:{minute:02d}",
                "height": round(float(height), 2),
                "type": ttype.lower()
            })

    tides.sort(key=lambda x: (x["date"], x["time"]))
    return tides


def main():
    print(f"Fetching tide data for {STATION}...")
    html = fetch_page(URL)
    tides = parse_tides(html)

    if not tides:
        print("ERROR: No tide data parsed!")
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "station": STATION,
        "location": {"lat": 22.78, "lng": 115.35},
        "timezone": "Asia/Shanghai",
        "updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "tides": tides
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    dates = sorted(set(t["date"] for t in tides))
    print(f"Saved {len(tides)} events, {dates[0]} ~ {dates[-1]}")


if __name__ == "__main__":
    main()
