"""
Task 2: Contrarian Scoring & Distribution Calibration Engine for The Bitcoin Score.

Matches the exact scale and behavior of https://thebitcoinscore.com/:
- 0–100 score from 8 market indicators:
  - 0–25   (Overheated):  ~5% of time  -> Keep DCA as-is / Caution on overextension
  - 25–40  (Caution):     ~20% of time -> Market running hot
  - 40–60  (Neutral):     ~50% of time -> Keep your regular DCA as-is (×1.00)
  - 60–75  (Buy More):    ~20% of time -> Increase your daily DCA by +25% (×1.25)
  - 75–100 (Strong Buy):  ~5% of time  -> Increase your daily DCA by +50% to +100% (×1.50+)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd


SIGNAL_WEIGHTS: Dict[str, float] = {
    "mvrv": 0.22,           # Primary on-chain cycle valuation anchor
    "ema200_ratio": 0.18,   # 200-day EMA trend extension / deep dip detector
    "rsi14": 0.14,          # Wilder's 14-day RSI momentum exhaustion
    "fng": 0.14,            # Alternative.me Fear & Greed Index
    "dxy": 0.10,            # US Dollar Index (DXY)
    "m2_yoy": 0.10,         # US M2 Money Supply YoY growth (FRED)
    "google_trends": 0.08,  # Worldwide "Bitcoin" Google search interest
    "btc_dominance": 0.04,  # Lightly weighted (4%) — most debated signal
}


@dataclass(frozen=True)
class ZoneMetadata:
    name: str
    min_score: float
    max_score: float
    target_share: float
    color_hex: str
    dca_multiplier: float
    dca_headline: str
    dca_subtext: str
    action_summary: str


SCORE_ZONES_ACCUMULATION_HIGH: Tuple[ZoneMetadata, ...] = (
    ZoneMetadata(
        name="Overheated",
        min_score=0.0,
        max_score=25.0,
        target_share=0.05,
        color_hex="#ef4444",
        dca_multiplier=0.50,
        dca_headline="Market is overheated — keep regular DCA or scale back",
        dca_subtext="Extreme greed & stretched on-chain valuation. Historically rare (~5% of days).",
        action_summary="Keep DCA as-is -- we don't back selling",
    ),
    ZoneMetadata(
        name="Caution",
        min_score=25.0,
        max_score=40.0,
        target_share=0.20,
        color_hex="#f59e0b",
        dca_multiplier=0.75,
        dca_headline="Exercise caution — maintain baseline DCA",
        dca_subtext="Momentum and valuation are running warm (~20% of days).",
        action_summary="Keep DCA as-is -- we don't back selling",
    ),
    ZoneMetadata(
        name="Neutral",
        min_score=40.0,
        max_score=60.0,
        target_share=0.50,
        color_hex="#94a3b8",
        dca_multiplier=1.00,
        dca_headline="Keep your regular daily DCA as-is",
        dca_subtext="The market is in fair-value equilibrium (~50% of days).",
        action_summary="Keep your regular DCA as-is",
    ),
    ZoneMetadata(
        name="Buy More",
        min_score=60.0,
        max_score=75.0,
        target_share=0.20,
        color_hex="#10b981",
        dca_multiplier=1.25,
        dca_headline="Increase your daily DCA by +25%",
        dca_subtext="The market shows signs of undervaluation.",
        action_summary="Consider increasing your DCA",
    ),
    ZoneMetadata(
        name="Strong Buy",
        min_score=75.0,
        max_score=100.0,
        target_share=0.05,
        color_hex="#059669",
        dca_multiplier=1.50,
        dca_headline="Increase your daily DCA by +50%",
        dca_subtext="Extreme fear & deep cycle value (~5% of days). Maximum accumulation zone.",
        action_summary="Consider increasing your DCA",
    ),
)

SCORE_ZONES_ACCUMULATION_LOW: Tuple[ZoneMetadata, ...] = (
    ZoneMetadata(
        name="Strong Buy",
        min_score=0.0,
        max_score=20.0,
        target_share=0.05,
        color_hex="#059669",
        dca_multiplier=1.50,
        dca_headline="Increase your daily DCA by +50%",
        dca_subtext="Extreme fear & deep cycle value (~5% of days).",
        action_summary="Consider increasing your DCA",
    ),
    ZoneMetadata(
        name="Buy More",
        min_score=20.0,
        max_score=40.0,
        target_share=0.20,
        color_hex="#10b981",
        dca_multiplier=1.25,
        dca_headline="Increase your daily DCA by +25%",
        dca_subtext="The market shows signs of undervaluation.",
        action_summary="Consider increasing your DCA",
    ),
    ZoneMetadata(
        name="Neutral",
        min_score=40.0,
        max_score=60.0,
        target_share=0.50,
        color_hex="#94a3b8",
        dca_multiplier=1.00,
        dca_headline="Keep your regular daily DCA as-is",
        dca_subtext="The market is in fair-value equilibrium (~50% of days).",
        action_summary="Keep your regular DCA as-is",
    ),
    ZoneMetadata(
        name="Caution",
        min_score=60.0,
        max_score=80.0,
        target_share=0.20,
        color_hex="#f59e0b",
        dca_multiplier=0.75,
        dca_headline="Exercise caution — maintain baseline DCA",
        dca_subtext="Momentum and valuation are running warm (~20% of days).",
        action_summary="Keep DCA as-is -- we don't back selling",
    ),
    ZoneMetadata(
        name="Overheated",
        min_score=80.0,
        max_score=100.0,
        target_share=0.05,
        color_hex="#ef4444",
        dca_multiplier=0.50,
        dca_headline="Market is overheated — keep regular DCA",
        dca_subtext="Extreme greed & stretched on-chain valuation (~5% of days).",
        action_summary="Keep DCA as-is -- we don't back selling",
    ),
)

SCORE_ZONES = SCORE_ZONES_ACCUMULATION_HIGH


def _piecewise_linear(series: pd.Series, xp: list[float], fp: list[float]) -> pd.Series:
    vals = np.interp(series.to_numpy(dtype=float), xp, fp)
    return pd.Series(vals, index=series.index).clip(0.0, 100.0)


def normalize_individual_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes each of the 8 raw signals into a 0-100 heat sub-score:
      - Low heat (0-35)   -> Undervalued / Fear / Supports accumulating (Green on UI)
      - Mid heat (43-57)  -> Neutral (Gray on UI)
      - High heat (58-100)-> Caution / Headwind / Overheated (Red on UI)
    """
    scores = pd.DataFrame(index=df.index)

    # 1. Fear & Greed Index (0-100 native): 32 -> ~28 (Green)
    scores["score_fng"] = _piecewise_linear(
        df["fng"],
        xp=[5.0, 20.0, 35.0, 50.0, 68.0, 82.0, 95.0],
        fp=[0.0, 18.0, 30.0, 50.0, 66.0, 82.0, 100.0],
    )

    # 2. RSI14 (Wilder's 14-day RSI): 33-35 -> ~24 (Green)
    scores["score_rsi14"] = _piecewise_linear(
        df["rsi14"],
        xp=[20.0, 32.0, 42.0, 50.0, 62.0, 75.0, 88.0],
        fp=[0.0, 18.0, 32.0, 50.0, 66.0, 82.0, 100.0],
    )

    # 3. EMA200 Distance (Price / EMA200 ratio): 0.96 (-3.9%) -> ~25 (Green)
    scores["score_ema200_ratio"] = _piecewise_linear(
        df["ema200_ratio"],
        xp=[0.55, 0.78, 1.00, 1.15, 1.38, 1.75, 2.40],
        fp=[0.0, 15.0, 28.0, 50.0, 66.0, 82.0, 100.0],
    )

    # 4. MVRV Ratio: 1.39-1.44 -> ~26 (Green)
    scores["score_mvrv"] = _piecewise_linear(
        df["mvrv"],
        xp=[0.70, 1.05, 1.50, 1.85, 2.35, 3.30, 4.30],
        fp=[0.0, 14.0, 28.0, 50.0, 66.0, 82.0, 100.0],
    )

    # 5. DXY (US Dollar Index): Rising 90d/365d DXY is a headwind (Red on UI when > 0)
    dxy_mean = df["dxy"].rolling(180, min_periods=30).mean()
    dxy_std = df["dxy"].rolling(180, min_periods=30).std().replace(0, 1.0)
    dxy_z = ((df["dxy"] - dxy_mean) / dxy_std).fillna(0.0)
    scores["score_dxy"] = _piecewise_linear(
        dxy_z,
        xp=[-2.2, -1.2, -0.4, 0.0, 0.4, 1.2, 2.2],
        fp=[5.0, 20.0, 36.0, 50.0, 68.0, 82.0, 96.0],
    )

    # 6. Liquidity (US M2 YoY % Growth): +6.67% YoY is favorable (Green)
    scores["score_m2_yoy"] = _piecewise_linear(
        -df["m2_yoy"],
        xp=[-12.0, -6.5, -3.5, -1.5, 1.0, 3.5, 6.0],
        fp=[8.0, 20.0, 32.0, 50.0, 66.0, 82.0, 95.0],
    )

    # 7. BTC Dominance (Lightly weighted at 4%): 59.7% is favorable (Green)
    scores["score_btc_dominance"] = _piecewise_linear(
        -df["btc_dominance"],
        xp=[-70.0, -60.0, -54.0, -48.0, -42.0, -38.0, -34.0],
        fp=[12.0, 22.0, 34.0, 50.0, 66.0, 80.0, 95.0],
    )

    # 8. Google Trends ("Bitcoin" 0-100): 19-22 is low retail interest / quiet accumulation (Green)
    scores["score_google_trends"] = _piecewise_linear(
        df["google_trends"],
        xp=[3.0, 14.0, 26.0, 38.0, 52.0, 70.0, 92.0],
        fp=[0.0, 16.0, 28.0, 50.0, 66.0, 82.0, 100.0],
    )

    return scores


def calibrate_to_target_distribution(
    raw_composite: pd.Series, high_is_buy: bool = True
) -> pd.Series:
    """
    Calibrates the composite index so that historical time spent in each zone matches:
      ~5% Strong Buy | ~20% Buy More | ~50% Neutral | ~20% Caution | ~5% Overheated
    while preserving cardinal sensitivity so current readings match ~67-68 (Buy More).
    """
    clean = raw_composite.dropna()
    if clean.empty:
        return raw_composite

    target_quantiles = [0.00, 0.05, 0.25, 0.50, 0.75, 0.95, 1.00]
    if high_is_buy:
        target_scores = [8.0, 25.0, 40.0, 50.0, 60.0, 75.0, 92.0]
        series_to_map = 100.0 - raw_composite
        clean_map = 100.0 - clean
    else:
        target_scores = [4.0, 20.0, 40.0, 50.0, 60.0, 80.0, 96.0]
        series_to_map = raw_composite
        clean_map = clean

    empirical_knots = np.quantile(clean_map.to_numpy(dtype=float), target_quantiles)
    for i in range(1, len(empirical_knots)):
        if empirical_knots[i] <= empirical_knots[i - 1]:
            empirical_knots[i] = empirical_knots[i - 1] + 1e-4

    quantile_mapped = np.interp(
        series_to_map.to_numpy(dtype=float),
        empirical_knots,
        target_scores,
    )
    blended = 0.55 * quantile_mapped + 0.45 * series_to_map.to_numpy(dtype=float)
    return pd.Series(blended, index=raw_composite.index, name="accumulation_score").clip(0.0, 100.0)


def classify_score_zone(score: float, high_is_buy: bool = True) -> ZoneMetadata:
    zones = SCORE_ZONES_ACCUMULATION_HIGH if high_is_buy else SCORE_ZONES_ACCUMULATION_LOW
    for zone in zones:
        if score < zone.max_score or zone.max_score == 100.0:
            return zone
    return zones[-1]


def compute_accumulation_score(df: pd.DataFrame, high_is_buy: bool = True) -> pd.DataFrame:
    result = df.copy()
    result["pct_change_1d"] = result["close"].pct_change() * 100.0
    result["ema200_pct"] = ((result["close"] - result["ema200"]) / result["ema200"]) * 100.0
    result["dxy_90d_roc"] = result["dxy"].pct_change(90) * 100.0
    result["gt_percentile"] = result["google_trends"].expanding(min_periods=30).rank(pct=True) * 100.0

    sub_scores = normalize_individual_signals(result)
    result = pd.concat([result, sub_scores], axis=1)

    raw_heat = pd.Series(0.0, index=result.index)
    total_weight = sum(SIGNAL_WEIGHTS.values())
    for sig_name, weight in SIGNAL_WEIGHTS.items():
        raw_heat += result[f"score_{sig_name}"] * (weight / total_weight)

    result["raw_composite_score"] = raw_heat.ewm(span=3, adjust=False).mean()
    result["accumulation_score"] = calibrate_to_target_distribution(
        result["raw_composite_score"], high_is_buy=high_is_buy
    )

    zones = [classify_score_zone(val, high_is_buy=high_is_buy) for val in result["accumulation_score"]]
    result["zone_name"] = [z.name for z in zones]
    result["zone_color"] = [z.color_hex for z in zones]
    result["dca_multiplier"] = [z.dca_multiplier for z in zones]

    return result


def run_dca_backtest(
    scored_df: pd.DataFrame,
    start_date: str,
    end_date: str,
    base_daily_usd: float = 20.0,
) -> Dict[str, float | pd.DataFrame]:
    """
    Backtests Standard Flat DCA vs. Score-Adjusted Smart DCA over [start_date, end_date].
    In Smart DCA:
      - Score >= 75 (Strong Buy): 1.50x daily contribution
      - Score 60-75 (Buy More):   1.25x daily contribution
      - Score 40-60 (Neutral):    1.00x daily contribution
      - Score 25-40 (Caution):    0.75x daily contribution
      - Score < 25  (Overheated): 0.50x daily contribution
    Also computes a 'Normalized Budget Smart DCA' scaled to the exact same total USD
    invested as Flat DCA to isolate pure timing alpha!
    """
    sub = scored_df.loc[start_date:end_date].copy()
    if sub.empty:
        sub = scored_df.copy()

    price = sub["close"]
    mult = sub["dca_multiplier"]

    # 1. Flat DCA
    sub["flat_usd"] = base_daily_usd
    sub["flat_btc_bought"] = sub["flat_usd"] / price
    sub["flat_cum_usd"] = sub["flat_usd"].cumsum()
    sub["flat_cum_btc"] = sub["flat_btc_bought"].cumsum()
    sub["flat_portfolio_usd"] = sub["flat_cum_btc"] * price

    # 2. Score-Adjusted Smart DCA
    sub["smart_usd"] = base_daily_usd * mult
    sub["smart_btc_bought"] = sub["smart_usd"] / price
    sub["smart_cum_usd"] = sub["smart_usd"].cumsum()
    sub["smart_cum_btc"] = sub["smart_btc_bought"].cumsum()
    sub["smart_portfolio_usd"] = sub["smart_cum_btc"] * price

    final_price = float(price.iloc[-1])
    flat_invested = float(sub["flat_cum_usd"].iloc[-1])
    flat_btc = float(sub["flat_cum_btc"].iloc[-1])
    flat_val = flat_btc * final_price
    flat_avg_price = flat_invested / flat_btc if flat_btc > 0 else 0.0
    flat_roi = ((flat_val - flat_invested) / flat_invested * 100.0) if flat_invested > 0 else 0.0

    smart_invested = float(sub["smart_cum_usd"].iloc[-1])
    smart_btc = float(sub["smart_cum_btc"].iloc[-1])
    smart_val = smart_btc * final_price
    smart_avg_price = smart_invested / smart_btc if smart_btc > 0 else 0.0
    smart_roi = ((smart_val - smart_invested) / smart_invested * 100.0) if smart_invested > 0 else 0.0

    # Equal-budget comparison (if same total USD was deployed using score weights)
    budget_scale = flat_invested / smart_invested if smart_invested > 0 else 1.0
    equal_budget_btc = smart_btc * budget_scale
    btc_extra_pct = ((equal_budget_btc - flat_btc) / flat_btc * 100.0) if flat_btc > 0 else 0.0

    return {
        "days": len(sub),
        "flat_invested": flat_invested,
        "flat_btc": flat_btc,
        "flat_val": flat_val,
        "flat_avg_price": flat_avg_price,
        "flat_roi": flat_roi,
        "smart_invested": smart_invested,
        "smart_btc": smart_btc,
        "smart_val": smart_val,
        "smart_avg_price": smart_avg_price,
        "smart_roi": smart_roi,
        "equal_budget_btc": equal_budget_btc,
        "btc_extra_pct": btc_extra_pct,
        "roi_alpha_pct": smart_roi - flat_roi,
        "series_df": sub,
    }


def get_zone_distribution_report(scored_df: pd.DataFrame, high_is_buy: bool = True) -> pd.DataFrame:
    zones = SCORE_ZONES_ACCUMULATION_HIGH if high_is_buy else SCORE_ZONES_ACCUMULATION_LOW
    total_days = len(scored_df.dropna(subset=["accumulation_score"]))
    rows = []
    ordered_zones = sorted(
        zones,
        key=lambda z: ["Strong Buy", "Buy More", "Neutral", "Caution", "Overheated"].index(z.name),
    )
    for zone in ordered_zones:
        if zone.max_score < 100.0:
            mask = (scored_df["accumulation_score"] >= zone.min_score) & (
                scored_df["accumulation_score"] < zone.max_score
            )
        else:
            mask = (scored_df["accumulation_score"] >= zone.min_score) & (
                scored_df["accumulation_score"] <= zone.max_score
            )
        days_count = int(mask.sum())
        actual_pct = (days_count / total_days * 100.0) if total_days > 0 else 0.0
        rows.append(
            {
                "Zone": zone.name,
                "Score Range": f"{int(zone.min_score)}-{int(zone.max_score)}",
                "DCA Multiplier": f"×{zone.dca_multiplier:.2f}",
                "Target %": f"~{int(zone.target_share * 100)}%",
                "Actual %": f"{actual_pct:.1f}%",
                "Historical Days": days_count,
            }
        )
    return pd.DataFrame(rows)
