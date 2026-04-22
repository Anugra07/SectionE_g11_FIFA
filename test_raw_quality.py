#!/usr/bin/env python3
"""
Raw FIFA CSV Data Quality Test Suite
- WorldCups.csv
- WorldCupMatches.csv
- WorldCupPlayers.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/raw")
FILES = {
    "WorldCups": DATA_DIR / "WorldCups.csv",
    "WorldCupMatches": DATA_DIR / "WorldCupMatches.csv",
    "WorldCupPlayers": DATA_DIR / "WorldCupPlayers.csv",
}

MIN_ROWS_COMBINED = 10_000
MIN_COLUMNS_EACH = 8

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️ WARN"

results = []


def log(section: str, test_name: str, status: str, detail: str = "") -> None:
    results.append((section, test_name, status, detail))
    print(f"  [{status.split()[0]}] {test_name}: {detail}")


print("\n" + "=" * 60)
print("  SECTION 0 — FILE LOADING")
print("=" * 60)

dfs: dict[str, pd.DataFrame] = {}
for name, path in FILES.items():
    try:
        dfs[name] = pd.read_csv(path, encoding="utf-8")
        log("Loading", f"Load {path}", PASS, f"{len(dfs[name])} rows loaded")
    except FileNotFoundError:
        log("Loading", f"Load {path}", FAIL, "File not found")
        sys.exit(1)

cups = dfs["WorldCups"]
matches = dfs["WorldCupMatches"]
players = dfs["WorldCupPlayers"]
matches_clean = matches.dropna(subset=["Year"]) if "Year" in matches.columns else matches

print("\n" + "=" * 60)
print("  SECTION 1 — SHAPE VALIDATION")
print("=" * 60)

total_rows = sum(len(df) for df in dfs.values())
log("Shape", "Combined row count > 10,000", PASS if total_rows > MIN_ROWS_COMBINED else FAIL, f"Total={total_rows:,}")
for name, df in dfs.items():
    log("Shape", f"{name} has >= {MIN_COLUMNS_EACH} columns", PASS if df.shape[1] >= MIN_COLUMNS_EACH else FAIL, f"{df.shape[1]} columns")

print("\n" + "=" * 60)
print("  SECTION 2 — DATA TYPE VALIDATION")
print("=" * 60)

if "Attendance" in cups.columns:
    conv = pd.to_numeric(cups["Attendance"].astype(str).str.replace(",", "", regex=False).str.replace(".", "", regex=False), errors="coerce")
    bad = int(conv.isna().sum())
    log("DTypes", "WorldCups Attendance numeric-convertible", WARN if bad else PASS, f"{bad} non-convertible")

for col in ["Home Team Goals", "Away Team Goals"]:
    if col in matches_clean.columns:
        bad = int(pd.to_numeric(matches_clean[col], errors="coerce").isna().sum())
        log("DTypes", f"{col} numeric", PASS if bad == 0 else FAIL, f"{bad} non-numeric")

print("\n" + "=" * 60)
print("  SECTION 3 — MISSING VALUE ANALYSIS")
print("=" * 60)

critical = {
    "WorldCups": ["Year", "Country", "Winner"],
    "WorldCupMatches": ["Year", "MatchID", "RoundID", "Home Team Name", "Away Team Name"],
    "WorldCupPlayers": ["MatchID", "RoundID", "Team Initials", "Player Name"],
}
for name, cols in critical.items():
    df = matches_clean if name == "WorldCupMatches" else dfs[name]
    for col in cols:
        if col in df.columns:
            miss = int(df[col].isna().sum())
            pct = miss / len(df) * 100 if len(df) else 0
            st = PASS if miss == 0 else (WARN if pct < 5 else FAIL)
            log("Missing", f"{name}: {col}", st, f"{miss} ({pct:.1f}%)")

print("\n" + "=" * 60)
print("  SECTION 4 — DUPLICATE DETECTION")
print("=" * 60)

for name, df in dfs.items():
    d = int(df.duplicated().sum())
    log("Duplicates", f"{name} duplicate rows", PASS if d == 0 else WARN, str(d))

print("\n" + "=" * 60)
print("  SECTION 5 — CROSS-FILE CONSISTENCY")
print("=" * 60)

if "MatchID" in players.columns and "MatchID" in matches.columns:
    p = set(players["MatchID"].dropna().astype(int))
    m = set(matches["MatchID"].dropna().astype(int))
    orphan = p - m
    log("ForeignKey", "Players.MatchID exist in Matches", PASS if not orphan else FAIL, f"{len(orphan)} orphans")

if "Year" in matches.columns and "Year" in cups.columns:
    my = set(matches.dropna(subset=["Year"])["Year"].astype(int))
    cy = set(cups["Year"].dropna().astype(int))
    unknown = my - cy
    log("ForeignKey", "Matches.Year exist in Cups.Year", PASS if not unknown else WARN, f"{len(unknown)} unknown")

print("\n" + "=" * 60)
print("  FINAL SUMMARY")
print("=" * 60)

total = len(results)
passed = sum(1 for r in results if "PASS" in r[2])
warned = sum(1 for r in results if "WARN" in r[2])
failed = sum(1 for r in results if "FAIL" in r[2])
score = round((passed / total) * 100, 1) if total else 0

print(f"  Total Checks: {total}")
print(f"  Passed: {passed}")
print(f"  Warnings: {warned}")
print(f"  Failed: {failed}")
print(f"  Readiness Score: {score}%")

sys.exit(0 if failed == 0 else 1)
