"""
Expected Value engine.

EV = (model_probability * decimal_odds) - 1

A positive EV means the bet is theoretically profitable long-term.
We only surface bets where EV > threshold and model confidence > threshold.
"""
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValueBet:
    market: str
    selection: str
    model_probability: float
    implied_probability: float
    decimal_odds: float
    expected_value: float
    confidence_label: str   # "high" | "medium" | "low"
    is_value: bool


def compute_ev(model_prob: float, decimal_odds: float) -> float:
    """
    EV = (p * odds) - 1
    e.g. p=0.58, odds=2.10 → EV = 0.218 (positive = value)
    """
    return round((model_prob * decimal_odds) - 1, 4)


def implied_probability(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability (no-vig approximation)."""
    if decimal_odds <= 1.0:
        return 1.0
    return round(1 / decimal_odds, 4)


def confidence_label(model_prob: float, ev: float) -> str:
    """Classify confidence tier for UI display."""
    if model_prob >= 0.65 and ev >= 0.10:
        return "high"
    elif model_prob >= 0.57 and ev >= 0.03:
        return "medium"
    else:
        return "low"


def evaluate_bet(
    market: str,
    selection: str,
    model_probability: float,
    decimal_odds: float,
    min_ev: float = 0.03,
    min_confidence: float = 0.52,
) -> ValueBet:
    """
    Full evaluation of a single market/selection.
    Returns a ValueBet with is_value=True if it clears both thresholds.
    """
    implied_prob = implied_probability(decimal_odds)
    ev = compute_ev(model_probability, decimal_odds)
    label = confidence_label(model_probability, ev)

    is_value = (
        ev >= min_ev
        and model_probability >= min_confidence
        and model_probability > implied_prob
    )

    return ValueBet(
        market=market,
        selection=selection,
        model_probability=model_probability,
        implied_probability=implied_prob,
        decimal_odds=decimal_odds,
        expected_value=ev,
        confidence_label=label,
        is_value=is_value,
    )


def kelly_stake(bankroll: float, model_prob: float, decimal_odds: float, fraction: float = 0.25) -> float:
    """
    Fractional Kelly criterion stake recommendation.
    fraction=0.25 = quarter Kelly (conservative, recommended for sports betting).
    Returns suggested stake amount.
    """
    b = decimal_odds - 1  # net odds
    q = 1 - model_prob
    kelly_pct = (model_prob * b - q) / b
    fractional_kelly = max(0, kelly_pct * fraction)
    return round(bankroll * fractional_kelly, 2)
