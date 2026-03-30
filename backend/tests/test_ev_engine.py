import pytest
from app.ml.ev_engine import compute_ev, implied_probability, evaluate_bet, kelly_stake


def test_compute_ev_positive():
    # model says 58%, odds 2.10 → EV = 0.218
    ev = compute_ev(0.58, 2.10)
    assert ev == pytest.approx(0.218, abs=0.001)


def test_compute_ev_negative():
    # model says 40%, odds 2.10 → no value
    ev = compute_ev(0.40, 2.10)
    assert ev < 0


def test_implied_probability():
    assert implied_probability(2.0) == 0.5
    assert implied_probability(1.5) == pytest.approx(0.6667, abs=0.001)


def test_evaluate_bet_value():
    bet = evaluate_bet("h2h", "home_win", 0.62, 2.10)
    assert bet.is_value is True
    assert bet.expected_value > 0


def test_evaluate_bet_no_value():
    bet = evaluate_bet("h2h", "home_win", 0.45, 2.10)
    assert bet.is_value is False


def test_kelly_stake():
    stake = kelly_stake(1000, 0.58, 2.10, fraction=0.25)
    assert stake > 0
    assert stake < 1000
