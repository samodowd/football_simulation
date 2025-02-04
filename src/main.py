# Simulation study to determine how often the best team do not win the league

# First we need to simulate a set a number of teams and get their average goals
# Scored and conceded. I'll take last year prem table as a starting point

import kagglehub
import pandas as pd
import numpy as np
import os
import itertools


AV_GOALS_FOR = "Av_Goals_For"
AV_GOALS_AGAINST = "Av_Goals_Against"

# Download latest version
path = kagglehub.dataset_download("mertbayraktar/english-premier-league-matches-20232024-season")
csv_path = os.path.join(path, "matches.csv")
score_data = pd.read_csv(filepath_or_buffer=csv_path)


def update_stats(full_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Construct an initial summary statistics table.
    Want to get a rolling window of last 18 games.
    Average goals for and goals against and a list of
    the scores of each in chronological order.

    :param full_stats:
    :return:
    """
    team_index = full_stats['Team'].unique()
    stats_frame = pd.DataFrame(index=team_index)
    stats_frame['Av_Goals_For'] = full_stats.groupby('Team')['GF'].mean()
    stats_frame['Av_Goals_Against'] = full_stats.groupby('Team')['GA'].mean()
    stats_frame['Av_Goals_Scored'] = full_stats['GF'].mean()
    stats_frame['Av_Goals_Conceded'] = full_stats['GF'].mean()

    return stats_frame

def simulate_goal_scored(team_a_exp_score: float,
                         team_b_exp_concede: float,
                         av_goal_scored: float,
                         av_goal_conceded: float) -> int:
    """

    :param team_a_exp_score:
    :param team_b_exp_concede:
    :return:
    """
    expected_goals = ((team_a_exp_score/av_goal_scored) *
                      (team_b_exp_concede/av_goal_conceded)) * av_goal_scored
    return np.random.poisson(expected_goals)

def simulate_game(home_stats:pd.Series,
                  away_stats: pd.Series,
                  week: int
                  ) -> pd.DataFrame:
    """

    :param home_stats:
    :param away_stats:
    :param week:
    :return:
    """
    # Get goals for team a
    home_goals = simulate_goal_scored(team_a_exp_score=home_stats[AV_GOALS_FOR],
                                      team_b_exp_concede=away_stats[AV_GOALS_AGAINST],
                                      av_goal_scored=home_stats['Av_Goals_Scored'],
                                      av_goal_conceded=home_stats['Av_Goals_Conceded'])

    away_goals = simulate_goal_scored(team_a_exp_score=away_stats[AV_GOALS_FOR],
                                      team_b_exp_concede=home_stats[AV_GOALS_AGAINST],
                                      av_goal_scored=home_stats['Av_Goals_Scored'],
                                      av_goal_conceded=home_stats['Av_Goals_Conceded'])
    if home_goals == away_goals:
        home_points = 1
        away_points = 1
    elif home_goals > away_goals:
        home_points = 3
        away_points = 0
    elif home_goals < away_goals:
        home_points = 0
        away_points = 3
    else:
        raise TypeError("Incorrect score type")

    home_row = pd.DataFrame(
        {
            'Team': [home_stats.name],
            'GF': [home_goals],
            'GA': [away_goals],
            'Points': [home_points],
            'Round': [f'Matchweek {week}'],
            'Opponent': [away_stats.name]
        }
    )

    away_row = pd.DataFrame(
        {
            'Team': [away_stats.name],
            'GF': [away_goals],
            'GA': [home_goals],
            'Points': [away_points],
            'Round': [f'Matchweek {week}'],
            'Opponent': [home_stats.name]
        }
    )

    output_frame = pd.concat([home_row, away_row])

    return output_frame

def add_match_week(fixtures_df: pd.DataFrame) -> pd.DataFrame:
    # Dictionary to track the last week a team played
    team_last_week = {}
    week = 1
    fixtures_list =[]

    for _, row in fixtures_df.iterrows():
        team1, team2 = row["Team"], row["Opponent"]

        # Find the earliest available week where neither team has played
        while team1 in team_last_week and team_last_week[team1] == week or \
                team2 in team_last_week and team_last_week[team2] == week:
            week += 1

        # Assign week and update tracking
        fixtures_list.append((team1, team2, week))
        team_last_week[team1] = week
        team_last_week[team2] = week

        # Reset week to 1 if it exceeds 38 (for long lists)
        if week > 37:
            week = 1

    # Convert back to DataFrame
    schedule_df = pd.DataFrame(fixtures_list, columns=["Team", "Opponent", "Round"])
    sorted_schedule = schedule_df.sort_values("Round")

    return sorted_schedule

def run_season() -> pd.DataFrame:
    filtered_results = score_data[['Team', 'GF', 'GA', 'Round', 'Opponent']]
    filtered_results['Points'] = np.nan
    teams = filtered_results['Team'].unique()
    fixtures =  pd.DataFrame(list(itertools.product(teams, teams)), columns=['Team', 'Opponent'])
    fixtures = fixtures.loc[fixtures['Team'] != fixtures['Opponent']]
    fixtures = add_match_week(fixtures)
    fixtures = fixtures.sort_values('Round')
    for _, row in fixtures.iterrows():
        home = row['Team']
        away = row['Opponent']
        match_week = row['Round']
        updated_stats = update_stats(filtered_results)
        home_stats = updated_stats.loc[home]
        away_stats = updated_stats.loc[away]
        try:
            match_results = simulate_game(
                home_stats=home_stats,
                away_stats=away_stats,
                week = match_week
            )
        except:
            print('test')
        filtered_results = pd.concat([filtered_results, match_results])

    return filtered_results

def season_summary(all_results: pd.DataFrame) -> pd.DataFrame:
    this_season_results = all_results.loc[~all_results['Points'].isna()]
    summary_table = this_season_results.groupby('Team').sum().sort_values('Points', ascending=False)

    return summary_table

def get_winner_season() -> str:
    season_results = run_season()
    league_table = season_summary(all_results=season_results)
    winner = league_table.iloc[0].name

    return winner

if __name__ == '__main__':
    winners = []
    for game in range(1,100):
        winner = get_winner_season()
        winners = winners + [winner]

    winner_frame = pd.DataFrame(data={'winners': winners})
    print(winner_frame.groupby(['winners'])['winners'].count())
