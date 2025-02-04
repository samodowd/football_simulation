from src.main import simulate_goal_scored

def test_goal_simulation():
    random_goal_scored = simulate_goal_scored(
        team_a_exp_score=4,
        team_b_exp_concede=4,
        av_goal_scored=2,
        av_goal_conceded=2
    )

    assert random_goal_scored >=0
    assert isinstance(random_goal_scored, int)