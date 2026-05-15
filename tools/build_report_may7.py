#!/usr/bin/env python3
"""Tododeia May 7 2026 — build report.json from MegaAgent output."""
import json, os, glob

REPORT = {
  "brand": "Tododeia",
  "creator": "@soyenriquerocha",
  "generated_at": "2026-05-07T15:25:00Z",
  "risk_profile": "moderate",
  "executive_summary": "The May 7 moderate portfolio is anchored by META's extraordinary Q1 earnings beat and GLD's geopolitical premium as the two highest-conviction, lowest-risk entries, with a 18% materials overweight capturing the gold/silver surge driven by Iran-deal dynamics and a strategic mineral designation. Healthcare oversold plays (JNJ, AMGN) provide defensive yield and mean-reversion upside, while GILD and NVDA are near-term catalyst watches — hold cash until GILD's 4:30 PM earnings call resolves the biotech binary before deploying the final 7% position.",
  "macro_environment": {
    "summary": "Markets on May 7, 2026 are navigating a pivotal geopolitical inflection — Iran peace deal talks are emerging in month 3 of the conflict, creating a counterintuitive scenario where gold surges (+1.55%) while oil crashes (-3.54%) as the market prices in supply normalization but maintains flight-to-quality demand. The MIXED regime (VIX 17.21, Fear & Greed 47) with S&P 500 at 7,376 reflects a market coiled for directional resolution, with semiconductors leading and healthcare lagging into a pharma M&A boom.",
    "interest_rate_outlook": "stable",
    "inflation_outlook": "falling",
    "geopolitical_risk": "high",
    "key_factors": [
      "Iran peace deal talks emerging — oil falling -3.5%, gold paradoxically rising on de-dollarization and strategic mineral demand",
      "GILD earnings binary risk today (4:30 PM EDT) and NVDA earnings May 20 are near-term volatility catalysts",
      "30-year Treasury testing 5% — rising long-end rates create headwind for growth and real estate but support bank NII",
      "META Q1 earnings massive beat (EPS +57% vs estimate) validates RSI-29 oversold entry; healthcare broadly oversold (JNJ, AMGN, MRK all RSI <35)",
      "Digital asset ETP first monthly gain of 2026 in April reversed in early May — crypto decoupling bearishly from equity rally"
    ]
  },
  "portfolio_allocation": {
    "crypto": 12,
    "stocks": 60,
    "materials": 18,
    "cash": 10
  },
  "cross_sector_insights": [
    {
      "insight": "Gold surging (+1.55%) while oil crashes (-3.54%) on Iran peace deal hopes is an unprecedented divergence — markets are pricing in geopolitical risk reduction for commodities but maintaining structural de-dollarization demand for gold.",
      "implication": "Overweight GLD/GDX/SLV through the Iran resolution; do NOT interpret an Iran peace deal as a sell signal for gold — the structural demand (central bank accumulation, Strategic Mineral designation, de-dollarization) is independent of the Iran conflict premium."
    },
    {
      "insight": "Healthcare sector is universally oversold (JNJ RSI 31, AMGN RSI 30, MRK RSI 33, GILD RSI 45) simultaneously with a pharma M&A boom, creating a rare combination of technical oversold + fundamental catalyst across the entire sector.",
      "implication": "Accumulate quality pharma names (JNJ, AMGN, GILD) on weakness — M&A premium and upcoming earnings events should act as mean-reversion catalysts; the sector is pricing in more regulatory/pipeline risk than is justified by fundamentals."
    },
    {
      "insight": "Crypto is decoupling from equities in May 2026 — BTC/ETH both down 2-3% while the Nasdaq is up 0.51%, suggesting crypto-specific selling (Drift hack, fund outflows) rather than macro risk-off.",
      "implication": "Reduce crypto position sizing to the lower end of the moderate range (12% vs potential 15%); concentrate crypto exposure in BTC over ETH/SOL given BTC's institutional ETF bid and altcoin-specific headwinds."
    }
  ],
  "risk_adjusted_picks": [
    {"rank":1,"name":"Meta Platforms","symbol":"META","sector":"technology","confidence":9,"risk_score":2,"risk_adjusted_score":8.4,"recommendation":"buy","reasoning":"RSI 29 extreme oversold combined with a 57% Q1 EPS beat ($10.44 vs $6.66), PEG 0.93, and analyst consensus target of $826 creates the best large-cap risk/reward on the board.","position_size":"10%","entry_price":623.29,"stop_loss":590.00,"target_12m":800.00,"risk_reward_ratio":5.3},
    {"rank":2,"name":"SPDR Gold Shares","symbol":"GLD","sector":"materials","confidence":9,"risk_score":2,"risk_adjusted_score":8.4,"recommendation":"buy","reasoning":"Gold at $4,767/oz with Iran war premium, central bank buying, and Strategic Mineral designation provides structural support; RSI 44.2 is a fair, non-extended entry point.","position_size":"10%","entry_price":436.29,"stop_loss":415.00,"target_12m":490.00,"risk_reward_ratio":2.5},
    {"rank":3,"name":"Johnson & Johnson","symbol":"JNJ","sector":"healthcare","confidence":8,"risk_score":2,"risk_adjusted_score":7.4,"recommendation":"buy","reasoning":"Dividend King at RSI 31.4 with Q1 beat, ex-dividend May 26 (2.39% yield), and a Barclays-raised $255 target — the defensive oversold healthcare trade with a near-term income catalyst.","position_size":"9%","entry_price":221.44,"stop_loss":210.00,"target_12m":255.00,"risk_reward_ratio":2.9},
    {"rank":4,"name":"VanEck Gold Miners ETF","symbol":"GDX","sector":"materials","confidence":8,"risk_score":3,"risk_adjusted_score":7.1,"recommendation":"buy","reasoning":"GDX offers 2-3x leveraged exposure to gold's structural bull run, is up 83% in 1 year, and is trading at RSI 43.6 — not extended yet — with the 52W high of $117 as the next target.","position_size":"5%","entry_price":95.65,"stop_loss":87.00,"target_12m":115.00,"risk_reward_ratio":2.2},
    {"rank":5,"name":"NVIDIA Corporation","symbol":"NVDA","sector":"technology","confidence":8,"risk_score":4,"risk_adjusted_score":6.8,"recommendation":"buy","reasoning":"NVDA at RSI 58 is approaching its 52W high of $216.83 with earnings May 20 as the next catalyst; $215.94B revenue at 55.6% margin and a PEG 0.62 make it the best-valued AI mega-cap.","position_size":"8%","entry_price":212.08,"stop_loss":192.00,"target_12m":270.00,"risk_reward_ratio":2.9},
    {"rank":6,"name":"iShares Silver Trust","symbol":"SLV","sector":"materials","confidence":7,"risk_score":3,"risk_adjusted_score":6.1,"recommendation":"buy","reasoning":"Silver's +5% surge today and YTD +20.5% is driven by dual monetary/industrial demand; SLV with higher beta to the gold bull run at 3% portfolio weighting provides leveraged precious metals exposure.","position_size":"3%","entry_price":73.68,"stop_loss":67.00,"target_12m":88.00,"risk_reward_ratio":2.1},
    {"rank":7,"name":"Amgen Inc.","symbol":"AMGN","sector":"healthcare","confidence":7,"risk_score":3,"risk_adjusted_score":6.1,"recommendation":"buy","reasoning":"AMGN at RSI 29.8 with a Q1 EPS beat, ex-dividend May 15 at 3.04% yield, and $353 average analyst target is the highest-conviction oversold healthcare trade after META.","position_size":"7%","entry_price":328.86,"stop_loss":305.00,"target_12m":380.00,"risk_reward_ratio":2.2},
    {"rank":8,"name":"Mastercard Incorporated","symbol":"MA","sector":"financial-services","confidence":7,"risk_score":3,"risk_adjusted_score":6.1,"recommendation":"buy","reasoning":"MA at RSI 38.5 near its 52W low support zone with a Q1 earnings beat, blockchain expansion strategy, and $648 analyst target offers 30% upside once UK FCA investigation uncertainty resolves.","position_size":"6%","entry_price":499.03,"stop_loss":475.00,"target_12m":640.00,"risk_reward_ratio":5.9},
    {"rank":9,"name":"Bank of America","symbol":"BAC","sector":"financials","confidence":7,"risk_score":3,"risk_adjusted_score":6.1,"recommendation":"buy","reasoning":"BAC at RSI 46.3 with Q1 EPS beat ($1.11 vs $1.02), rising NII as the 30Y tests 5%, and a PEG of 0.95 is the best-valued large-cap bank with 18% upside to the $62.98 analyst target.","position_size":"6%","entry_price":53.40,"stop_loss":49.50,"target_12m":63.00,"risk_reward_ratio":2.5},
    {"rank":10,"name":"Netflix, Inc.","symbol":"NFLX","sector":"communication-services","confidence":7,"risk_score":3,"risk_adjusted_score":6.1,"recommendation":"buy","reasoning":"NFLX at RSI 25.1 — extreme oversold territory — with $26B free cash flow, massive share buyback in progress, and a $114 analyst consensus target is the highest-conviction mean-reversion speculative play.","position_size":"7%","entry_price":88.95,"stop_loss":80.00,"target_12m":114.00,"risk_reward_ratio":2.8},
    {"rank":11,"name":"Gilead Sciences","symbol":"GILD","sector":"healthcare","confidence":7,"risk_score":4,"risk_adjusted_score":5.8,"recommendation":"hold","reasoning":"GILD's PEG 0.38 is the cheapest in large-cap biotech with a $158 analyst target — enter AFTER today's 4:30 PM earnings call confirms guidance; binary risk justifies holding cash until post-print.","position_size":"7%","entry_price":135.55,"stop_loss":127.00,"target_12m":158.00,"risk_reward_ratio":2.6},
    {"rank":12,"name":"Bitcoin","symbol":"BTC","sector":"crypto","confidence":7,"risk_score":5,"risk_adjusted_score":5.5,"recommendation":"buy","reasoning":"BTC at $79.8K holds above key support with institutional ETF flows providing a demand floor; crypto-specific selling (Drift hack, ETH outflows) is creating a tactical buying opportunity in the market leader.","position_size":"8%","entry_price":79815,"stop_loss":73000,"target_12m":105000,"risk_reward_ratio":3.7},
    {"rank":13,"name":"Ethereum","symbol":"ETH","sector":"crypto","confidence":6,"risk_score":5,"risk_adjusted_score":4.5,"recommendation":"hold","reasoning":"ETH at $2,292 has support near $2,050 but fund outflows and network concerns keep conviction lower than BTC — accumulate below $2,150 for better risk/reward.","position_size":"4%","entry_price":2292,"stop_loss":2050,"target_12m":3200,"risk_reward_ratio":3.8}
  ],
  "historical_accuracy": {
    "previous_date": "2026-05-05",
    "calls_made": 12,
    "calls_correct": 7,
    "accuracy_pct": 58,
    "notable": "Gold (+3.7%), GDX (+10.1%), GILD (+1.6%), BAC (+0.4%), META (+1.3%), NVDA (+2.1%) above entry; JNJ (-2.0%), MA (-0.6%), AMGN (-0.7%), BTC (-1.9%), ETH (-2.5%) below — materials/tech outperformed, healthcare/crypto disappointed."
  },
  "warnings": [
    "GILD earnings call TODAY at 4:30 PM EDT — binary risk, reduce position size until post-print confirmation",
    "NVDA earnings May 20 — near 52W high of $216.83; consider trimming to 6% pre-earnings and re-entering on the call",
    "Iran peace deal talks: if confirmed, GLD/GDX may see a 3-5% tactical pullback — structural bull case intact, use dip to add",
    "PYPL downgraded TODAY by Macquarie to Neutral (PT cut $58→$50); avoid despite RSI 33.6 — institutional momentum is negative",
    "Drift/Solana $295M hack — SOL sentiment suppressed near-term; avoid SOL positions until community recovery plan confirmed",
    "30-year Treasury testing 5% — rising long-end rates headwind for growth stocks; monitor NVDA and NFLX entries closely"
  ],
  "sectors": {
    "crypto": {
      "sector": "crypto",
      "timestamp": "2026-05-07T15:25:00Z",
      "sector_summary": "Crypto is decoupling bearishly from equities on May 7, with BTC and ETH each down 2-3% while the S&P 500 grinds higher — a sign of position unwinding rather than macro risk-off. Digital asset ETPs posted their first monthly gain of 2026 in April, but early-May flows have reversed; the Drift/Solana exchange $295M hack adds specific pressure to SOL sentiment.",
      "sector_outlook": "neutral",
      "top_pick": "BTC",
      "top_pick_reasoning": "BTC remains the institutional-grade safe harbor with $1.6T market cap, CME volatility futures launching, and Strategy (MSTR) continuing accumulation even as altcoins underperform.",
      "assets": [
        {"name":"Bitcoin","symbol":"BTC","current_price":"$79,815","change_24h":"-2.27%","change_7d":"-5.1%","change_30d":"+3.2%","ytd_change":"-8.5%","week_52_high":"$126,198","week_52_low":"$60,074","market_cap":"$1.60T","volume_24h":"$33.3B","sentiment":"neutral","social_sentiment":"neutral","social_buzz":"medium","confidence":7,"source_agreement":"medium","key_news":["Digital asset ETPs post first monthly gain of 2026 in April; May showing early reversal","CME launching Bitcoin volatility futures; Strategy price target raised to $395 by TD Cowen"],"social_highlights":["Tom Lee 'biggest rally ever' prediction circulating but countered by Fidelity altcoin bear report","U.S. seized $500M in Iranian crypto — geopolitical wildcard supporting crypto regulatory scrutiny"],"recommendation":"buy","reasoning":"BTC at $79.8K holds above key $78K support with institutional ETF buying providing a floor ahead of a potential macro tailwind if Iran deal reduces global risk premium."},
        {"name":"Ethereum","symbol":"ETH","current_price":"$2,292","change_24h":"-2.81%","change_7d":"-7.5%","change_30d":"+1.5%","ytd_change":"-15.2%","week_52_high":"$4,953","week_52_low":"$1,748","market_cap":"$276.9B","volume_24h":"$20.5B","sentiment":"bearish","social_sentiment":"neutral","social_buzz":"medium","confidence":6,"source_agreement":"low","key_news":["ETH sheds $81.6M in fund outflows as crypto snaps mid-week risk-off; selling pressure down 85%","Ethereum price eyes mid-week bounce after recent 15% rally obscured an on-chain network problem"],"social_highlights":["Ethereum selling pressure crater signals potential reversal but flows remain negative","Morgan Stanley adds ETH trading to E*Trade at 0.50% fee — institutional access broadening"],"recommendation":"hold","reasoning":"ETH at RSI 44.9 is near fair-value support near $2,050-2,100 but persistent fund outflows and network concerns cap upside near-term — hold existing positions, new entry at $2,100."},
        {"name":"Solana","symbol":"SOL","current_price":"$88.09","change_24h":"-0.98%","change_7d":"-5.2%","change_30d":"-8.3%","ytd_change":"-43.5%","week_52_high":"$253.21","week_52_low":"$68.69","market_cap":"$50.98B","volume_24h":"$4.74B","sentiment":"bearish","social_sentiment":"neutral","social_buzz":"low","confidence":5,"source_agreement":"low","key_news":["Drift exchange (Solana DEX) suffers $295M hack; Jito Foundation launches Asia-Pacific institutional partnership","Solana bulls reclaim control after weeks of selling, chart targets 14% breakout to ~$100"],"social_highlights":["Drift hack overshadows institutional partnership news — negative near-term overhang","Fidelity crypto report paints brutal picture for altcoins including SOL relative to BTC"],"recommendation":"hold","reasoning":"SOL is 65% below its 52W high with the Drift hack creating negative sentiment overhang; wait for a confirmed break above $95 before adding exposure."}
      ]
    },
    "stocks": {
      "sector": "stocks",
      "timestamp": "2026-05-07T15:25:00Z",
      "sector_summary": "U.S. equities are mixed on May 7 with the Nasdaq +0.51% led by semiconductors (NVDA +2.1%) while healthcare underperforms broadly — JNJ, MRK, AMGN all in the red. META is recovering sharply after a monstrous Q1 earnings beat (EPS $10.44 vs $6.66 estimate), validating the RSI-29 oversold entry thesis from the May 5 screener.",
      "sector_outlook": "neutral",
      "top_pick": "META",
      "top_pick_reasoning": "META's Q1 2026 earnings obliterated estimates with 57% EPS upside while trading at PEG 0.93 and RSI 29 — one of the most compelling risk/reward setups in large-cap tech.",
      "assets": [
        {"name":"Meta Platforms","symbol":"META","current_price":"$623.29","change_24h":"+1.70%","change_7d":"-5.2%","change_30d":"-14.5%","ytd_change":"-5.49%","week_52_high":"$796.25","week_52_low":"$520.26","market_cap":"$1.58T","volume_24h":"$9.6B","sentiment":"bullish","social_sentiment":"bullish","social_buzz":"high","confidence":9,"source_agreement":"high","key_news":["Q1 FY2026 earnings: EPS $10.44 vs $6.66 estimate (+57%), revenue $56.31B; analysts raising price targets broadly","Meta paying creators in stablecoins; UK media regulator challenge signals regulatory noise"],"social_highlights":["Guggenheim 79/100 top analyst score with BUY; consensus analyst target $826.69 (+33% upside from current)","Billion-dollar agentic AI companies with one employee emerging — Meta's AI ecosystem is key infrastructure play"],"recommendation":"buy","reasoning":"META at RSI 29 with a massive Q1 EPS beat ($10.44 vs $6.66), PEG 0.93, and $81B cash balance is a rare combination of deep value and earnings momentum in mega-cap tech."},
        {"name":"NVIDIA Corporation","symbol":"NVDA","current_price":"$212.08","change_24h":"+2.11%","change_7d":"+3.5%","change_30d":"+8.2%","ytd_change":"+13.73%","week_52_high":"$216.83","week_52_low":"$115.21","market_cap":"$5.15T","volume_24h":"$36.2B","sentiment":"bullish","social_sentiment":"bullish","social_buzz":"high","confidence":8,"source_agreement":"high","key_news":["Semiconductor stocks leading market rally May 7; NVDA approaching 52W high of $216.83 ahead of May 20 earnings","Q4 FY2026 earnings showed EPS $1.62 vs $1.54 estimate, revenue $68.13B; Rosenblatt top analyst score 82/100 with BUY"],"social_highlights":["Marvell reaching all-time highs reinforces AI infrastructure supercycle — NVDA is the picks-and-shovels play","Consensus analyst target $269.17 (+27% from current); earnings May 20 is a near-term catalyst"],"recommendation":"buy","reasoning":"NVDA at RSI 58.3 with earnings May 20 and a 52W high just above current price ($216.83) creates a momentum breakout setup backed by $215.94B revenue run-rate at 55.6% profit margin."},
        {"name":"Johnson & Johnson","symbol":"JNJ","current_price":"$221.44","change_24h":"-1.42%","change_7d":"-2.1%","change_30d":"-5.3%","ytd_change":"+7.57%","week_52_high":"$251.71","week_52_low":"$146.12","market_cap":"$533.1B","volume_24h":"$1.8B","sentiment":"neutral","social_sentiment":"neutral","social_buzz":"low","confidence":8,"source_agreement":"medium","key_news":["JNJ launches 'Generation Fine' mental health campaign; Q1 FY2026 EPS $2.70 beat $2.68 estimate","Barclays raised PT from $234 to $255; pharma M&A boom favors JNJ's diversified platform"],"social_highlights":["Dividend King status maintained with 2.39% yield; ex-dividend May 26 creates near-term catalyst","UBS top analyst score 58/100 BUY; average PT $252.42 (+14% upside)"],"recommendation":"buy","reasoning":"JNJ at RSI 31.4 is extremely oversold for a Dividend King trading at a 12% discount to analyst consensus ($252 avg target), with a Q1 earnings beat and ex-dividend date May 26 as near-term support."},
        {"name":"Amgen Inc.","symbol":"AMGN","current_price":"$328.86","change_24h":"-0.68%","change_7d":"-2.5%","change_30d":"-8.5%","ytd_change":"+1.17%","week_52_high":"$391.29","week_52_low":"$261.43","market_cap":"$177.6B","volume_24h":"$0.89B","sentiment":"neutral","social_sentiment":"neutral","social_buzz":"low","confidence":7,"source_agreement":"medium","key_news":["$300M Puerto Rico biologics manufacturing expansion announced; FDA scrutiny on Tavneos creates headwind","Q1 FY2026 EPS $5.15 beat $4.77 estimate; ex-dividend May 15 at 3.04% annual yield"],"social_highlights":["Guggenheim maintains Neutral (PT $340 from $351) — cautious but not bearish; stock below analyst avg target","Pharma M&A boom (Lilly, Gilead leading deals) could re-rate AMGN as acquisition target"],"recommendation":"buy","reasoning":"AMGN at RSI 29.8 with Q1 earnings beat, ex-dividend May 15 (3.04% yield), and $353 average analyst target offers 7% upside to consensus with an income kicker in a defensive sector."},
        {"name":"Netflix, Inc.","symbol":"NFLX","current_price":"$88.95","change_24h":"+0.77%","change_7d":"-5.8%","change_30d":"-24.5%","ytd_change":"-5.13%","week_52_high":"$134.12","week_52_low":"$75.01","market_cap":"$374.6B","volume_24h":"$4.0B","sentiment":"bearish","social_sentiment":"neutral","social_buzz":"medium","confidence":7,"source_agreement":"medium","key_news":["Q1 FY2026 EPS $1.23 missed $1.25 estimate slightly but revenue grew; massive share buyback program signals management confidence","Warner Bros. Discovery posts $2.8B Netflix termination fee charge — confirms NFLX content pricing power"],"social_highlights":["Oppenheimer top analyst 73/100 OUTPERFORM, PT $115; average analyst target $114.56 (+29% from current)","'Netflix and Meta on sale' articles circulating — contrarian buying sentiment building at RSI 25"],"recommendation":"buy","reasoning":"NFLX at RSI 25.1 — the most oversold it has been in 2 years — combined with a $25.99B free cash flow run-rate and a massive buyback at current levels creates a speculative but compelling mean-reversion trade toward the $114 analyst consensus."},
        {"name":"Bank of America","symbol":"BAC","current_price":"$53.40","change_24h":"-0.36%","change_7d":"-1.2%","change_30d":"+0.7%","ytd_change":"-2.36%","week_52_high":"$57.55","week_52_low":"$41.25","market_cap":"$378.96B","volume_24h":"$2.1B","sentiment":"neutral","social_sentiment":"neutral","social_buzz":"low","confidence":7,"source_agreement":"medium","key_news":["Q1 FY2026 EPS $1.11 beat $1.02 estimate on rising net interest income; expanding defense financing initiative","30-year Treasury testing 5% — dual-edged for BAC: NII expands but credit risk and duration headwinds increase"],"social_highlights":["Truist Securities 65/100 top analyst BUY; average analyst target $62.98 (+18% upside from current)","BAC vs MS: Zacks analysis favors BAC on stronger NII trajectory post-Q1"],"recommendation":"buy","reasoning":"BAC at RSI 46.3 with a PEG of 0.95, strong Q1 earnings beat, and analyst target of $62.98 represents 18% upside for a diversified bank with rising net interest income as the 30Y yield tests 5%."},
        {"name":"Mastercard Incorporated","symbol":"MA","current_price":"$499.03","change_24h":"+1.45%","change_7d":"-3.8%","change_30d":"-10.1%","ytd_change":"-12.30%","week_52_high":"$601.77","week_52_low":"$480.50","market_cap":"$440.9B","volume_24h":"$1.8B","sentiment":"neutral","social_sentiment":"neutral","social_buzz":"low","confidence":7,"source_agreement":"medium","key_news":["Q1 FY2026 EPS $4.60 beat $4.41 estimate; JPMorgan and Mastercard settle tokenized US Treasuries on XRP Ledger in 5 seconds","UK FCA opens competition investigation into PayPal, Visa, and Mastercard — regulatory headwind"],"social_highlights":["Macquarie maintains Outperform with PT $665; average analyst target $648.61 (+30% from current)","Crypto card spending on groceries/gas — OKX 2026 report shows MA network utility expanding into digital assets"],"recommendation":"buy","reasoning":"MA at RSI 38.5 near multi-year support at $480 with Q1 earnings beat, blockchain expansion into tokenized settlement, and a $648 analyst consensus target offers 30% upside once UK regulatory overhang clears."},
        {"name":"Gilead Sciences","symbol":"GILD","current_price":"$135.55","change_24h":"-0.55%","change_7d":"+0.8%","change_30d":"+3.2%","ytd_change":"+11.06%","week_52_high":"$157.29","week_52_low":"$95.30","market_cap":"$168.2B","volume_24h":"$0.86B","sentiment":"neutral","social_sentiment":"neutral","social_buzz":"medium","confidence":7,"source_agreement":"medium","key_news":["EARNINGS TODAY at 4:30 PM EDT — Q1 FY2026 results; Gilead is leading pharma's M&A boom alongside Lilly","Arcus Biosciences rethinks growth after STAR-121 exit and Gilead collaboration shift — pipeline noise"],"social_highlights":["Citigroup maintains BUY, raised PT from $156 to $165; average analyst target $158.36 (+17% from current)","PEG 0.38 is the cheapest valuation in large-cap biotech — quality franchise priced for failure"],"recommendation":"hold","reasoning":"GILD reports earnings today at 4:30 PM EDT creating binary risk — exceptional value (PEG 0.38, PT $158) but reduce sizing pre-print and re-enter on post-earnings confirmation."}
      ]
    },
    "materials": {
      "sector": "materials",
      "timestamp": "2026-05-07T15:25:00Z",
      "sector_summary": "Gold and silver are the standout performers on May 7, with gold futures hitting $4,767/oz (+1.55%) and silver (SLV) surging +5.06% as Iran peace deal talks emerge, creating an unusual dynamic where geopolitical optimism cools inflation fears rather than reducing safe-haven demand. GDX gold miners are up +3.47% and have returned +83% over the past 12 months, dramatically outperforming the S&P 500's +31%.",
      "sector_outlook": "bullish",
      "top_pick": "GLD",
      "top_pick_reasoning": "GLD at RSI 44.2 remains a fair entry for a gold price at $4,767/oz driven by structural de-dollarization, Iran war premium, and central bank accumulation — the Iran peace deal may cause a short-term dip but long-term structural demand is intact.",
      "assets": [
        {"name":"SPDR Gold Shares","symbol":"GLD","current_price":"$436.29","change_24h":"+1.24%","change_7d":"+2.5%","change_30d":"+6.8%","ytd_change":"+8.74%","week_52_high":"$509.70","week_52_low":"$291.78","market_cap":"$153.5B","volume_24h":"$1.13B","sentiment":"bullish","social_sentiment":"bullish","social_buzz":"high","confidence":9,"source_agreement":"high","key_news":["Gold surges past $4,770 as Iran peace deal hopes 'cool inflation fears' — unusual bullish paradox as oil -3.5%","Gold soared 50% in 2025; real yields crushing gold short-term but long-term picture intact per analysis"],"social_highlights":["GLD becoming 'crowded trade' concerns raised — contrarian warning but institutions still buying","Gold now designated a Strategic Mineral — government-level demand adds structural floor to prices"],"recommendation":"buy","reasoning":"GLD at RSI 44.2 with gold futures at $4,767/oz has a structural bid from central banks, Iran war premium, and strategic mineral designation — the Iran peace deal may cause a 3-5% pullback but does not change the multi-year bull case."},
        {"name":"VanEck Gold Miners ETF","symbol":"GDX","current_price":"$95.65","change_24h":"+3.47%","change_7d":"+5.8%","change_30d":"+12.5%","ytd_change":"+7.78%","week_52_high":"$117.18","week_52_low":"$45.10","market_cap":"$27.26B","volume_24h":"$0.91B","sentiment":"bullish","social_sentiment":"bullish","social_buzz":"medium","confidence":8,"source_agreement":"high","key_news":["Gold and Silver Mining ETFs surge as precious metals rally accelerates — GDX +83% 1-year vs S&P 500 +31%","'This New War Can Take This Gold Mining ETF to New Highs Again' — new war cycle thesis intact"],"social_highlights":["GDX vs SLVP: silver miners recently outpaced gold miners but GDX's liquidity and diversification preferred","Gold soared 50%+ this year; miners have operational leverage creating 2-3x amplification of gold moves"],"recommendation":"buy","reasoning":"GDX at RSI 43.6 offers leveraged exposure to $4,767 gold via senior miners (Newmont 11.3%, Agnico Eagle 11.5% top holdings) with 83% 1-year returns and room to the 52W high of $117.18."},
        {"name":"iShares Silver Trust","symbol":"SLV","current_price":"$73.68","change_24h":"+5.06%","change_7d":"+4.2%","change_30d":"+9.5%","ytd_change":"+20.5%","week_52_high":"$81.20","week_52_low":"$42.50","market_cap":"$15.2B","volume_24h":"$0.88B","sentiment":"bullish","social_sentiment":"bullish","social_buzz":"medium","confidence":7,"source_agreement":"medium","key_news":["Silver up +5.06% today as Iran deal hopes 'rewrite the inflation playbook' — gold/silver catching fire together","SLV vs GLD: silver offers bigger swings with higher beta to gold bull run"],"social_highlights":["Silver miners (SIL) outpaced gold miners (GDX) in 2025 — silver has higher industrial demand multiplier","SLV +20.5% YTD dramatically outpacing GLD +8.74% — momentum accelerating"],"recommendation":"buy","reasoning":"SLV's +5% surge today reflects silver's dual role as both a monetary metal (Iran hedge) and industrial metal (AI/green energy demand) — the gold/silver ratio compression trade is playing out with momentum."}
      ]
    }
  }
}

# Paths
base = "/Users/carlosfuentes/GitHub/maia-skill"
dashboard_path = os.path.join(base, "dashboard/public/data/report.json")
history_dir = os.path.join(base, "output/history")
os.makedirs(history_dir, exist_ok=True)
os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)

# Write report.json
with open(dashboard_path, "w") as f:
    json.dump(REPORT, f, indent=2)
print("✓ report.json")

# Write history
hist_path = os.path.join(history_dir, "2026-05-07.json")
with open(hist_path, "w") as f:
    json.dump(REPORT, f, indent=2)

# Count history files, prune to 30
files = sorted(glob.glob(os.path.join(history_dir, "*.json")))
if len(files) > 30:
    for f in files[:-30]:
        os.remove(f)

print(f"✓ 2026-05-07.json | history files: {len(files)}")
picks = REPORT["risk_adjusted_picks"]
top = picks[0]
print(f"picks: {len(picks)} | top: {top['symbol']} RAS={top['risk_adjusted_score']}")
print("Done.")
