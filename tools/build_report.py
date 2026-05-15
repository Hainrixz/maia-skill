#!/usr/bin/env python3
"""Build and save Tododeia report.json and history for May 5, 2026."""
import json, os

report = {
  "brand": "Tododeia",
  "creator": "@soyenriquerocha",
  "generated_at": "2026-05-05T03:15:07Z",
  "risk_profile": "moderate",
  "executive_summary": "F&G recovered to 50 Neutral from 29 Fear in 5 days, signaling capitulation exhaustion — healthcare sector shows unprecedented simultaneous oversold sweep (AMGN, GILD, JNJ, REGN all RSI<35) creating a rare multi-stock defensive entry. NFLX at RSI 18.7 (most extreme since March 2020) with 55% FCF margin and a $25B buyback offers asymmetric recovery as post-earnings selling pressure exhausts.",
  "macro_environment": {
    "summary": "S&P 500 at 7,200 consolidating after Monday pullback (-0.41%) from record highs as Iran-US conflict escalates — US sank Iranian boats in Hormuz and oil holds above $100/barrel. F&G snapped back to 50 Neutral from 29 Fear in just 5 days as institutional buyers re-entered oversold positions; no US-China trade deal has been confirmed despite ongoing negotiations.",
    "interest_rate_outlook": "stable",
    "inflation_outlook": "rising",
    "geopolitical_risk": "high",
    "key_factors": [
      "Iran-US tensions: US sank Iranian boats in Hormuz Strait — oil above $100/barrel structural floor",
      "F&G recovered to 50 Neutral from Fear 29 in 5 days — sentiment shift favoring oversold re-entry",
      "No US-China trade deal confirmed — tariff headwinds persist for multinational revenue",
      "NFLX $25B buyback authorization supports floor; analyst Strong Buy consensus PT $119 (+31% upside)",
      "NVDA zero China market share from export controls — domestic AI capex thesis intact but China revenue $0"
    ]
  },
  "portfolio_allocation": {"crypto": 8, "stocks": 58, "materials": 12, "cash": 22},
  "cross_sector_insights": [
    {
      "insight": "Healthcare simultaneous oversold sweep: AMGN RSI 29.2, GILD RSI 30.6, JNJ RSI 27.2, REGN RSI 34.7 — all excellent-oversold at the same time",
      "implication": "Sector rotation into defensive healthcare hedges against continued tariff/geopolitical volatility while capturing mean-reversion upside — 4-pick basket diversifies within the sector"
    },
    {
      "insight": "Gold pulled back from $4,635 (Apr 30) to $4,520 on Iran ceasefire speculation then reversed as US-Iran hostilities escalated with US sinking Iranian boats",
      "implication": "GLD at RSI 28.4 is a better entry than Apr 30 — structural Iran war + USD weakness tailwind is intact; GDX at RSI 26.3 adds miners catch-up trade with 1.5x leverage to spot gold"
    },
    {
      "insight": "NVDA revealed zero China market share from export controls — a permanent revenue headwind — while earnings confirmed for May 20",
      "implication": "Reduce NVDA position sizing from 8% to 5% vs prior sessions; domestic AI capex narrative intact but China risk reprices ceiling — maintain buy with tighter stop at $182"
    }
  ],
  "risk_adjusted_picks": [
    {"rank": 1, "name": "Netflix", "symbol": "NFLX", "sector": "consumer discretionary", "confidence": 8, "risk_score": 4, "risk_adjusted_score": 6.8, "recommendation": "buy", "reasoning": "RSI 18.7 most extreme oversold in screener since Mar 2020 — $25B buyback floor — FCF 55.4% best in consumer tech — earnings risk cleared 19 days ago", "position_size": "8%", "entry_price": 91.02, "stop_loss": 80.0, "target_12m": 119.0, "risk_reward_ratio": 2.5},
    {"rank": 2, "name": "META Platforms", "symbol": "META", "sector": "technology", "confidence": 8, "risk_score": 4, "risk_adjusted_score": 6.8, "recommendation": "buy", "reasoning": "PEG 0.93 sub-1 for +33.1% revenue growth — RSI 33.5 oversold — binary cleared 6d ago — analyst avg PT $836 = +37% upside", "position_size": "7%", "entry_price": 610.41, "stop_loss": 540.0, "target_12m": 836.0, "risk_reward_ratio": 3.9},
    {"rank": 3, "name": "Johnson & Johnson", "symbol": "JNJ", "sector": "healthcare", "confidence": 7, "risk_score": 2, "risk_adjusted_score": 6.4, "recommendation": "buy", "reasoning": "Safest oversold: RSI 27.2 — 71d to earnings removes binary — 3.5% dividend defensive floor — MedTech tariff resilience", "position_size": "7%", "entry_price": 224.20, "stop_loss": 212.0, "target_12m": 265.0, "risk_reward_ratio": 2.3},
    {"rank": 4, "name": "SPDR Gold Shares", "symbol": "GLD", "sector": "materials", "confidence": 7, "risk_score": 3, "risk_adjusted_score": 6.1, "recommendation": "buy", "reasoning": "RSI 28.4 deeper oversold than Apr 30 entry ($435) — better entry at $414 — Iran war + USD weakness structural tailwind confirmed", "position_size": "7%", "entry_price": 414.71, "stop_loss": 385.0, "target_12m": 480.0, "risk_reward_ratio": 1.9},
    {"rank": 5, "name": "Regeneron Pharmaceuticals", "symbol": "REGN", "sector": "healthcare", "confidence": 7, "risk_score": 3, "risk_adjusted_score": 6.1, "recommendation": "buy", "reasoning": "Beat4 confirmed 6d ago — Dupixent +19% revenue — RSI 34.7 oversold — 60+ days to next earnings removes binary", "position_size": "6%", "entry_price": 709.21, "stop_loss": 640.0, "target_12m": 860.0, "risk_reward_ratio": 2.4},
    {"rank": 6, "name": "Mastercard", "symbol": "MA", "sector": "payments", "confidence": 7, "risk_score": 3, "risk_adjusted_score": 6.1, "recommendation": "buy", "reasoning": "Beat4 EPS+21% sell-the-news dip — RSI 45.4 near support — analyst consensus PT $649 = 28% upside from $504", "position_size": "6%", "entry_price": 504.74, "stop_loss": 470.0, "target_12m": 649.0, "risk_reward_ratio": 4.0},
    {"rank": 7, "name": "Amgen", "symbol": "AMGN", "sector": "healthcare", "confidence": 7, "risk_score": 4, "risk_adjusted_score": 5.8, "recommendation": "buy", "reasoning": "Beat4 confirmed (EPS $5.15 vs est $4.77) — RSI 29.2 post-earnings oversold from $348 — MariTide Phase III GLP-1 H2 2026 catalyst", "position_size": "6%", "entry_price": 323.85, "stop_loss": 295.0, "target_12m": 400.0, "risk_reward_ratio": 2.6},
    {"rank": 8, "name": "Gilead Sciences", "symbol": "GILD", "sector": "healthcare", "confidence": 7, "risk_score": 4, "risk_adjusted_score": 5.8, "recommendation": "buy half", "reasoning": "PEG 0.37 deepest value in screener — RSI 30.6 oversold — EARNINGS MAY 7 (est EPS $1.89) — half-position only until results", "position_size": "4%", "entry_price": 132.69, "stop_loss": 120.0, "target_12m": 165.0, "risk_reward_ratio": 2.4},
    {"rank": 9, "name": "NVIDIA", "symbol": "NVDA", "sector": "technology", "confidence": 7, "risk_score": 4, "risk_adjusted_score": 5.8, "recommendation": "buy", "reasoning": "PEG 0.63 best in Mag7 for 73.2% revenue growth — RSI 52 fair entry — earnings May 20 = 15-day runway — zero China share headwind priced in", "position_size": "5%", "entry_price": 198.48, "stop_loss": 182.0, "target_12m": 269.0, "risk_reward_ratio": 3.7},
    {"rank": 10, "name": "VanEck Gold Miners ETF", "symbol": "GDX", "sector": "materials", "confidence": 7, "risk_score": 4, "risk_adjusted_score": 5.8, "recommendation": "buy", "reasoning": "RSI 26.3 extreme oversold — miners trading 15-20% below spot gold NAV — 1.5x operating leverage catch-up trade", "position_size": "5%", "entry_price": 85.65, "stop_loss": 78.0, "target_12m": 110.0, "risk_reward_ratio": 2.8},
    {"rank": 11, "name": "Ethereum", "symbol": "ETH-USD", "sector": "crypto", "confidence": 7, "risk_score": 5, "risk_adjusted_score": 5.5, "recommendation": "buy", "reasoning": "RSI 57 healthy — Apr 30 pick confirmed +4.8% gain — Pectra upgrade narrative and GENIUS Act stablecoin bill provide tailwind", "position_size": "5%", "entry_price": 2372.77, "stop_loss": 2050.0, "target_12m": 3200.0, "risk_reward_ratio": 2.6},
    {"rank": 12, "name": "Goldman Sachs", "symbol": "GS", "sector": "financials", "confidence": 6, "risk_score": 3, "risk_adjusted_score": 5.1, "recommendation": "buy", "reasoning": "Beat4 — RSI 48 near support — F&G=50 Neutral recovery boosts IB deal sentiment — 70-day earnings runway", "position_size": "4%", "entry_price": 903.27, "stop_loss": 840.0, "target_12m": 1080.0, "risk_reward_ratio": 2.7}
  ],
  "historical_accuracy": {
    "previous_date": "2026-04-30",
    "calls_made": 12,
    "calls_correct": 5,
    "accuracy_pct": 42,
    "notable": "Winners: LLY +4.6% (guidance upgrade), ETH +4.8% (Pectra narrative), MRK +2.5%, GILD +1.0%, REGN +0.8% — Losers: AMGN -7.0% (Guggenheim PT cut despite beat), GLD -4.8% (ceasefire speculation), NFLX -2.2% (continued pressure), MA/OXY/NVDA -0.5 to -1.3%"
  },
  "warnings": [
    "BINARY EVENT: GILD earnings May 7 — analyst est EPS $1.89 — half-position only until results confirm",
    "BINARY EVENT: COIN Coinbase earnings May 7 — avoid new entries",
    "UPCOMING BINARY: NVDA earnings May 20 — 15-day runway — tighten stop to $182 as date approaches",
    "CASH 22% elevated: Deploy after GILD/COIN report May 7 — add to GLD/GDX on Iran escalation",
    "NVDA RISK: Zero China market share from export controls — permanent revenue headwind reprices ceiling"
  ],
  "sectors": {
    "crypto": {
      "sector": "crypto",
      "timestamp": "2026-05-05T03:15:07Z",
      "sector_summary": "Bitcoin reclaimed $80K for first time since January driven by GENIUS Act stablecoin legislation progress and institutional ETF inflows; briefly knocked to $79K by Iran missile report before recovering to $80,794. Ethereum at $2,373 (+4.8% from Apr 30 entry) with Pectra upgrade narrative providing technical tailwind above BTC's momentum.",
      "sector_outlook": "neutral",
      "top_pick": "ETH-USD",
      "top_pick_reasoning": "ETH RSI 57 is healthier than BTC RSI 69.3 approaching overbought — Apr 30 pick confirmed the thesis with +4.8% gain — Pectra upgrade near-term catalyst",
      "assets": [
        {
          "name": "Bitcoin", "symbol": "BTC-USD",
          "current_price": "$80,794", "change_24h": "+0.62%", "change_7d": "+8.2%",
          "change_30d": "+12.5%", "ytd_change": "-18.3%",
          "week_52_high": "$109,000", "week_52_low": "$52,000",
          "market_cap": "$1.59T", "volume_24h": "$42B",
          "sentiment": "bullish", "social_sentiment": "bullish", "social_buzz": "high",
          "confidence": 6, "source_agreement": "medium",
          "key_news": [
            "Bitcoin reclaims $80K for first time since January on GENIUS Act stablecoin bill progress",
            "Iran missile report briefly knocked BTC to $79K before fast recovery — safe-haven bid intact"
          ],
          "social_highlights": ["ETF inflows accelerating — institutional re-accumulation signal"],
          "recommendation": "hold",
          "reasoning": "RSI 69.3 approaching overbought — hold existing positions but wait for RSI <60 before adding; GENIUS Act is structural bullish catalyst"
        },
        {
          "name": "Ethereum", "symbol": "ETH-USD",
          "current_price": "$2,373", "change_24h": "+0.32%", "change_7d": "+5.1%",
          "change_30d": "+8.7%", "ytd_change": "-28.4%",
          "week_52_high": "$4,100", "week_52_low": "$1,450",
          "market_cap": "$285B", "volume_24h": "$18B",
          "sentiment": "bullish", "social_sentiment": "bullish", "social_buzz": "medium",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "Ethereum +4.8% since Apr 30 pick — best performer from last session confirming thesis",
            "Pectra upgrade narrative building momentum in developer community"
          ],
          "social_highlights": ["ETH/BTC ratio improving — ETH outperforming BTC on weekly basis"],
          "recommendation": "buy",
          "reasoning": "RSI 57 healthy entry — confirmed Apr 30 thesis with +4.8% — Pectra upgrade + GENIUS Act tailwind; better risk/reward than BTC at RSI 69"
        },
        {
          "name": "Solana", "symbol": "SOL-USD",
          "current_price": "$84.59", "change_24h": "-0.8%", "change_7d": "+2.3%",
          "change_30d": "+5.1%", "ytd_change": "-62.4%",
          "week_52_high": "$295", "week_52_low": "$60",
          "market_cap": "$39B", "volume_24h": "$3.2B",
          "sentiment": "neutral", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 5, "source_agreement": "medium",
          "key_news": [
            "SOL RSI 46.1 fair — downtrend intact — meme coin activity subdued",
            "No major protocol catalysts near term vs ETH Pectra narrative"
          ],
          "social_highlights": ["SOL social buzz at multi-month lows — ETH/BTC dominating crypto conversation"],
          "recommendation": "hold",
          "reasoning": "RSI 46.1 neutral — downtrend intact — no clear catalyst vs ETH Pectra narrative; hold existing, no new entries"
        }
      ]
    },
    "stocks": {
      "sector": "stocks",
      "timestamp": "2026-05-05T03:15:07Z",
      "sector_summary": "S&P 500 at 7,200 consolidating after Monday -0.41% on Iran escalation; Nasdaq outperforming (+0.19%) as F&G snapped back to 50 Neutral. Healthcare sector shows unprecedented simultaneous oversold sweep (AMGN/GILD/JNJ/REGN all RSI<35) while NFLX reaches RSI 18.7 — most extreme oversold reading in the entire 55-ticker screener.",
      "sector_outlook": "neutral",
      "top_pick": "NFLX",
      "top_pick_reasoning": "RSI 18.7 most extreme oversold in screener — $25B buyback authorized — FCF 55.4% best in consumer tech — analyst Strong Buy PT $119 (+31% upside)",
      "assets": [
        {
          "name": "Netflix", "symbol": "NFLX",
          "current_price": "$91.02", "change_24h": "-1.2%", "change_7d": "-8.4%",
          "change_30d": "-32.1%", "ytd_change": "-41.3%",
          "week_52_high": "$1,065", "week_52_low": "$80",
          "market_cap": "$39B", "volume_24h": "$2.8B",
          "sentiment": "bearish", "social_sentiment": "neutral", "social_buzz": "high",
          "confidence": 8, "source_agreement": "high",
          "key_news": [
            "NFLX Q1 Apr 16 earnings guidance disappointed — Warner Bros acquisition failed; $25B buyback authorized",
            "Analyst Strong Buy consensus PT $119 = +31% upside; Erste Group lone Hold downgrade citing slowing growth"
          ],
          "social_highlights": ["Retail capitulation signal — short interest at 3-year high suggesting fuel for short squeeze"],
          "recommendation": "buy",
          "reasoning": "RSI 18.7 extreme oversold — most extreme since March 2020 — $25B buyback + FCF 55.4% + analyst PT $119 — earnings cleared 19 days ago",
          "technicals": {"trend": "downtrend", "rsi": 18.7, "macd": "bearish", "key_support": 80.0, "key_resistance": 108.0, "entry_quality": "excellent — most oversold in screener"},
          "valuation": {"forward_pe": 23.70, "peg": 1.34, "verdict": "reasonable with $25B buyback and 55% FCF exceptional for growth"},
          "fundamentals": {"revenue_growth": "+16.2% YoY", "fcf_margin": "55.4%", "verdict": "best FCF in consumer tech; beat2 streak; $25B buyback authorized"}
        },
        {
          "name": "META Platforms", "symbol": "META",
          "current_price": "$610.41", "change_24h": "+0.6%", "change_7d": "-6.2%",
          "change_30d": "-18.9%", "ytd_change": "-12.4%",
          "week_52_high": "$796", "week_52_low": "$450",
          "market_cap": "$1.54T", "volume_24h": "$28B",
          "sentiment": "neutral", "social_sentiment": "mixed", "social_buzz": "high",
          "confidence": 8, "source_agreement": "high",
          "key_news": [
            "META ad spend headwinds: Iran war caused consumer budget shift away from digital ads — Zuckerberg acknowledged trajectory change",
            "Analyst consensus Strong Buy avg PT $836 = +37% upside; 8,000 layoffs alongside AI infrastructure investment"
          ],
          "social_highlights": ["META AI (Llama) organic usage growth accelerating — monetization runway extends price target ceiling"],
          "recommendation": "buy",
          "reasoning": "PEG 0.93 sub-1 for +33.1% revenue growth rare at $1.5T scale — RSI 33.5 oversold — analyst avg PT $836 = +37% — binary cleared 6 days ago",
          "technicals": {"trend": "downtrend", "rsi": 33.5, "macd": "bearish", "key_support": 560.0, "key_resistance": 680.0, "entry_quality": "excellent — oversold, binary cleared"},
          "valuation": {"forward_pe": 16.87, "peg": 0.93, "verdict": "undervalued — PEG sub-1 for hypergrowth at scale"},
          "fundamentals": {"revenue_growth": "+33.1% YoY", "fcf_margin": "11.9%", "verdict": "Llama AI monetization; beat3; analyst consensus PT $836"}
        },
        {
          "name": "Gilead Sciences", "symbol": "GILD",
          "current_price": "$132.69", "change_24h": "+0.2%", "change_7d": "+1.5%",
          "change_30d": "-4.8%", "ytd_change": "-6.2%",
          "week_52_high": "$148", "week_52_low": "$88",
          "market_cap": "$168B", "volume_24h": "$3.1B",
          "sentiment": "neutral", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "GILD earnings May 7 — analyst est EPS $1.89 / revenue $6.89B — Citigroup Buy PT $165",
            "HIV franchise priority review + Arcellx cell therapy collaboration are key catalysts — avg analyst PT $158 vs current $132"
          ],
          "social_highlights": ["GILD has lowest PEG (0.37) in entire 55-ticker screener — value investors accumulating"],
          "recommendation": "buy half",
          "reasoning": "PEG 0.37 deepest value in entire screener — RSI 30.6 oversold — EARNINGS IN 2 DAYS (May 7 est EPS $1.89) — half-position only",
          "technicals": {"trend": "mixed", "rsi": 30.6, "macd": "bearish", "key_support": 120.0, "key_resistance": 148.0, "entry_quality": "excellent — oversold, pre-earnings"},
          "valuation": {"forward_pe": 13.80, "peg": 0.37, "verdict": "deepest PEG value in screener — analyst avg PT $158 = +19% upside"},
          "fundamentals": {"revenue_growth": "+4.7% YoY", "fcf_margin": "25.6%", "verdict": "beat4 streak; HIV/oncology tariff moat; Arcellx collaboration"}
        },
        {
          "name": "Johnson & Johnson", "symbol": "JNJ",
          "current_price": "$224.20", "change_24h": "-0.3%", "change_7d": "-2.1%",
          "change_30d": "-6.3%", "ytd_change": "-9.5%",
          "week_52_high": "$267", "week_52_low": "$210",
          "market_cap": "$538B", "volume_24h": "$6.8B",
          "sentiment": "neutral", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "JNJ RSI 27.2 deeply oversold — 71 days to next earnings removes binary risk entirely",
            "MedTech + pharma diversification provides tariff resilience — 3.5% dividend yield provides income floor"
          ],
          "social_highlights": ["JNJ accumulation at multi-year support — institutional buy signals increasing"],
          "recommendation": "buy",
          "reasoning": "Safest oversold: RSI 27.2 — 71d to earnings removes binary — 3.5% dividend floor — MedTech tariff resilience",
          "technicals": {"trend": "mixed", "rsi": 27.2, "macd": "bearish", "key_support": 212.0, "key_resistance": 252.0, "entry_quality": "excellent — deeply oversold"},
          "valuation": {"forward_pe": 17.64, "peg": 2.95, "verdict": "fair for defensive healthcare compounder with 3.5% dividend"},
          "fundamentals": {"revenue_growth": "+9.9% YoY", "fcf_margin": "13.0%", "verdict": "MedTech fortress; beat3; 71d earnings runway; 3.5% dividend"}
        },
        {
          "name": "Amgen", "symbol": "AMGN",
          "current_price": "$323.85", "change_24h": "-0.1%", "change_7d": "-7.0%",
          "change_30d": "-10.2%", "ytd_change": "-12.8%",
          "week_52_high": "$395", "week_52_low": "$260",
          "market_cap": "$172B", "volume_24h": "$4.2B",
          "sentiment": "neutral", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "AMGN Q1 beat: EPS $5.15 vs est $4.77 (+8% beat); revenue $8.62B — beat4 streak confirmed",
            "Guggenheim trimmed PT from $351 to $340 Neutral despite beat — stock -7% from $348 entry to $323"
          ],
          "social_highlights": ["Post-earnings RSI oversold historically resets within 10-15 days — MariTide Phase III H2 catalyst upcoming"],
          "recommendation": "buy",
          "reasoning": "Beat4 confirmed (EPS $5.15 vs $4.77) — binary cleared 5d ago — RSI 29.2 post-earnings oversold from $348 — MariTide GLP-1 H2 2026 catalyst",
          "technicals": {"trend": "mixed", "rsi": 29.2, "macd": "bearish", "key_support": 295.0, "key_resistance": 385.0, "entry_quality": "excellent — oversold, post-earnings"},
          "valuation": {"forward_pe": 13.79, "peg": 2.17, "verdict": "fair for large-cap biotech with GLP-1 pipeline catalyst"},
          "fundamentals": {"revenue_growth": "+5.8% YoY", "fcf_margin": "20.0%", "verdict": "beat4 confirmed; MariTide Phase III H2 2026 GLP-1 catalyst; US manufacturing moat"}
        },
        {
          "name": "Regeneron Pharmaceuticals", "symbol": "REGN",
          "current_price": "$709.21", "change_24h": "+0.4%", "change_7d": "+0.8%",
          "change_30d": "-8.3%", "ytd_change": "-15.2%",
          "week_52_high": "$975", "week_52_low": "$630",
          "market_cap": "$74B", "volume_24h": "$1.8B",
          "sentiment": "neutral", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "REGN Q1 beat4 confirmed 6 days ago — Dupixent +19% revenue growth $3.81B continuing dominance",
            "Eylea HD maintains market share despite biosimilar pressure — pipeline diversification reduces risk"
          ],
          "social_highlights": ["REGN recovering from oversold — Apr 30 pick +0.8% confirming thesis intact"],
          "recommendation": "buy",
          "reasoning": "Beat4 confirmed 6d ago — Dupixent +19% revenue — RSI 34.7 oversold — 60+ days to next earnings",
          "technicals": {"trend": "mixed", "rsi": 34.7, "macd": "bearish", "key_support": 640.0, "key_resistance": 800.0, "entry_quality": "excellent — oversold, binary cleared"},
          "valuation": {"forward_pe": 13.18, "peg": 1.43, "verdict": "reasonable for durable biotech with Dupixent growth"},
          "fundamentals": {"revenue_growth": "+19.0% YoY", "fcf_margin": "21.9%", "verdict": "Dupixent durable; beat4 confirmed 6d ago; 60d+ earnings runway"}
        },
        {
          "name": "Mastercard", "symbol": "MA",
          "current_price": "$504.74", "change_24h": "-0.1%", "change_7d": "-0.5%",
          "change_30d": "-5.8%", "ytd_change": "-3.2%",
          "week_52_high": "$567", "week_52_low": "$431",
          "market_cap": "$468B", "volume_24h": "$4.1B",
          "sentiment": "neutral", "social_sentiment": "neutral", "social_buzz": "medium",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "MA Q1 beat: EPS +21% on Apr 30 — stock -3.4% sell-the-news to $504; cross-border travel +18%",
            "Analyst consensus PT $649 = 28.6% upside from current level; buy-the-dip signals accumulating"
          ],
          "social_highlights": ["MA sell-the-news dips historically recover within 4-8 weeks — support at $475 strong"],
          "recommendation": "buy",
          "reasoning": "Beat4 EPS+21% sell-the-news dip — RSI 45.4 near support — analyst consensus PT $649 = 28% upside",
          "technicals": {"trend": "downtrend", "rsi": 45.4, "macd": "neutral", "key_support": 475.0, "key_resistance": 545.0, "entry_quality": "good — post-earnings near support"},
          "valuation": {"forward_pe": 22.19, "peg": 1.59, "verdict": "fair for quality compounder with $649 analyst target"},
          "fundamentals": {"revenue_growth": "+15.8% YoY", "fcf_margin": "47.6%", "verdict": "beat4 confirmed; cross-border +18%; analyst PT $649"}
        },
        {
          "name": "NVIDIA", "symbol": "NVDA",
          "current_price": "$198.48", "change_24h": "-0.4%", "change_7d": "-1.1%",
          "change_30d": "+8.3%", "ytd_change": "-5.6%",
          "week_52_high": "$242", "week_52_low": "$86",
          "market_cap": "$4.85T", "volume_24h": "$52B",
          "sentiment": "bullish", "social_sentiment": "bullish", "social_buzz": "high",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "NVDA CEO Jensen Huang: zero China market share from export controls — permanent headwind vs ~$5-8B prior annual revenue",
            "Earnings confirmed May 20 — analyst Strong Buy consensus PT $269 = +36% upside; Blackwell GPU ramp intact"
          ],
          "social_highlights": ["AI capex supercycle intact domestically — Microsoft/Google/Meta confirmed increased NVDA orders in recent earnings"],
          "recommendation": "buy",
          "reasoning": "PEG 0.63 best in Mag7 for 73.2% growth — RSI 52 fair — earnings May 20 = 15-day runway — China zero-share headwind priced in",
          "technicals": {"trend": "uptrend", "rsi": 52.0, "macd": "neutral", "key_support": 182.0, "key_resistance": 225.0, "entry_quality": "fair"},
          "valuation": {"forward_pe": 17.66, "peg": 0.63, "verdict": "best PEG in Mag7 — China revenue permanently $0 reprices ceiling"},
          "fundamentals": {"revenue_growth": "+73.2% YoY", "fcf_margin": "26.9%", "verdict": "Blackwell ramp; beat4 streak; AI capex supercycle; PT $269"}
        },
        {
          "name": "Goldman Sachs", "symbol": "GS",
          "current_price": "$903.27", "change_24h": "+0.8%", "change_7d": "+2.1%",
          "change_30d": "+5.4%", "ytd_change": "+11.2%",
          "week_52_high": "$985", "week_52_low": "$612",
          "market_cap": "$295B", "volume_24h": "$2.9B",
          "sentiment": "bullish", "social_sentiment": "bullish", "social_buzz": "medium",
          "confidence": 6, "source_agreement": "high",
          "key_news": [
            "GS beat4 streak intact — IB pipeline recovering as F&G improved from 29 Fear to 50 Neutral in 5 days",
            "F&G=50 Neutral recovery historically correlates with IB activity rebound — GS positioned for deal reopening"
          ],
          "social_highlights": ["Dealmaking revival narrative building — GS leading financials recovery"],
          "recommendation": "buy",
          "reasoning": "Beat4 — RSI 48 near support — F&G=50 recovery boosts IB sentiment — 70-day earnings runway",
          "technicals": {"trend": "uptrend", "rsi": 48.1, "macd": "neutral", "key_support": 850.0, "key_resistance": 980.0, "entry_quality": "good — near support"},
          "valuation": {"forward_pe": 13.82, "peg": 1.43, "verdict": "reasonable for top IB in dealmaking recovery"},
          "fundamentals": {"revenue_growth": "+14.5% YoY", "fcf_margin": "N/A", "verdict": "beat4; IB rebound; F&G recovery tailwind; 70d earnings runway"}
        }
      ]
    },
    "materials": {
      "sector": "materials",
      "timestamp": "2026-05-05T03:15:07Z",
      "sector_summary": "Gold pulled back to $4,520-4,580/oz from $4,635 highs (Apr 30) on Iran ceasefire speculation before reversing as US sank Iranian boats in Hormuz — structural safe-haven demand remains intact with oil above $100/barrel. Gold miners (GDX) at extreme RSI 26.3 oversold are trading 15-20% below NAV vs spot gold, creating a catch-up trade with 1.5x operating leverage.",
      "sector_outlook": "neutral",
      "top_pick": "GLD",
      "top_pick_reasoning": "RSI 28.4 deeply oversold at $414 — Iran-US Hormuz escalation + USD weakness structural tailwind intact — better entry than Apr 30 $435",
      "assets": [
        {
          "name": "SPDR Gold Shares", "symbol": "GLD",
          "current_price": "$414.71", "change_24h": "+0.4%", "change_7d": "-4.8%",
          "change_30d": "+3.2%", "ytd_change": "+18.6%",
          "week_52_high": "$436", "week_52_low": "$224",
          "market_cap": "$118B", "volume_24h": "$2.1B",
          "sentiment": "bullish", "social_sentiment": "bullish", "social_buzz": "medium",
          "confidence": 7, "source_agreement": "high",
          "key_news": [
            "Gold at one-month low on May 4 on Iran ceasefire speculation — recovered as US sank Iranian boats in Hormuz",
            "Inflation fears from oil above $100/barrel capping gold recovery despite USD weakness"
          ],
          "social_highlights": ["Central bank gold purchases remain at record pace — institutional accumulation signal"],
          "recommendation": "buy",
          "reasoning": "RSI 28.4 deeply oversold — better entry than Apr 30 $435 — Iran war + USD weakness structural tailwind confirmed by US-Iran naval skirmish"
        },
        {
          "name": "VanEck Gold Miners ETF", "symbol": "GDX",
          "current_price": "$85.65", "change_24h": "+0.6%", "change_7d": "-5.2%",
          "change_30d": "+8.1%", "ytd_change": "+42.3%",
          "week_52_high": "$98", "week_52_low": "$32",
          "market_cap": "$20B", "volume_24h": "$0.9B",
          "sentiment": "bullish", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 7, "source_agreement": "medium",
          "key_news": [
            "GDX RSI 26.3 extreme oversold — gold miners trading at significant discount to spot gold NAV",
            "Newmont NEM beat4 confirmed 12d ago with +45.8% revenue — major GDX holding strengthening ETF"
          ],
          "social_highlights": ["Gold miners 15-20% behind spot gold YTD — catch-up trade with 1.5x operating leverage"],
          "recommendation": "buy",
          "reasoning": "RSI 26.3 extreme oversold — miners trading 15-20% below spot gold NAV — NEM beat4 confirms fundamentals — 1.5x leverage catch-up"
        },
        {
          "name": "Crude Oil WTI", "symbol": "CL",
          "current_price": "$102.40", "change_24h": "+0.8%", "change_7d": "-2.1%",
          "change_30d": "+4.3%", "ytd_change": "+28.5%",
          "week_52_high": "$112", "week_52_low": "$68",
          "market_cap": "N/A", "volume_24h": "$28B",
          "sentiment": "bullish", "social_sentiment": "bullish", "social_buzz": "high",
          "confidence": 6, "source_agreement": "medium",
          "key_news": [
            "WTI above $100 — US sank Iranian boats in Hormuz May 4 preventing ceasefire — 94% Hormuz blocked",
            "OXY Occidental earnings May 5 — CEO Vicki Hollub retirement announced; COO Jackson succeeds June 1"
          ],
          "social_highlights": ["Oil structural supply disruption intact — Hormuz 6% normal capacity by May 15 estimate"],
          "recommendation": "hold",
          "reasoning": "WTI $102 structural floor from Hormuz blockage — wait for OXY earnings results before adding energy positions"
        },
        {
          "name": "Newmont Corporation", "symbol": "NEM",
          "current_price": "$108.33", "change_24h": "+0.3%", "change_7d": "-2.4%",
          "change_30d": "+5.7%", "ytd_change": "+38.2%",
          "week_52_high": "$122", "week_52_low": "$40",
          "market_cap": "$96B", "volume_24h": "$1.2B",
          "sentiment": "bullish", "social_sentiment": "neutral", "social_buzz": "low",
          "confidence": 6, "source_agreement": "medium",
          "key_news": [
            "NEM beat4 confirmed 12d ago with +45.8% revenue — largest gold miner benefiting from $4,500+ gold",
            "RSI 38.9 fair — GDX ETF preferred over NEM for lower single-stock risk with same sector exposure"
          ],
          "social_highlights": ["NEM is 11% of GDX — strong NEM results support ETF thesis"],
          "recommendation": "hold",
          "reasoning": "RSI 38.9 fair — NEM beat4 12d ago supports gold miner thesis — GDX preferred for sector exposure with lower concentration risk"
        }
      ]
    }
  }
}

# Save report.json
os.makedirs("dashboard/public/data", exist_ok=True)
with open("dashboard/public/data/report.json", "w") as f:
    json.dump(report, f, indent=2)
print("✓ Saved dashboard/public/data/report.json")

# Save history
os.makedirs("output/history", exist_ok=True)
history = {
    "date": "2026-05-05",
    "generated_at": "2026-05-05T03:15:07Z",
    "risk_profile": "moderate",
    "vix": 18.29,
    "fg": 50,
    "regime": "MIXED",
    "candidates_screened": 35,
    "picks": [
        {"rank": 1, "symbol": "NFLX", "entry": 91.02, "stop": 80.0, "target": 119.0, "confidence": 8, "ras": 6.8},
        {"rank": 2, "symbol": "META", "entry": 610.41, "stop": 540.0, "target": 836.0, "confidence": 8, "ras": 6.8},
        {"rank": 3, "symbol": "JNJ", "entry": 224.20, "stop": 212.0, "target": 265.0, "confidence": 7, "ras": 6.4},
        {"rank": 4, "symbol": "GLD", "entry": 414.71, "stop": 385.0, "target": 480.0, "confidence": 7, "ras": 6.1},
        {"rank": 5, "symbol": "REGN", "entry": 709.21, "stop": 640.0, "target": 860.0, "confidence": 7, "ras": 6.1},
        {"rank": 6, "symbol": "MA", "entry": 504.74, "stop": 470.0, "target": 649.0, "confidence": 7, "ras": 6.1},
        {"rank": 7, "symbol": "AMGN", "entry": 323.85, "stop": 295.0, "target": 400.0, "confidence": 7, "ras": 5.8},
        {"rank": 8, "symbol": "GILD", "entry": 132.69, "stop": 120.0, "target": 165.0, "confidence": 7, "ras": 5.8, "note": "half-position — earnings May 7"},
        {"rank": 9, "symbol": "NVDA", "entry": 198.48, "stop": 182.0, "target": 269.0, "confidence": 7, "ras": 5.8, "note": "earnings May 20"},
        {"rank": 10, "symbol": "GDX", "entry": 85.65, "stop": 78.0, "target": 110.0, "confidence": 7, "ras": 5.8},
        {"rank": 11, "symbol": "ETH-USD", "entry": 2372.77, "stop": 2050.0, "target": 3200.0, "confidence": 7, "ras": 5.5},
        {"rank": 12, "symbol": "GS", "entry": 903.27, "stop": 840.0, "target": 1080.0, "confidence": 6, "ras": 5.1}
    ],
    "historical_accuracy_from_prev": {
        "prev_date": "2026-04-30",
        "correct": 5,
        "total": 12,
        "pct": 42,
        "notable_win": "LLY +4.6% (guidance upgrade), ETH +4.8% (Pectra narrative), MRK +2.5%, GILD +1.0%, REGN +0.8%",
        "notable_miss": "AMGN -7.0% (Guggenheim PT cut despite beat4), GLD -4.8% (ceasefire profit-taking), NFLX -2.2% (continued pressure), MA/OXY/NVDA -0.5 to -1.3%"
    },
    "key_events": {
        "AMGN_earnings": "Beat: EPS 5.15 vs est 4.77; Guggenheim PT cut 351->340 despite beat — stock -7%",
        "NFLX_buyback": "25B stock buyback authorized — analyst Strong Buy PT 119",
        "META_headwinds": "Iran war caused ad spend trajectory change; 8000 layoffs; analyst avg PT 836",
        "gold": "GLD 414.71 pulled back from 435 — Iran-US naval skirmish May 4 maintains structural bid",
        "NVDA_china": "Jensen confirms zero China market share from export controls — permanent headwind",
        "crypto": "BTC reclaims 80K on GENIUS Act; ETH +4.8% from Apr 30 confirms thesis",
        "OXY": "Earnings May 5 pending — CEO Vicki Hollub retirement announced; COO Jackson succeeds"
    }
}
with open("output/history/2026-05-05.json", "w") as f:
    json.dump(history, f, indent=2)
print("✓ Saved output/history/2026-05-05.json")
print(f"Total picks: {len(history['picks'])}")
print(f"Apr30 accuracy: {history['historical_accuracy_from_prev']['pct']}%")
print("Done.")
