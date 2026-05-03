# ⚽ FIFA World Cup Analytics
### Decoding 84 Years of Football History — 1930 to 2014

> **DVA Capstone 2 · Data Visualization & Analytics · Newton School of Technology**  
> Sector: Sports Analytics · Submitted: May 2026

---

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Tableau](https://img.shields.io/badge/Tableau-Public-E97627?style=flat&logo=tableau&logoColor=white)](https://public.tableau.com)
[![Jupyter](https://img.shields.io/badge/Notebooks-Jupyter-F37626?style=flat&logo=jupyter&logoColor=white)](https://jupyter.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)
[![Dataset](https://img.shields.io/badge/Dataset-Kaggle-20BEFF?style=flat&logo=kaggle&logoColor=white)](https://www.kaggle.com/datasets/abecklas/fifa-world-cup)

---

## 📌 Project Overview

This project is a full end-to-end sports analytics pipeline built on 84 years of FIFA World Cup data — spanning 20 editions, 836 matches, 83 nations, and 7,638 players from 1930 to 2014.

Three raw Kaggle datasets were merged, cleaned, and transformed using a Python ETL pipeline into a single 36,595-row master dataset and four KPI tables. The final output is an interactive three-dashboard Tableau Public workbook with insights and recommendations for FIFA, national federations, broadcasters, and host nations.

**Business Problem:**
> Despite 84 years of competition data, there is no quantified understanding of how tournament era, match stage, home advantage, and player efficiency collectively drive match outcomes and commercial performance — leaving FIFA, national federations, and host nations making high-stakes decisions on squad selection, scheduling, and venue strategy without historical evidence.

---

## 🔗 Quick Links

| Asset | Link |
|---|---|
| 📊 Tableau Dashboard | [View on Tableau Public](#) ← *Insert URL after publishing* |
| 📄 Project Report | `reports/project_report.pdf` |
| 📽️ Presentation Deck | `reports/presentation.pdf` |
| 📚 Data Dictionary | [`docs/data_dictionary.md`](docs/data_dictionary.md) |
| 🗃️ Raw Dataset | [Kaggle — abecklas/fifa-world-cup](https://www.kaggle.com/datasets/abecklas/fifa-world-cup) |

---

## 🗂️ Repository Structure

```
FIFA_WorldCup_Analytics/
│
├── README.md                          ← You are here
│
├── data/
│   ├── raw/                           ← Original, unedited source files
│   │   ├── WorldCupMatches.csv        │  836 real matches (4,572 raw rows)
│   │   ├── WorldCupPlayers.csv        │  37,784 player-match records
│   │   └── WorldCups.csv              │  20 tournament editions
│   │
│   └── processed/                     ← Output of the ETL pipeline
│       ├── world_cup_master.csv        │  Master dataset (36,595 × 37)
│       ├── kpi_tournament.csv          │  Tournament-level KPIs (20 × 15)
│       ├── kpi_team.csv               │  All-time team performance (83 × 12)
│       ├── kpi_player.csv             │  Player career records (7,638 × 14)
│       └── kpi_match.csv              │  Match analytics (836 × 35)
│
├── notebooks/
│   ├── 01_extraction.ipynb            ← Load raw CSVs, validate, checksum
│   ├── 02_cleaning.ipynb              ← 15-step cleaning pipeline
│   ├── 03_eda.ipynb                   ← Exploratory data analysis
│   ├── 04_statistical_analysis.ipynb  ← Hypothesis testing & regression
│   └── 05_final_load_prep.ipynb       ← KPI computation & export
│
├── scripts/
│   └── etl_pipeline.py                ← Standalone reproducible ETL script
│
├── tableau/
│   ├── screenshots/                   ← Dashboard screenshots (PNG)
│   │   ├── dashboard_01_executive.png
│   │   ├── dashboard_02_match.png
│   │   └── dashboard_03_player_team.png
│   └── dashboard_links.md             ← Tableau Public URL
│
├── reports/
│   ├── project_report.pdf             ← Final project report (10-12 pages)
│   └── presentation.pdf              ← Presentation deck (11 slides)
│
└── docs/
    └── data_dictionary.md             ← Full column definitions for all files
```

---

## 📦 Dataset

| File | Rows | Columns | Grain |
|---|---|---|---|
| `WorldCupMatches.csv` | 836 (real) | 20 | One row per match |
| `WorldCupPlayers.csv` | 37,784 | 9 | One row per player per match |
| `WorldCups.csv` | 20 | 10 | One row per tournament edition |
| `world_cup_master.csv` *(processed)* | 36,595 | 37 | Player × Match × Tournament |
| `kpi_tournament.csv` *(processed)* | 20 | 15 | One row per tournament |
| `kpi_team.csv` *(processed)* | 83 | 12 | One row per nation (all-time) |
| `kpi_player.csv` *(processed)* | 7,638 | 14 | One row per player (all-time) |
| `kpi_match.csv` *(processed)* | 836 | 35 | One row per match |

**Source:** [Kaggle — FIFA World Cup Dataset by abecklas](https://www.kaggle.com/datasets/abecklas/fifa-world-cup)  
**Coverage:** 1930 – 2014 · 20 editions · 83 nations · 7,638 players · 836 matches

> ⚠️ The files in `data/raw/` are **never modified** after download. All transformations happen in `notebooks/02_cleaning.ipynb` and output to `data/processed/`.

---

## 🔧 ETL Pipeline

All cleaning and transformation was done in Python across 5 Jupyter Notebooks and consolidated in `scripts/etl_pipeline.py`.

### Merge Logic

```
WorldCupPlayers  (37,784 rows)
    └── LEFT JOIN WorldCupMatches   ON  RoundID + MatchID
            └── LEFT JOIN WorldCups  ON  Year
                    └──▶  world_cup_master.csv  (36,595 rows × 37 cols)
```

*736 duplicate rows removed + 454 NaT datetime rows dropped = 36,595 final rows.*

### Key Cleaning Steps

| Step | Issue | Fix Applied |
|---|---|---|
| 1 | 3,720 fully blank rows in `WorldCupMatches` | `dropna(how='all')` |
| 2 | 736 duplicate rows in merged dataset | `drop_duplicates()` |
| 3 | Column names with mixed case and spaces | Renamed to `snake_case` |
| 4 | `datetime` stored as plain string | `pd.to_datetime(format='%d %b %Y - %H:%M')` |
| 5 | Goals and attendance stored as `float` | Cast to `int` after blank row removal |
| 6 | `attendance` — 2 missing values | Filled with year-level median |
| 7 | `win_conditions` — empty string for normal results | Replaced with `'Normal'` |
| 8 | `shirt_number` — value `0` used as unknown | Replaced `0` with `NaN` |
| 9 | `position` — 33,641 nulls (pre-1980s unrecorded) | `fillna('Unknown')` |
| 10 | `event` — 28,715 nulls (no action recorded) | `fillna('No Event')` |
| 11 | `line_up` — opaque codes `S` / `N` | Mapped to `Starting` / `Substitute` |
| 12 | `tournament_attendance` — dot-thousands string format | Removed `.`, cast to `int` |
| 13 | Leading/trailing whitespace in all string columns | `.str.strip()` on all object columns |
| 14 | Missing derived analytical columns | Added `total_goals`, `win_type`, `is_home_win`, `is_knockout`, `era` and more |

### Feature Engineering

New columns created during the pipeline:

- `total_goals` = `home_team_goals + away_team_goals`
- `ht_goals` = `half_time_home_goals + half_time_away_goals`
- `second_half_goals` = `total_goals - ht_goals`
- `goal_margin` = `abs(home_team_goals - away_team_goals)`
- `win_type` = `Normal` / `Extra Time` / `Penalties` (parsed from `win_conditions`)
- `is_home_win`, `is_away_win`, `is_draw` (binary flags from goal comparison)
- `is_high_scoring` = `1` if `total_goals >= 4`
- `is_goalless` = `1` if `total_goals == 0`
- `is_knockout` = `1` if match stage is a knockout round
- `era` = `Classic Era (≤16 teams)` / `Expansion Era (24 teams)` / `Modern Era (32 teams)`

---

## 📊 KPI Framework

Four KPI tables were computed in `notebooks/05_final_load_prep.ipynb`:

### KPI_Tournament — *Tournament-Level Performance*
`avg_goals_per_match`, `avg_attendance_per_match`, `host_nation_won`, `goals_per_team`, `era`

### KPI_Team — *All-Time National Team Rankings*
`win_rate_pct`, `goal_difference`, `goals_per_match`, `titles_won`, `tournament_appearances`

### KPI_Player — *Player Career Records*
`goals_per_appearance`, `career_span_years`, `starts`, `sub_appearances`, `tournaments_attended`

### KPI_Match — *Match-Level Analytics*
`is_home_win`, `is_knockout`, `is_high_scoring`, `is_goalless`, `win_type`, `goal_margin`, `second_half_goals`

---

## 🔬 Statistical Analysis

All tests in `notebooks/04_statistical_analysis.ipynb` using `scipy` and `statsmodels`:

| Test | Question | Result | Key Numbers |
|---|---|---|---|
| **Linear Regression** | Are goals/match declining over time? | ✅ Confirmed | slope = −0.0267/yr, R² = 0.61, p < 0.001 |
| **One-Sample t-Test** | Does home advantage actually exist? | ✅ Confirmed | 57.51% win rate, t = 4.36, p < 0.001 |
| **Two-Sample t-Test** | Is knockout home advantage stronger? | ✅ Confirmed | 65.45% vs 55.12%, t = 2.54, p = 0.011 |
| **Chi-Squared Test** | Does era affect how matches are decided? | ✅ Confirmed | χ² = 15.917, dof = 4, p = 0.003 |
| **Pearson Correlation** | Do high-scoring matches draw bigger crowds? | ⚠️ Negative | r = −0.116, p < 0.001 *(capacity drives crowds, not goals)* |
| **Shapiro-Wilk Test** | Are goals normally distributed? | ❌ Non-normal | W = 0.9243, skew = 0.969, p < 0.0001 |

---

## 📈 Tableau Dashboards

Three interactive dashboards published on Tableau Public:

### Dashboard 1 — Executive Overview
**Audience:** FIFA leadership, tournament directors  
**KPIs:** Tournaments (19), Total Goals (2,208), Matches (772), Avg Goals/Match (2.860)  
**Charts:** Goals/match trend · Tournament attendance · Top 15 teams by wins · Win rate scatter  
**Filters:** Era, Year slider, Titles Won

### Dashboard 2 — Match Analytics
**Audience:** Match analysts, broadcast scheduling teams  
**KPIs:** Home Win (58.66%), Away Win (18.90%), Draw Rate (22.44%), Goalless Rate (8.27%)  
**Charts:** Match outcome pie · Goals distribution · Avg goals by stage · Attendance scatter  
**Filters:** Win Type, Stage, Era, Is Knockout, Year range

### Dashboard 3 — Player & Team Deep Dive
**Audience:** Coaches, scouts, federation analytics teams  
**KPIs:** Most Goals (16 — Klose), Most Appearances (32 — Ronaldo), Total Players (7,638), Players Scored (1,177)  
**Charts:** Top 15 scorers · Team goal difference · Discipline cards · Appearances vs Goals quadrant  
**Filters:** Team selector, Tournaments Attended, Goal Difference Label

🔗 **Tableau Public URL:** [Insert published dashboard URL here]

---

## 💡 Key Insights

1. **Goals are in structural decline** — each decade produces 0.27 fewer goals per match (R² = 0.61). This is driven by tactical evolution, not formatting — FIFA cannot reverse it without rule changes.

2. **USA 1994 set the commercial benchmark** — 68,991 average attendance per match, 38.9% above the post-1994 median. No host in 30 years has recovered this level. Driven entirely by stadium capacity strategy.

3. **Home advantage is statistically real** — 57.51% win rate overall, rising to 65.45% in knockout rounds (+10pp). Confirmed via t-test (p < 0.001). Away-designated teams face a measurable structural disadvantage.

4. **Brazil dominates every all-time metric simultaneously** — 5 titles, 67% win rate, +118 goal difference, 20 consecutive appearances. No other nation achieves this combination.

5. **Germany's record is analytically split** — Germany FR (1954–1986, 3 titles) and Germany (1990–2014, 1 title) are the same footballing nation separated by reunification. Combined: 4 titles and the strongest win rate among major nations.

6. **84.6% of World Cup players never scored** — goal-scoring is a rare, elite skill concentrated in a small group of specialist forwards. Only 210 of 7,638 players achieved a goals-per-appearance ratio of ≥0.5.

7. **Penalty shootouts are a modern phenomenon** — zero in the Classic Era, now deciding 3.1% of all knockout matches. They introduce randomness into the tournament's highest-stakes games.

8. **Attendance is NOT driven by goal output** — the Pearson correlation between attendance and total goals is negative (r = −0.116). Stadium capacity and host prestige drive crowds, not how exciting the match is expected to be.

---

## 🎯 Recommendations

| # | Recommendation | For | Expected Impact |
|---|---|---|---|
| R1 | Use KPI_Tournament era analysis to model scoring risk for the 2026 48-team format before finalising scheduling | FIFA | Avoid lowest-ever goal output in WC history at current 2.49 goals/match avg |
| R2 | Adopt goals-per-appearance ≥ 0.5 (weighted by minutes) as the primary forward selection KPI | Federations | 2–3 extra goals per tournament → 1–2 additional knockout wins per edition |
| R3 | Apply KPI_Tournament attendance model to evaluate 2030/2034 host bids against USA 1994 benchmark | FIFA & Hosts | Est. USD 150–200M incremental ticket revenue if the 38.9% attendance gap is closed |
| R4 | Integrate KPI_Match home advantage data into knockout tactical briefs for away-designated matches | Federations | Reducing the 10pp away penalty to 5pp → 1 extra win per 20 knockout matches |

---

## ⚙️ How to Run

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn scipy statsmodels jupyter
```

### Run the full pipeline

```bash
# Clone the repository
git clone https://github.com/[your-username]/FIFA_WorldCup_Analytics.git
cd FIFA_WorldCup_Analytics

# Run the full ETL pipeline (extraction → cleaning → KPI output)
python scripts/etl_pipeline.py

# Or run notebooks step by step
jupyter notebook notebooks/01_extraction.ipynb
jupyter notebook notebooks/02_cleaning.ipynb
jupyter notebook notebooks/03_eda.ipynb
jupyter notebook notebooks/04_statistical_analysis.ipynb
jupyter notebook notebooks/05_final_load_prep.ipynb
```

### Expected output

Running `etl_pipeline.py` will produce all five files in `data/processed/`:
- `world_cup_master.csv`
- `kpi_tournament.csv`
- `kpi_team.csv`
- `kpi_player.csv`
- `kpi_match.csv`

---

## ⚠️ Known Limitations

| # | Limitation | Impact |
|---|---|---|
| 1 | Dataset ends at 2014 — excludes 2018 and 2022 | Post-2014 trends may differ from historical patterns |
| 2 | Position data missing for 89% of players (pre-1982) | Position-based analysis restricted to modern era only |
| 3 | Germany FR and Germany treated as separate entities | Combined German all-time totals are analytically understated |
| 4 | Attendance missing for 2 matches — filled with year median | Minor distortion in match-level attendance statistics |
| 5 | No in-match tactical data (passes, shots, xG) | Analysis is outcome-based; causal claims cannot be made |
| 6 | Correlation ≠ causation | All patterns are observational, not causal |

---

## 🚀 Future Scope

- **Expand to 2018 & 2022** — validate whether modern-era trends hold post-2014
- **Integrate Opta/StatsBomb data** — add xG, passes, pressures for process-level analysis
- **Build a match outcome predictor** — logistic regression using team, stage, era, home advantage
- **Attendance forecasting model** — time-series using host GDP, team popularity, and stage importance
- **Real-time Tableau dashboard** — live tournament benchmarking against historical KPIs

---

## 👤 Team & Contributions

| Member | Role | Contributions |
|---|---|---|
| **Ashish Kumar Yadav** | Project Lead | Dataset sourcing, ETL pipeline, EDA, statistical analysis, Tableau dashboards, report, presentation |
| [Member 2] | Data Lead | Dataset sourcing, data dictionary |
| [Member 3] | ETL Lead | Notebooks 01 & 02 — extraction and cleaning |
| [Member 4] | Analysis Lead | Notebooks 03 & 04 — EDA and statistical analysis |
| [Member 5] | Visualization Lead | Tableau dashboard design and publishing |
| [Member 6] | Strategy Lead | Problem statement, KPI framework, recommendations |
| [Member 7] | PPT & Quality Lead | Final report, presentation deck, contribution matrix |

> All contributions are verifiable via GitHub Insights, PR history, and committed files.

---

## 📋 Submission Checklist

- [x] Public repository with correct naming convention
- [x] All notebooks committed in `.ipynb` format
- [x] `data/raw/` contains original, unedited datasets
- [x] `data/processed/` contains cleaned master dataset and 4 KPI tables
- [x] `docs/data_dictionary.md` is complete
- [x] `scripts/etl_pipeline.py` is committed and reproducible
- [x] `tableau/screenshots/` contains dashboard screenshots
- [ ] `tableau/dashboard_links.md` contains Tableau Public URL ← *Add after publishing*
- [x] `reports/project_report.pdf` is complete
- [x] `reports/presentation.pdf` is complete
- [x] All members have visible commits and pull requests

---

## 📜 License

This project is submitted as part of the DVA Capstone 2 at Newton School of Technology.  
Dataset credit: [abecklas on Kaggle](https://www.kaggle.com/datasets/abecklas/fifa-world-cup)  
For academic use only.

---

*Last updated: May 2026 · Maintained by: Ashish Kumar Yadav · Newton School of Technology*
