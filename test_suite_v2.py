#!/usr/bin/env python3
"""
Combined CSV Merge & Join Validation Suite v2.0
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path('data')
RAW_DIR = BASE_DIR / 'raw'
PROCESSED_DIR = BASE_DIR / 'processed'

FILES = {
    'WorldCups': RAW_DIR / 'WorldCups.csv',
    'WorldCupMatches': RAW_DIR / 'WorldCupMatches.csv',
    'WorldCupPlayers': RAW_DIR / 'WorldCupPlayers.csv',
}

MIN_ROWS_COMBINED = 10_000
MIN_COLUMNS_EACH = 8
MIN_COLUMNS_COMBINED = 15
OUTPUT_COMBINED_CSV = PROCESSED_DIR / 'WorldCup_Combined.csv'

PASS = '✅ PASS'
FAIL = '❌ FAIL'
WARN = '⚠️  WARN'

results: list[tuple[str, str, str, str]] = []


def log(section: str, test_name: str, status: str, detail: str = '') -> None:
    results.append((section, test_name, status, detail))
    tag = status.split()[0]
    print(f'  [{tag}] {test_name}: {detail}')


def section_header(title: str) -> None:
    print('\n' + '=' * 65)
    print(f'  {title}')
    print('=' * 65)


def main() -> None:
    section_header('SECTION 0 — FILE LOADING')
    dfs: dict[str, pd.DataFrame] = {}
    for name, path in FILES.items():
        try:
            dfs[name] = pd.read_csv(path, encoding='utf-8')
            log('Loading', f'Load {path}', PASS, f"{len(dfs[name])} rows, {dfs[name].shape[1]} cols")
        except FileNotFoundError:
            log('Loading', f'Load {path}', FAIL, 'File not found — ensure data/raw exists')
            sys.exit(1)

    cups = dfs['WorldCups'].copy()
    matches = dfs['WorldCupMatches'].copy()
    players = dfs['WorldCupPlayers'].copy()

    section_header('SECTION 1 — SHAPE VALIDATION (Pre-Clean)')
    total_rows = sum(len(df) for df in dfs.values())
    log('Shape', 'Combined raw row count > 10,000', PASS if total_rows > MIN_ROWS_COMBINED else FAIL, f'Total = {total_rows:,}')
    for name, df in dfs.items():
        log('Shape', f'{name} has >= {MIN_COLUMNS_EACH} columns', PASS if df.shape[1] >= MIN_COLUMNS_EACH else FAIL, f'{df.shape[1]} columns')

    section_header('SECTION 2 — DATA CLEANING (Pre-Merge)')
    cups_before = len(cups)
    cups['Attendance'] = pd.to_numeric(cups['Attendance'].astype(str).str.replace(',', '', regex=False).str.replace('.', '', regex=False), errors='coerce')
    cups['Year'] = pd.to_numeric(cups['Year'], errors='coerce')
    cups = cups.dropna(subset=['Year']).copy()
    cups['Year'] = cups['Year'].astype(int)
    cups = cups.drop_duplicates().copy()
    log('Cleaning', 'WorldCups: dropna Year + dedup', PASS, f'{cups_before} → {len(cups)} rows')

    matches_before = len(matches)
    matches['Year'] = pd.to_numeric(matches['Year'], errors='coerce')
    matches = matches.dropna(subset=['Year']).copy()
    matches['Year'] = matches['Year'].astype(int)
    for col in ['Home Team Goals', 'Away Team Goals', 'Half-time Home Goals', 'Half-time Away Goals', 'Attendance']:
        if col in matches.columns:
            matches[col] = pd.to_numeric(matches[col], errors='coerce')
    matches = matches.drop_duplicates().copy()
    log('Cleaning', 'WorldCupMatches: dropna Year + cast + dedup', PASS, f'{matches_before} → {len(matches)} rows')

    players_before = len(players)
    players = players.dropna(subset=['MatchID']).copy()
    players['MatchID'] = pd.to_numeric(players['MatchID'], errors='coerce').astype('Int64')
    if 'RoundID' in players.columns:
        players['RoundID'] = pd.to_numeric(players['RoundID'], errors='coerce').astype('Int64')
    if 'Shirt Number' in players.columns:
        players['Shirt Number'] = players['Shirt Number'].replace(0, np.nan)
    players = players.drop_duplicates().copy()
    log('Cleaning', 'WorldCupPlayers: dropna MatchID + cast + dedup', PASS, f'{players_before} → {len(players)} rows')
    players["Shirt Number"] = players["Shirt Number"].replace(0, np.nan)
players = players.drop_duplicates()
log("Cleaning", "WorldCupPlayers: dropna MatchID + cast + dedup", PASS, f"{players_before} → {len(players)} rows")

for df in (cups, matches, players):
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
log("Cleaning", "All files: Strip whitespace", PASS, "Done")

if "Stage" in matches.columns:
    before_unique = matches["Stage"].nunique()
    matches["Stage"] = matches["Stage"].str.replace(r"Group\s+\d+", "Group Stage", regex=True)
    after_unique = matches["Stage"].nunique()
    log("Cleaning", "WorldCupMatches: Normalize Stage names", PASS, f"{before_unique} → {after_unique}")

section_header("SECTION 3 — JOIN KEY VALIDATION")

cups_years = set(cups["Year"].unique())
matches_years = set(matches["Year"].unique())
log("JoinKey", "Matches.Year ⊆ WorldCups.Year", PASS if not (matches_years - cups_years) else WARN, f"Orphan years: {matches_years - cups_years or 'None'}")
log("JoinKey", "WorldCups.Year ⊆ Matches.Year", PASS if not (cups_years - matches_years) else WARN, f"Extra cup years: {cups_years - matches_years or 'None'}")

match_ids = set(matches["MatchID"].dropna().astype(int))
player_mids = set(players["MatchID"].dropna().astype(int))
orphan_pmids = player_mids - match_ids
log("JoinKey", "Players.MatchID ⊆ Matches.MatchID", PASS if not orphan_pmids else FAIL, f"Orphan MatchIDs: {len(orphan_pmids)}")

round_ids_m = set(matches["RoundID"].dropna().astype(int))
round_ids_p = set(players["RoundID"].dropna().astype(int))
orphan_rids = round_ids_p - round_ids_m
log("JoinKey", "Players.RoundID ⊆ Matches.RoundID", PASS if not orphan_rids else FAIL, f"Orphan RoundIDs: {len(orphan_rids)}")

log("JoinKey", "MatchID join coverage", PASS, f"{len(player_mids & match_ids)} MatchIDs present in both")

for df, col, name in [
    (matches, "MatchID", "Matches"),
    (matches, "RoundID", "Matches"),
    (players, "MatchID", "Players"),
    (players, "RoundID", "Players"),
    (matches, "Year", "Matches"),
    (cups, "Year", "Cups"),
]:
    nulls = int(df[col].isna().sum())
    log("JoinKey", f"{name}.{col} null check", PASS if nulls == 0 else FAIL, f"{nulls} nulls")

section_header("SECTION 4 — THREE-FILE MERGE & LOSS ANALYSIS")

rows_before_m1 = len(players)
merged_pm = players.merge(matches, on=["MatchID", "RoundID"], how="left", suffixes=("_player", "_match"))
rows_after_m1 = len(merged_pm)

year_col = "Year_match" if "Year_match" in merged_pm.columns else "Year"
unmatched_m1 = int(merged_pm[year_col].isna().sum()) if year_col in merged_pm.columns else 0
log("Merge", "Step 1: Players LEFT JOIN Matches (MatchID + RoundID)", PASS if unmatched_m1 == 0 else WARN, f"{rows_before_m1} → {rows_after_m1} | unmatched={unmatched_m1}")

rows_before_m2 = len(merged_pm)
if year_col in merged_pm.columns:
    merged_pm[year_col] = pd.to_numeric(merged_pm[year_col], errors="coerce").astype("Int64")
combined = merged_pm.merge(cups, left_on=year_col, right_on="Year", how="left", suffixes=("", "_cup"))
rows_after_m2 = len(combined)
unmatched_m2 = int(combined["Winner"].isna().sum()) if "Winner" in combined.columns else 0
log("Merge", "Step 2: merged LEFT JOIN WorldCups (Year)", PASS if unmatched_m2 == 0 else WARN, f"{rows_before_m2} → {rows_after_m2} | unmatched={unmatched_m2}")

loss = rows_before_m1 - rows_after_m2
loss_pct = (loss / rows_before_m1) * 100 if rows_before_m1 else 0
log("Merge", "Total row loss across all joins", PASS if loss_pct < 5 else WARN, f"{loss} rows ({loss_pct:.2f}%)")
log("Merge", "Final combined shape", PASS, f"{combined.shape[0]:,} rows × {combined.shape[1]} columns")

section_header("SECTION 5 — COMBINED DATASET VALIDATION")
log("Combined", "Combined rows > 10,000", PASS if len(combined) > MIN_ROWS_COMBINED else FAIL, f"{len(combined):,} rows")
log("Combined", f"Combined columns >= {MIN_COLUMNS_COMBINED}", PASS if combined.shape[1] >= MIN_COLUMNS_COMBINED else WARN, f"{combined.shape[1]} columns")

dupes = int(combined.duplicated().sum())
log("Combined", "No duplicate rows in combined dataset", PASS if dupes == 0 else WARN, f"{dupes} duplicates")

critical_combined = [
    "Player Name", "Team Initials", "MatchID", "RoundID",
    "Home Team Name", "Away Team Name", "Home Team Goals", "Away Team Goals",
    "Year", "Winner", "Country",
]
for col in critical_combined:
    present = col in combined.columns
    log("Combined", f"Column '{col}' present", PASS if present else WARN, "Found" if present else "Missing")

print("\n  [INFO] Missing value % in combined (top columns):")
miss = (combined.isna().sum() / len(combined) * 100).sort_values(ascending=False)
for col, pct in miss[miss > 0].head(15).items():
    flag = "⚠️ " if pct > 20 else "  "
    print(f"    {flag}{col}: {pct:.1f}%")

for col in ["Home Team Goals", "Away Team Goals"]:
    if col in combined.columns:
        neg = int((pd.to_numeric(combined[col], errors="coerce") < 0).sum())
        log("Combined", f"{col} >= 0 in combined", PASS if neg == 0 else FAIL, f"{neg} negative")

year_col_combined = year_col if year_col in combined.columns else "Year"
if year_col_combined in combined.columns:
    yr = pd.to_numeric(combined[year_col_combined], errors="coerce")
    bad_yr = int((~yr.between(1930, 2030)).sum())
    log("Combined", "Year in [1930–2030]", PASS if bad_yr == 0 else FAIL, f"{bad_yr} out-of-range")

section_header("SECTION 6 — EXPORT COMBINED CSV")
try:
    OUTPUT_COMBINED_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_COMBINED_CSV, index=False, encoding="utf-8")
    size_kb = os.path.getsize(OUTPUT_COMBINED_CSV) / 1024
    log("Export", f"Save {OUTPUT_COMBINED_CSV}", PASS, f"{len(combined):,} rows × {combined.shape[1]} cols ({size_kb:.1f} KB)")
except Exception as e:
    log("Export", f"Save {OUTPUT_COMBINED_CSV}", FAIL, str(e))

section_header("SECTION 7 — READINESS SCORE SUMMARY")

total = len(results)
passed = sum(1 for r in results if "PASS" in r[2])
warned = sum(1 for r in results if "WARN" in r[2])
failed = sum(1 for r in results if "FAIL" in r[2])
score = round((passed / total) * 100, 1) if total else 0

print(f"""
  Total Checks  : {total}
  ✅ PASSED     : {passed}
  ⚠️  WARNINGS   : {warned}
  ❌ FAILED     : {failed}

  🏆 READINESS SCORE : {score}%
""")

if failed > 0:
    print("  ❌ FAILED CHECKS:")
    for r in results:
        if "FAIL" in r[2]:
            print(f"     → [{r[0]}] {r[1]}: {r[3]}")

if score >= 90:
    verdict = "🟢 READY FOR ANALYSIS — combined CSV exported successfully"
elif score >= 70:
    verdict = "🟡 MOSTLY READY — review warnings before starting analysis"
else:
    verdict = "🔴 NOT READY — fix FAILED checks before analysis"

print(f"  VERDICT: {verdict}")
print("\n" + "=" * 65)
print("  TEST SUITE v2.0 COMPLETE")
print("=" * 65 + "\n")
