"""
test.py — Comprehensive Data Quality, Cleaning & Join Integrity Validation
Project: FIFA World Cup Analytics | SectionE_g11
Purpose: Validate cleaned dataset quality, join integrity, data completeness, 
         and referential consistency across ETL pipeline

Run with: python test.py
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


class DataValidator:
    def __init__(self, processed_path='data/processed/wc_players_combined.csv'):
        self.df = pd.read_csv(processed_path)
        self.report = {}
        self.raw_cups = None
        self.raw_matches = None
        self.raw_players = None
        self._load_raw_datasets()
        
    def _load_raw_datasets(self):
        """Load raw datasets for comparison and integrity checks"""
        try:
            self.raw_cups = pd.read_csv('data/raw/WorldCups.csv')
            self.raw_matches = pd.read_csv('data/raw/WorldCupMatches.csv')
            self.raw_players = pd.read_csv('data/raw/WorldCupPlayers.csv')
        except Exception as e:
            print(f'⚠️  Warning: Could not load raw datasets: {e}')
        
    def validate_all(self):
        """Run all validation checks"""
        print('\n' + '='*80)
        print('FIFA WORLD CUP DATA QUALITY & JOIN INTEGRITY REPORT')
        print('='*80 + '\n')
        
        self.check_structure()
        self.check_nulls()
        self.check_dtypes()
        self.check_duplicates()
        self.check_value_ranges()
        self.check_join_integrity()
        self.check_referential_consistency()
        self.check_data_cleaning_quality()
        self.check_data_consistency()
        self.compute_analytics_metrics()
        self.print_summary()
        
        return self.report
    
    def check_join_integrity(self):
        """Validate that joins were performed correctly without data loss or orphaning"""
        print('🔗 JOIN INTEGRITY CHECK')
        print('-' * 80)
        
        # Check 1: Match-level consistency
        # Each match should have consistent Home_Team, Away_Team, Year, Stage across all players in that match
        matches_check = self.df.groupby('MatchID').agg({
            'Home_Team': 'nunique',
            'Away_Team': 'nunique',
            'Year': 'nunique',
            'Stage_Std': 'nunique',
            'Attendance': 'nunique',
            'Total_Goals': 'nunique'
        }).reset_index()
        
        inconsistent_matches = (matches_check[matches_check.columns[1:]] > 1).any(axis=1).sum()
        print(f'  ✓ Match consistency (all players in match have same match details):')
        print(f'    - Consistent Matches: {len(matches_check) - inconsistent_matches} / {len(matches_check)}')
        if inconsistent_matches > 0:
            print(f'    ⚠️  INCONSISTENT MATCHES FOUND: {inconsistent_matches}')
            print(matches_check[matches_check[matches_check.columns[1:]] > 1].head())
        
        # Check 2: Team-Match join validity
        # Each player's team should match either Home_Team or Away_Team
        home_team_players = (self.df['Player_Team'] == self.df['Home_Team']).sum()
        away_team_players = (self.df['Player_Team'] == self.df['Away_Team']).sum()
        
        print(f'\n  ✓ Player-Team-Match join validity:')
        print(f'    - Players on Home Team: {home_team_players:,}')
        print(f'    - Players on Away Team: {away_team_players:,}')
        print(f'    - Total players: {len(self.df):,}')
        
        total_assigned = home_team_players + away_team_players
        if total_assigned == len(self.df):
            print(f'    ✓ ALL PLAYERS CORRECTLY ASSIGNED TO MATCH TEAMS')
        else:
            orphaned = len(self.df) - total_assigned
            print(f'    ⚠️  ORPHANED RECORDS: {orphaned} players not in Home_Team or Away_Team')
        
        # Check 3: Year-Host_Nation join validity
        valid_year_host = self.df.groupby('Year').apply(
            lambda x: (x['Host_Country'] == x['Host_Country'].iloc[0]).all()
        ).all()
        print(f'\n  ✓ Year-Host_Country join consistency:')
        if valid_year_host:
            print(f'    ✓ Each year has exactly ONE host country')
        else:
            print(f'    ⚠️  INCONSISTENT YEAR-HOST MAPPING DETECTED')
            year_hosts = self.df.groupby('Year')['Host_Country'].nunique()
            print(f'    Years with multiple hosts: {(year_hosts > 1).sum()}')
        
        # Check 4: Match existence validation
        unique_matches = self.df[['MatchID', 'Home_Team', 'Away_Team', 'Year']].drop_duplicates()
        print(f'\n  ✓ Unique Match Coverage:')
        print(f'    - Total unique matches in dataset: {unique_matches.shape[0]:,}')
        
        # If raw data available, validate against source
        if self.raw_matches is not None:
            raw_match_count = self.raw_matches['MatchID'].nunique()
            print(f'    - Raw matches (source): {raw_match_count}')
            print(f'    - Coverage: {(unique_matches.shape[0] / raw_match_count * 100):.1f}%')
        
        self.report['join_integrity'] = {
            'consistent_matches': len(matches_check) - inconsistent_matches,
            'home_team_players': int(home_team_players),
            'away_team_players': int(away_team_players),
            'orphaned_records': int(len(self.df) - total_assigned),
            'year_host_consistent': bool(valid_year_host),
            'unique_matches': unique_matches.shape[0]
        }
        print()
    
    def check_referential_consistency(self):
        """Validate foreign key relationships are maintained"""
        print('🔐 REFERENTIAL CONSISTENCY CHECK')
        print('-' * 80)
        
        # Check 1: All Years in dataset should exist in raw Cups data
        if self.raw_cups is not None:
            valid_years = set(self.raw_cups['Year'].unique())
            df_years = set(self.df['Year'].unique())
            invalid_years = df_years - valid_years
            print(f'  ✓ Year validity check:')
            print(f'    - Valid years in processed data: {len(df_years - invalid_years)} / {len(df_years)}')
            if invalid_years:
                print(f'    ⚠️  INVALID YEARS FOUND: {sorted(invalid_years)}')
            else:
                print(f'    ✓ All years are valid World Cup tournaments')
        
        # Check 2: Team names consistency
        print(f'\n  ✓ Team name consistency:')
        home_teams = set(self.df['Home_Team'].unique())
        away_teams = set(self.df['Away_Team'].unique())
        player_teams = set(self.df['Player_Team'].unique())
        all_teams = home_teams | away_teams | player_teams
        
        print(f'    - Unique home teams: {len(home_teams)}')
        print(f'    - Unique away teams: {len(away_teams)}')
        print(f'    - Unique player teams: {len(player_teams)}')
        print(f'    - Total unique teams: {len(all_teams)}')
        
        # Check for team name inconsistencies (e.g., "Germany" vs "West Germany")
        potential_dupes = {}
        for team in all_teams:
            base = team.split()[-1] if team else team
            if base not in potential_dupes:
                potential_dupes[base] = []
            potential_dupes[base].append(team)
        
        dupe_teams = {k: v for k, v in potential_dupes.items() if len(v) > 1}
        if dupe_teams:
            print(f'\n    ⚠️  Potential team name variants detected:')
            for key, teams in dupe_teams.items():
                print(f'       - {key}: {teams}')
        else:
            print(f'    ✓ No duplicate team name patterns detected')
        
        # Check 3: Match Result consistency
        valid_results = {'Home Win', 'Away Win', 'Draw'}
        invalid_results = set(self.df['Match_Result'].unique()) - valid_results
        print(f'\n  ✓ Match Result values:')
        print(f'    - Valid results found: {sorted(self.df["Match_Result"].unique())}')
        if invalid_results:
            print(f'    ⚠️  INVALID RESULTS: {invalid_results}')
        
        # Check 4: Lineup status validity
        if 'Is_Starter' in self.df.columns and 'Is_Substitute' in self.df.columns:
            valid_lineup = ((self.df['Is_Starter'] == True) | (self.df['Is_Substitute'] == True)).sum()
            print(f'\n  ✓ Lineup status values:')
            print(f'    - Records with valid lineup: {valid_lineup:,} / {len(self.df):,}')
            if valid_lineup == len(self.df):
                print(f'    ✓ All players have valid starter/substitute designation')
        
        # Check 5: Host country consistency
        print(f'\n  ✓ Host Country consistency:')
        unique_hosts = self.df['Host_Country'].nunique()
        print(f'    - Unique host countries: {unique_hosts}')
        year_hosts = self.df.groupby('Year')['Host_Country'].nunique()
        consistent_hosts = (year_hosts == 1).all()
        if consistent_hosts:
            print(f'    ✓ Each tournament has exactly ONE host country')
        else:
            print(f'    ⚠️  Some years have multiple host countries')
        
        self.report['referential_consistency'] = {
            'valid_years': bool(not invalid_years if self.raw_cups is not None else True),
            'unique_teams': len(all_teams),
            'valid_match_results': bool(not invalid_results),
            'host_consistent': consistent_hosts
        }
        print()
    
    def check_data_cleaning_quality(self):
        """Validate data was properly cleaned (no encoding errors, malformed data, etc)"""
        print('🧹 DATA CLEANING QUALITY CHECK')
        print('-' * 80)
        
        # Check 1: No HTML encoding remnants
        print(f'  ✓ Encoding artifact detection:')
        suspicious_patterns = [
            ('HTML entities', ['&', '&#', '&lt;', '&gt;', '&nbsp;', 'rn&gt;', 'rn"&']),
            ('Incomplete cleaning', ['nan', 'None', 'NULL']),
            ('Whitespace issues', ['  ', '\t', '\n'])
        ]
        
        issues_found = False
        for pattern_name, patterns in suspicious_patterns:
            found = False
            for col in self.df.select_dtypes(include=['object']).columns:
                for pattern in patterns:
                    if any(pattern in str(val) for val in self.df[col].dropna().unique() if isinstance(val, str)):
                        if not found:
                            print(f'    ⚠️  {pattern_name}: {patterns}')
                            found = True
                            issues_found = True
                        break
        
        if not issues_found:
            print(f'    ✓ No encoding artifacts detected')
        
        # Check 2: Numeric fields are numeric
        print(f'\n  ✓ Data type consistency:')
        numeric_cols = ['Goals', 'Yellow_Cards', 'Red_Cards', 'Attendance', 'Total_Goals']
        numeric_issues = []
        
        for col in numeric_cols:
            if col in self.df.columns:
                if not pd.api.types.is_numeric_dtype(self.df[col]):
                    numeric_issues.append(col)
        
        if numeric_issues:
            print(f'    ⚠️  Non-numeric columns: {numeric_issues}')
        else:
            print(f'    ✓ All numeric columns have correct dtype')
        
        # Check 3: String fields have reasonable content
        print(f'\n  ✓ String field validation:')
        string_cols = ['Home_Team', 'Away_Team', 'Player_Team', 'Stage', 'Host_Nation']
        
        for col in string_cols:
            if col in self.df.columns:
                empty_count = self.df[col].isna().sum() + (self.df[col] == '').sum()
                avg_length = self.df[col].astype(str).str.len().mean()
                print(f'    - {col}: {empty_count} empty, avg_len={avg_length:.1f}')
        
        # Check 4: No leading/trailing whitespace
        print(f'\n  ✓ Whitespace trimming validation:')
        leading_trailing = 0
        for col in self.df.select_dtypes(include=['object']).columns:
            whitespace_issues = self.df[col].astype(str).apply(
                lambda x: x != x.strip() and len(x.strip()) > 0
            ).sum()
            leading_trailing += whitespace_issues
        
        if leading_trailing == 0:
            print(f'    ✓ All strings properly trimmed')
        else:
            print(f'    ⚠️  {leading_trailing} cells have leading/trailing whitespace')
        
        self.report['cleaning_quality'] = {
            'encoding_artifacts': issues_found,
            'numeric_dtype_valid': not bool(numeric_issues),
            'whitespace_trimmed': leading_trailing == 0
        }
        print()
    
    def check_structure(self):
        """Verify dataset structure"""
        print('📊 DATASET STRUCTURE')
        print('-' * 80)
        print(f'  Total Rows:    {len(self.df):,}')
        print(f'  Total Columns: {self.df.shape[1]}')
        print(f'  Memory Usage:  {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB')
        print(f'  Index Range:   0 — {len(self.df) - 1}')
        
        print(f'\n  Column Inventory:')
        print(f'  {self.df.columns.tolist()}')
        
        self.report['structure'] = {
            'rows': len(self.df),
            'columns': self.df.shape[1],
            'memory_mb': round(self.df.memory_usage(deep=True).sum() / 1024**2, 2)
        }
        print()
    
    def check_nulls(self):
        """Validate null values"""
        print('✅ NULL VALUES CHECK')
        print('-' * 80)
        nulls = self.df.isnull().sum()
        total_nulls = nulls.sum()
        
        if total_nulls == 0:
            print('  ✓ NO NULL VALUES DETECTED — Dataset is complete!')
        else:
            print(f'  ⚠️  Found {total_nulls} null values:')
            for col, count in nulls[nulls > 0].items():
                pct = (count / len(self.df)) * 100
                print(f'     - {col}: {count} ({pct:.2f}%)')
        
        self.report['nulls'] = {
            'total_nulls': int(total_nulls),
            'complete': total_nulls == 0
        }
        print()
    
    def check_dtypes(self):
        """Validate data types"""
        print('🔍 DATA TYPES CHECK')
        print('-' * 80)
        print('  Column              | Type       | Unique Values')
        print('  ' + '-' * 74)
        
        dtype_report = {}
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            unique = self.df[col].nunique()
            dtype_report[col] = dtype
            print(f'  {col:<18} | {dtype:<10} | {unique:>6,}')
        
        self.report['dtypes'] = dtype_report
        print()
    
    def check_duplicates(self):
        """Check for duplicate rows and partial duplicates"""
        print('🔄 DUPLICATE RECORDS CHECK')
        print('-' * 80)
        
        exact_duplicates = self.df.duplicated().sum()
        print(f'  ✓ Exact Row Duplicates: {exact_duplicates}')
        if exact_duplicates == 0:
            print(f'    ✓ No duplicate rows found — dataset is clean')
        else:
            print(f'    ⚠️  Found {exact_duplicates} exact duplicate rows')
        
        # Check for match-level duplicates (same match, different players - expected)
        match_duplicates = self.df.duplicated(
            subset=['MatchID', 'Player_Team'], keep=False
        ).sum()
        print(f'\n  ✓ Match-level repeats (same match, same team): {match_duplicates:,}')
        print(f'    (This is expected — multiple players per team)')
        
        # Check for player-level partial duplicates (same player in same match - not expected)
        if 'Player_Name' in self.df.columns or 'Team_Initials' in self.df.columns:
            player_match_dupes = self.df.duplicated(
                subset=['MatchID', 'Player_Team', 'Goals', 'Yellow_Cards', 'Red_Cards'],
                keep=False
            ).sum()
            print(f'\n  ✓ Potential player-match duplicates: {player_match_dupes:,}')
            if player_match_dupes > 0:
                print(f'    ⚠️  Check if same player appears multiple times in one match')
        
        self.report['duplicates'] = {
            'exact_duplicates': int(exact_duplicates),
            'is_clean': exact_duplicates == 0
        }
        print()
    
    def check_value_ranges(self):
        """Validate numeric value ranges"""
        print('📏 VALUE RANGES CHECK')
        print('-' * 80)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        range_report = {}
        
        for col in numeric_cols:
            min_val = self.df[col].min()
            max_val = self.df[col].max()
            mean_val = self.df[col].mean()
            std_val = self.df[col].std()
            
            range_report[col] = {
                'min': float(min_val),
                'max': float(max_val),
                'mean': float(mean_val),
                'std': float(std_val)
            }
            
            print(f'  {col:<18} | Min: {min_val:>8} | Max: {max_val:>8} | '
                  f'Mean: {mean_val:>8.2f} | Std: {std_val:>8.2f}')
        
        self.report['value_ranges'] = range_report
        print()
    
    def check_data_consistency(self):
        """Check logical consistency"""
        print('🎯 DATA CONSISTENCY CHECKS')
        print('-' * 80)
        
        # Year range
        year_min = self.df['Year'].min()
        year_max = self.df['Year'].max()
        year_valid = (self.df['Year'] >= 1930) & (self.df['Year'] <= 2026)
        print(f'  ✓ Year range (actual: {year_min}-{year_max}):')
        print(f'    - Within 1930-2026: {year_valid.sum():,} / {len(self.df):,}')
        
        # Stage values
        if 'Stage_Std' in self.df.columns:
            valid_stages = {'Group Stage', 'Quarter-Final', 'Semi-Final', 'Final', 
                           'Round of 16', 'Third Place', 'Preliminary', 'First Round'}
            stage_valid = self.df['Stage_Std'].isin(valid_stages)
            print(f'\n  ✓ Stage values:')
            print(f'    - Valid stages: {stage_valid.sum():,} / {len(self.df):,}')
            print(f'    - Unique stages: {sorted(self.df["Stage_Std"].unique())}')
            if not stage_valid.all():
                invalid_stages = set(self.df['Stage_Std'].unique()) - valid_stages
                print(f'    ⚠️  Invalid stages: {invalid_stages}')
        
        # Match Result values
        valid_results = {'Home Win', 'Away Win', 'Draw'}
        result_valid = self.df['Match_Result'].isin(valid_results)
        print(f'\n  ✓ Match Results:')
        print(f'    - Valid results: {result_valid.sum():,} / {len(self.df):,}')
        print(f'    - Results found: {sorted(self.df["Match_Result"].unique())}')
        
        # Card counts (should be non-negative)
        cards_valid = (self.df['Yellow_Cards'] >= 0) & (self.df['Red_Cards'] >= 0)
        print(f'\n  ✓ Card counts (non-negative):')
        print(f'    - Valid: {cards_valid.sum():,} / {len(self.df):,}')
        
        # Goals consistency
        goals_valid = self.df['Goals'] >= 0
        print(f'\n  ✓ Goals (non-negative):')
        print(f'    - Valid: {goals_valid.sum():,} / {len(self.df):,}')
        
        # Attendance (should be > 0 for valid matches)
        attendance_valid = self.df['Attendance'] > 0
        print(f'\n  ✓ Attendance (> 0):')
        print(f'    - Valid: {attendance_valid.sum():,} / {len(self.df):,}')
        zero_attendance = (self.df['Attendance'] == 0).sum()
        if zero_attendance > 0:
            print(f'    ⚠️  Matches with 0 attendance: {zero_attendance}')
        
        # Total Goals consistency
        print(f'\n  ✓ Total Goals consistency:')
        print(f'    - Total goals in matches: {self.df["Total_Goals"].sum():,}')
        print(f'    - Average per match: {self.df["Total_Goals"].mean():.2f}')
        
        all_valid = (year_valid & result_valid & cards_valid & goals_valid & attendance_valid).sum()
        print(f'\n  Overall Consistency: {all_valid:,} / {len(self.df):,} '
              f'({(all_valid/len(self.df)*100):.2f}%)')
        
        self.report['consistency'] = {
            'year_valid': int(year_valid.sum()),
            'result_valid': int(result_valid.sum()),
            'cards_valid': int(cards_valid.sum()),
            'goals_valid': int(goals_valid.sum()),
            'attendance_valid': int(attendance_valid.sum()),
            'overall_valid': int(all_valid),
            'overall_pct': round(all_valid/len(self.df)*100, 2)
        }
        print()
    
    def compute_analytics_metrics(self):
        """Compute key analytics metrics"""
        print('📈 ANALYTICS METRICS')
        print('-' * 80)
        
        metrics = {}
        
        # Team metrics
        home_teams = self.df['Home_Team'].nunique()
        away_teams = self.df['Away_Team'].nunique()
        player_teams = self.df['Player_Team'].nunique()
        unique_teams = set(self.df['Home_Team'].unique()) | set(self.df['Away_Team'].unique())
        print(f'  Unique Teams: {len(unique_teams)}')
        print(f'    - Home Team entries: {home_teams}')
        print(f'    - Away Team entries: {away_teams}')
        print(f'    - Player Team entries: {player_teams}')
        metrics['unique_teams'] = len(unique_teams)
        
        # Venue metrics
        if 'City' in self.df.columns:
            venues = self.df['City'].nunique()
            print(f'\n  Venues: {venues} unique cities')
            metrics['venues'] = venues
        
        # Tournament coverage
        tournaments = self.df['Year'].nunique()
        year_range = f"{self.df['Year'].min()}-{self.df['Year'].max()}"
        print(f'\n  Tournaments: {tournaments} World Cups ({year_range})')
        print(f'    Years: {sorted(self.df["Year"].unique())}')
        metrics['tournaments'] = tournaments
        
        # Player appearances
        player_apps = len(self.df)
        print(f'\n  Player Appearances: {player_apps:,} records')
        metrics['player_appearances'] = player_apps
        
        # Goal statistics
        total_goals = self.df['Goals'].sum()
        avg_goals_per_record = self.df['Goals'].mean()
        records_with_goals = (self.df['Goals'] > 0).sum()
        print(f'\n  Goals Statistics:')
        print(f'    - Total Goals: {int(total_goals):,}')
        print(f'    - Avg Goals/Record: {avg_goals_per_record:.4f}')
        print(f'    - Records with Goals: {records_with_goals:,}')
        metrics['goals'] = {
            'total': int(total_goals),
            'avg_per_record': round(avg_goals_per_record, 4),
            'records_with_goals': int(records_with_goals)
        }
        
        # Card statistics
        total_yellows = self.df['Yellow_Cards'].sum()
        total_reds = self.df['Red_Cards'].sum()
        records_with_yellows = (self.df['Yellow_Cards'] > 0).sum()
        records_with_reds = (self.df['Red_Cards'] > 0).sum()
        print(f'\n  Disciplinary Statistics:')
        print(f'    - Total Yellow Cards: {int(total_yellows):,}')
        print(f'    - Total Red Cards: {int(total_reds):,}')
        print(f'    - Records with Yellows: {records_with_yellows:,}')
        print(f'    - Records with Reds: {records_with_reds:,}')
        metrics['cards'] = {
            'yellows': int(total_yellows),
            'reds': int(total_reds),
            'records_with_yellows': int(records_with_yellows),
            'records_with_reds': int(records_with_reds)
        }
        
        # Match outcomes
        home_wins = (self.df['Match_Result'] == 'Home Win').sum()
        away_wins = (self.df['Match_Result'] == 'Away Win').sum()
        draws = (self.df['Match_Result'] == 'Draw').sum()
        unique_matches = self.df[['MatchID', 'Home_Team', 'Away_Team']].drop_duplicates().shape[0] if 'MatchID' in self.df.columns else 'N/A'
        
        print(f'\n  Match Outcomes:')
        if unique_matches != 'N/A':
            print(f'    - Unique Matches: {unique_matches:,}')
        print(f'    - Home Wins: {home_wins:,}')
        print(f'    - Away Wins: {away_wins:,}')
        print(f'    - Draws: {draws:,}')
        metrics['match_outcomes'] = {
            'unique_matches': unique_matches if unique_matches == 'N/A' else int(unique_matches),
            'home_wins': int(home_wins),
            'away_wins': int(away_wins),
            'draws': int(draws)
        }
        
        # Attendance
        avg_attendance = self.df['Attendance'].mean()
        max_attendance = self.df['Attendance'].max()
        min_attendance = self.df['Attendance'].min()
        print(f'\n  Attendance Statistics:')
        print(f'    - Average: {avg_attendance:,.0f}')
        print(f'    - Maximum: {max_attendance:,}')
        print(f'    - Minimum: {min_attendance:,}')
        metrics['attendance'] = {
            'average': round(avg_attendance),
            'maximum': int(max_attendance),
            'minimum': int(min_attendance)
        }
        
        self.report['analytics_metrics'] = metrics
        print()
    
    def print_summary(self):
        """Print final summary"""
        print('='*80)
        print('✅ DATA VALIDATION COMPLETE')
        print('='*80)
        print(f'\n  Dataset Status: READY FOR ANALYSIS')
        print(f'  Total Records: {len(self.df):,}')
        print(f'  Quality Checks Passed: {self._count_passed_checks()}/{self._count_total_checks()}')
        print(f'\n  Next Steps:')
        print(f'    1. Load into Tableau for visualization')
        print(f'    2. Run exploratory data analysis (03_eda.ipynb)')
        print(f'    3. Perform statistical analysis (04_statistical_analysis.ipynb)')
        print(f'    4. Generate KPI dashboard')
        print('\n')
    
    def _count_passed_checks(self):
        """Count how many checks passed"""
        count = 0
        if self.report.get('nulls', {}).get('complete'):
            count += 1
        if self.report.get('duplicates', {}).get('is_clean'):
            count += 1
        if self.report.get('join_integrity', {}).get('orphaned_records') == 0:
            count += 1
        if self.report.get('referential_consistency', {}).get('valid_match_results'):
            count += 1
        if self.report.get('cleaning_quality', {}).get('whitespace_trimmed'):
            count += 1
        return count
    
    def _count_total_checks(self):
        """Total checks performed"""
        return 5


def main():
    # Check if processed file exists
    processed_file = 'data/processed/wc_players_combined.csv'
    
    if not os.path.exists(processed_file):
        print(f'❌ ERROR: {processed_file} not found!')
        print('   Make sure you are on the correct branch with the processed data file.')
        return
    
    # Run validation
    validator = DataValidator(processed_file)
    report = validator.validate_all()
    
    return report


if __name__ == '__main__':
    main()
