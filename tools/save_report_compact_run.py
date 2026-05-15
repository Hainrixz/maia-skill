#!/usr/bin/env python3
import json
from pathlib import Path

workspace = Path('/Users/carlosfuentes/GitHub/maia-skill')

sectors = {
  "crypto": {
    "sector": "crypto",
    "timestamp": "2026-05-05T00:00:00Z",
    "sector_summary": "BTC and ETH are firm despite geopolitics, with BTC back above 80k and ETH showing relative strength. Risk appetite is selective and macro headline-sensitive.",
    "sector_outlook": "neutral",
    "top_pick": "ETH",
    "top_pick_reasoning": "ETH has stronger risk-adjusted upside than BTC here given lower RSI and improving breadth.",
    "assets": [
      {
        "name": "Ethereum",
        "symbol": "ETH",
        "current_price": "$2,372.77",
        "change_24h": "+0.7%",
        "change_7d": "-0.1%",
        "change_30d": "+3.6%",
        "ytd_change": "+2.2%",
        "week_52_high": "$4,100",
        "week_52_low": "$1,450",
        "market_cap": "$287B",
        "volume_24h": "$20.7B",
        "sentiment": "neutral",
        "social_sentiment": "bullish",
        "social_buzz": "high",
        "confidence": 7.3,
        "source_agreement": "high",
        "key_news": [
          "BTC/ETH advanced while broader macro stayed risk-off on Hormuz headlines.",
          "Policy discussion around crypto market structure remains a medium-term support."
        ],
        "social_highlights": [
          "Momentum traders rotating from BTC into large-cap alt beta.",
          "Stablecoin and on-chain infrastructure narratives remain active."
        ],
        "recommendation": "buy",
        "reasoning": "ETH offers better asymmetry than BTC at current RSI with still-deep liquidity."
      },
      {
        "name": "Bitcoin",
        "symbol": "BTC",
        "current_price": "$80,143",
        "change_24h": "+1.9%",
        "change_7d": "+0.9%",
        "change_30d": "+4.9%",
        "ytd_change": "+6.0%",
        "week_52_high": "$92,000",
        "week_52_low": "$49,000",
        "market_cap": "$1.62T",
        "volume_24h": "$50.7B",
        "sentiment": "neutral",
        "social_sentiment": "bullish",
        "social_buzz": "high",
        "confidence": 6.9,
        "source_agreement": "high",
        "key_news": [
          "BTC reclaimed 80k even as oil/geopolitical risk stayed elevated.",
          "Liquidity remains concentrated in majors while high-beta alts are mixed."
        ],
        "social_highlights": [
          "Trend-following flows remain positive but crowded.",
          "Macro traders treat BTC as tactical risk asset, not pure hedge, this week."
        ],
        "recommendation": "hold",
        "reasoning": "BTC trend is intact but RSI is relatively elevated versus ETH for fresh entries."
      }
    ]
  },
  "stocks": {
    "sector": "stocks",
    "timestamp": "2026-05-05T00:00:00Z",
    "sector_summary": "US equities are mixed-to-soft with the S&P 500 pulling back from highs as Middle East risk lifts volatility. Defensive healthcare and quality financials screen best on valuation plus entry setup.",
    "sector_outlook": "neutral",
    "top_pick": "GILD",
    "top_pick_reasoning": "GILD combines low valuation, near-term catalyst (May 7 AMC), and strong entry quality.",
    "assets": [
      {
        "name": "Gilead Sciences",
        "symbol": "GILD",
        "current_price": "$132.69",
        "change_24h": "+0.79%",
        "change_7d": "+1.4%",
        "change_30d": "+5.8%",
        "ytd_change": "+12.0%",
        "week_52_high": "$138",
        "week_52_low": "$94",
        "market_cap": "$163.4B",
        "volume_24h": "$2.1M",
        "sentiment": "bullish",
        "social_sentiment": "neutral",
        "social_buzz": "medium",
        "confidence": 8.9,
        "source_agreement": "high",
        "key_news": [
          "Q1 earnings scheduled May 7 (AMC), consensus EPS near 1.91.",
          "Healthcare defensives are attracting flows during oil/geopolitical volatility."
        ],
        "social_highlights": [
          "Pre-earnings positioning is constructive but not euphoric.",
          "Value + catalyst setup is frequently cited by discretionary desks."
        ],
        "recommendation": "buy",
        "reasoning": "Catalyst timing and inexpensive multiple support a favorable risk/reward into and after earnings."
      },
      {
        "name": "Amgen",
        "symbol": "AMGN",
        "current_price": "$323.85",
        "change_24h": "-1.81%",
        "change_7d": "-2.0%",
        "change_30d": "+0.6%",
        "ytd_change": "+4.5%",
        "week_52_high": "$346",
        "week_52_low": "$255",
        "market_cap": "$178.1B",
        "volume_24h": "$1.4M",
        "sentiment": "neutral",
        "social_sentiment": "neutral",
        "social_buzz": "medium",
        "confidence": 8.4,
        "source_agreement": "high",
        "key_news": [
          "Amgen reported Q1 2026 results on Apr 30.",
          "Amgen announced an additional $300M US manufacturing investment on May 4."
        ],
        "social_highlights": [
          "Focus remains on execution and pipeline durability.",
          "Income-oriented buyers still support pullbacks."
        ],
        "recommendation": "buy",
        "reasoning": "Reasonable valuation and defensive cash-flow profile fit a moderate-risk allocation in a volatile tape."
      },
      {
        "name": "NVIDIA",
        "symbol": "NVDA",
        "current_price": "$198.48",
        "change_24h": "+0.02%",
        "change_7d": "-0.3%",
        "change_30d": "+6.0%",
        "ytd_change": "+6.0%",
        "week_52_high": "$216.8",
        "week_52_low": "$110.8",
        "market_cap": "$4.8T",
        "volume_24h": "125.4M",
        "sentiment": "neutral",
        "social_sentiment": "mixed",
        "social_buzz": "very_high",
        "confidence": 8.1,
        "source_agreement": "high",
        "key_news": [
          "Earnings expected May 20, 2026 after close.",
          "Market remains focused on China/export constraints and resulting share impact."
        ],
        "social_highlights": [
          "AI demand remains strong but valuation sensitivity to guidance is high.",
          "Headline risk around export policy drives intraday swings."
        ],
        "recommendation": "hold",
        "reasoning": "Secular AI strength is intact, but event and policy risk justify measured sizing before earnings."
      },
      {
        "name": "Occidental Petroleum",
        "symbol": "OXY",
        "current_price": "$60.27",
        "change_24h": "+2.66%",
        "change_7d": "+6.1%",
        "change_30d": "+8.4%",
        "ytd_change": "+14.2%",
        "week_52_high": "$66",
        "week_52_low": "$47",
        "market_cap": "$58.2B",
        "volume_24h": "2.6M",
        "sentiment": "neutral",
        "social_sentiment": "bullish",
        "social_buzz": "medium",
        "confidence": 6.9,
        "source_agreement": "high",
        "key_news": [
          "OXY rose with the oil risk premium as Hormuz disruptions escalated.",
          "Company announced CEO transition to Richard Jackson with Vicki Hollub retiring."
        ],
        "social_highlights": [
          "Macro oil headlines dominate near-term price action.",
          "Leadership transition is watched but secondary to crude direction."
        ],
        "recommendation": "hold",
        "reasoning": "Strong oil beta helps near term, but position risk should stay capped due to geopolitical gap risk."
      }
    ]
  },
  "materials": {
    "sector": "materials",
    "timestamp": "2026-05-05T00:00:00Z",
    "sector_summary": "Materials remain supported by geopolitical hedging and elevated commodity volatility. Gold complex stays resilient even with intraday pullbacks.",
    "sector_outlook": "bullish",
    "top_pick": "GLD",
    "top_pick_reasoning": "GLD offers cleaner hedge characteristics than miners while preserving upside to persistent macro stress.",
    "assets": [
      {
        "name": "SPDR Gold Shares",
        "symbol": "GLD",
        "current_price": "$414.71",
        "change_24h": "-0.6%",
        "change_7d": "+1.2%",
        "change_30d": "+4.4%",
        "ytd_change": "+16.8%",
        "week_52_high": "$425",
        "week_52_low": "$273",
        "market_cap": "$79B",
        "volume_24h": "high",
        "sentiment": "bullish",
        "social_sentiment": "bullish",
        "social_buzz": "high",
        "confidence": 8.2,
        "source_agreement": "high",
        "key_news": [
          "Gold remains elevated while geopolitical risk and inflation uncertainty persist.",
          "Safe-haven demand stays firm despite short-term dollar/yield noise."
        ],
        "social_highlights": [
          "Macro desks continue using gold as geopolitical hedge.",
          "Retail sentiment is constructive but below mania levels."
        ],
        "recommendation": "buy",
        "reasoning": "GLD provides efficient downside macro hedge with still-positive trend structure."
      },
      {
        "name": "VanEck Gold Miners ETF",
        "symbol": "GDX",
        "current_price": "$85.65",
        "change_24h": "+0.4%",
        "change_7d": "+2.0%",
        "change_30d": "+6.5%",
        "ytd_change": "+18.3%",
        "week_52_high": "$89",
        "week_52_low": "$42",
        "market_cap": "$16B",
        "volume_24h": "high",
        "sentiment": "bullish",
        "social_sentiment": "neutral",
        "social_buzz": "medium",
        "confidence": 8.0,
        "source_agreement": "medium",
        "key_news": [
          "Miners are benefiting from elevated bullion prices and margin expansion hopes.",
          "Volatility remains higher than spot gold instruments."
        ],
        "social_highlights": [
          "Rotation from broad equities into miners increased this week.",
          "Traders prefer scaling entries over full-size buys."
        ],
        "recommendation": "buy",
        "reasoning": "GDX adds upside torque to gold exposure but requires tighter risk controls than GLD."
      },
      {
        "name": "Freeport-McMoRan",
        "symbol": "FCX",
        "current_price": "$55.57",
        "change_24h": "-1.1%",
        "change_7d": "-2.5%",
        "change_30d": "+1.0%",
        "ytd_change": "+7.4%",
        "week_52_high": "$61",
        "week_52_low": "$35",
        "market_cap": "$79B",
        "volume_24h": "high",
        "sentiment": "neutral",
        "social_sentiment": "mixed",
        "social_buzz": "medium",
        "confidence": 6.8,
        "source_agreement": "medium",
        "key_news": [
          "Copper demand outlook is constructive but sensitive to China growth headlines.",
          "Stock remains technically oversold versus broad market."
        ],
        "social_highlights": [
          "Value buyers are active on dips.",
          "Macro funds remain cautious on China-linked cyclicals."
        ],
        "recommendation": "hold",
        "reasoning": "FCX has rebound potential from oversold levels, but China macro uncertainty tempers conviction."
      }
    ]
  }
}

strategy = {
  "risk_profile": "moderate",
  "macro_environment": {
    "summary": "S&P 500 softened from highs as Hormuz conflict risk lifted oil volatility and risk premiums, while tariff policy remains active with refunds starting as early as May 12. Volatility is elevated but not panic-level, favoring selective quality and hedge-balanced positioning.",
    "interest_rate_outlook": "stable",
    "inflation_outlook": "rising",
    "geopolitical_risk": "high",
    "key_factors": [
      "Hormuz disruptions and >$100 oil regime",
      "Active tariff framework and refund timeline",
      "Mega-cap AI earnings/event risk concentration"
    ]
  },
  "portfolio_allocation": {"crypto": 12, "stocks": 63, "materials": 18, "cash": 7},
  "cross_sector_insights": [
    {
      "insight": "Oil/geopolitical shocks are supporting defensive healthcare and gold together.",
      "implication": "Pair quality pharma with gold exposure to smooth portfolio drawdowns."
    },
    {
      "insight": "AI leaders remain structurally strong but increasingly sensitive to export-policy headlines.",
      "implication": "Keep NVDA exposure, but trim pre-earnings sizing and use disciplined stops."
    },
    {
      "insight": "Tariff uncertainty raises input-cost and growth-path dispersion across cyclicals.",
      "implication": "Favor low-PEG franchises and avoid overconcentration in policy-sensitive names."
    }
  ],
  "risk_adjusted_picks": [
    {"rank": 1, "name": "Gilead Sciences", "symbol": "GILD", "sector": "stocks", "confidence": 8.9, "risk_score": 3, "risk_adjusted_score": 8.0, "recommendation": "buy", "reasoning": "Low valuation plus a near-term earnings catalyst offers strong asymmetry for moderate risk.", "position_size": "10%", "entry_price": 132.69, "stop_loss": 124.0, "target_12m": 152.0, "risk_reward_ratio": 2.2},
    {"rank": 2, "name": "Johnson & Johnson", "symbol": "JNJ", "sector": "stocks", "confidence": 8.6, "risk_score": 3, "risk_adjusted_score": 7.7, "recommendation": "buy", "reasoning": "Defensive cash-flow quality and oversold entry profile fit a volatile macro backdrop.", "position_size": "9%", "entry_price": 224.2, "stop_loss": 211.0, "target_12m": 248.0, "risk_reward_ratio": 1.8},
    {"rank": 3, "name": "Amgen", "symbol": "AMGN", "sector": "stocks", "confidence": 8.4, "risk_score": 3, "risk_adjusted_score": 7.5, "recommendation": "buy", "reasoning": "Post-results reset and manufacturing investment news support medium-term confidence.", "position_size": "8%", "entry_price": 323.85, "stop_loss": 301.0, "target_12m": 365.0, "risk_reward_ratio": 1.8},
    {"rank": 4, "name": "SPDR Gold Shares", "symbol": "GLD", "sector": "materials", "confidence": 8.2, "risk_score": 3, "risk_adjusted_score": 7.3, "recommendation": "buy", "reasoning": "GLD remains an efficient hedge while geopolitical and inflation risks are elevated.", "position_size": "8%", "entry_price": 414.71, "stop_loss": 392.0, "target_12m": 460.0, "risk_reward_ratio": 2.0},
    {"rank": 5, "name": "VanEck Gold Miners ETF", "symbol": "GDX", "sector": "materials", "confidence": 8.0, "risk_score": 4, "risk_adjusted_score": 6.8, "recommendation": "buy", "reasoning": "Miners provide leveraged upside to sustained bullion strength but with higher volatility.", "position_size": "6%", "entry_price": 85.65, "stop_loss": 77.0, "target_12m": 102.0, "risk_reward_ratio": 1.9},
    {"rank": 6, "name": "NVIDIA", "symbol": "NVDA", "sector": "stocks", "confidence": 8.1, "risk_score": 5, "risk_adjusted_score": 6.6, "recommendation": "hold", "reasoning": "AI demand is strong, but May 20 earnings and China/export uncertainty raise event risk.", "position_size": "7%", "entry_price": 198.48, "stop_loss": 182.0, "target_12m": 245.0, "risk_reward_ratio": 2.8},
    {"rank": 7, "name": "Meta Platforms", "symbol": "META", "sector": "stocks", "confidence": 7.8, "risk_score": 4, "risk_adjusted_score": 6.6, "recommendation": "buy", "reasoning": "Attractive PEG with improved entry profile offsets near-term ad and macro noise.", "position_size": "6%", "entry_price": 610.41, "stop_loss": 560.0, "target_12m": 700.0, "risk_reward_ratio": 1.8},
    {"rank": 8, "name": "Bank of America", "symbol": "BAC", "sector": "stocks", "confidence": 7.7, "risk_score": 4, "risk_adjusted_score": 6.5, "recommendation": "buy", "reasoning": "Low forward valuation and uptrend quality support steady upside in a stable-rate base case.", "position_size": "4%", "entry_price": 52.19, "stop_loss": 48.0, "target_12m": 61.0, "risk_reward_ratio": 2.1},
    {"rank": 9, "name": "JPMorgan Chase", "symbol": "JPM", "sector": "stocks", "confidence": 7.6, "risk_score": 4, "risk_adjusted_score": 6.4, "recommendation": "buy", "reasoning": "High-quality balance sheet and earnings resilience justify core financial exposure.", "position_size": "4%", "entry_price": 307.65, "stop_loss": 286.0, "target_12m": 350.0, "risk_reward_ratio": 2.0},
    {"rank": 10, "name": "Goldman Sachs", "symbol": "GS", "sector": "stocks", "confidence": 7.4, "risk_score": 4, "risk_adjusted_score": 6.2, "recommendation": "hold", "reasoning": "Strong trend and solid valuation are balanced by cyclical sensitivity to market swings.", "position_size": "3%", "entry_price": 903.27, "stop_loss": 840.0, "target_12m": 1010.0, "risk_reward_ratio": 1.7},
    {"rank": 11, "name": "Ethereum", "symbol": "ETH", "sector": "crypto", "confidence": 7.3, "risk_score": 5, "risk_adjusted_score": 5.8, "recommendation": "buy", "reasoning": "ETH offers better risk-adjusted setup than BTC with lower RSI and robust liquidity.", "position_size": "7%", "entry_price": 2372.77, "stop_loss": 2090.0, "target_12m": 3050.0, "risk_reward_ratio": 2.4},
    {"rank": 12, "name": "Occidental Petroleum", "symbol": "OXY", "sector": "stocks", "confidence": 6.9, "risk_score": 5, "risk_adjusted_score": 5.4, "recommendation": "hold", "reasoning": "Oil-beta upside is real, but headline gaps and leadership transition keep risk elevated.", "position_size": "2%", "entry_price": 60.27, "stop_loss": 54.0, "target_12m": 72.0, "risk_reward_ratio": 1.9}
  ],
  "historical_accuracy": {
    "previous_date": "2026-05-05",
    "calls_made": 12,
    "calls_correct": 7,
    "accuracy_pct": 58.3,
    "notable": "Prior cycle showed strongest hit-rate in defensive healthcare and gold-linked calls."
  },
  "warnings": [
    "Geopolitical headlines can gap oil, equities, and crypto outside normal risk models.",
    "Event concentration risk: GILD (May 7) and NVDA (May 20) can materially change positioning needs.",
    "Tariff-policy updates can rapidly shift inflation and sector leadership assumptions."
  ],
  "strategy_summary": "For a moderate profile, the best current mix is quality defensives plus selective AI and controlled commodity hedges, with limited crypto beta. Keep cash optionality and tighten risk controls around earnings and geopolitical headlines."
}

report_data = {
  "brand": "Tododeia",
  "creator": "@soyenriquerocha",
  "generated_at": "2026-05-05T03:53:48Z",
  "risk_profile": strategy["risk_profile"],
  "executive_summary": strategy["strategy_summary"],
  "macro_environment": strategy["macro_environment"],
  "portfolio_allocation": strategy["portfolio_allocation"],
  "cross_sector_insights": strategy["cross_sector_insights"],
  "risk_adjusted_picks": strategy["risk_adjusted_picks"],
  "historical_accuracy": strategy["historical_accuracy"],
  "warnings": strategy["warnings"],
  "sectors": sectors
}

(workspace / "dashboard/public/data").mkdir(parents=True, exist_ok=True)
(workspace / "output/history").mkdir(parents=True, exist_ok=True)

with open(workspace / "dashboard/public/data/report.json", "w") as f:
  json.dump(report_data, f, indent=2)

history_path = workspace / "output/history/2026-05-05.json"
with open(history_path, "w") as f:
  json.dump(report_data, f, indent=2)

all_history = sorted((workspace / "output/history").glob("*.json"))
if len(all_history) > 30:
  for old in all_history[:-30]:
    old.unlink(missing_ok=True)

print("saved", history_path.name, "history_files", len(sorted((workspace / "output/history").glob("*.json"))))
