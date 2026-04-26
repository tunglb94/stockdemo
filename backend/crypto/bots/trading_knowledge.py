"""
Trading knowledge base — injected into bot system prompts each round.
Philosophy: models already know TA theory. Inject DECISION RULES only.
Format: English + structured (code-style rules > prose explanations).
"""

# =============================================================================
# TECHNICAL SIGNALS — decision rules, not definitions
# =============================================================================

TECHNICAL_SIGNALS = """
## TECHNICAL SIGNALS (decision rules)

### RSI
| RSI Value | Signal | Action |
|-----------|--------|--------|
| < 20 | Extreme oversold / capitulation | STRONG LONG |
| 20–30 | Oversold | LONG (wait for 1 green candle confirmation) |
| 30–45 | Bearish zone | Avoid longs |
| 45–55 | Neutral | No edge |
| 55–70 | Bullish zone | Hold longs |
| 70–80 | Overbought | Reduce size, take partial profit |
| > 80 | Extreme overbought | SHORT candidate or exit longs |

**Divergence rules:**
- Bullish divergence: price makes lower low, RSI makes higher low → reversal up imminent → BUY
- Bearish divergence: price makes higher high, RSI makes lower high → reversal down imminent → SHORT

### Momentum (24h % change — primary signal in this system)
```
if change_24h > +5%:  overbought → SHORT candidate, leverage 15-20x
if change_24h > +3%:  extended → SHORT candidate, leverage 10-15x
if change_24h < -5%:  oversold  → LONG candidate,  leverage 15-20x
if change_24h < -3%:  dipped    → LONG candidate,  leverage 10-15x
if abs(change_24h) < 2%: sideways → SKIP, no edge
```

### Moving Averages
```
EMA20 > EMA50 > EMA200 → strong uptrend → only LONG
EMA20 < EMA50 < EMA200 → strong downtrend → only SHORT
price pullback to EMA20 in uptrend → best LONG entry point
price bounce from EMA200 → very strong support → LONG
```

### Volume
```
volume > 200% avg + price up   → real breakout → enter LONG aggressively
volume > 200% avg + price down → panic sell / capitulation → consider LONG
volume < 50% avg + price up    → fake pump → do NOT enter
volume fading in uptrend       → distribution → prepare to exit
```

### Support & Resistance
- Round numbers (BTC $80k, ETH $3k): high psychological significance
- Previous ATH: strongest resistance; when broken = explosive FOMO move
- Old highs become support when reclaimed; old lows become resistance when broken
"""

# =============================================================================
# MARKET STRUCTURE
# =============================================================================

MARKET_STRUCTURE = """
## MARKET STRUCTURE

### BTC Dominance (BTC.D)
```
BTC.D rising  + BTC price rising  → BTC season → buy BTC/ETH, ignore alts
BTC.D falling + BTC price rising  → altseason   → buy SOL/AVAX/NEAR/INJ
BTC.D rising  + BTC price falling → risk-off    → hold cash or SHORT
BTC.D < 40%                       → altseason peak, prepare to exit alts
BTC.D > 60%                       → BTC dominates, alts underperform
```

### Sentiment Indicators
```
Fear & Greed 0–20   → Extreme Fear  → LONG signal (buy when others fear)
Fear & Greed 20–40  → Fear          → Accumulate carefully
Fear & Greed 60–80  → Greed         → Take partial profits
Fear & Greed 80–100 → Extreme Greed → SHORT signal (top is near)

Funding Rate > +0.1% → too many longs → SHORT squeeze incoming → SHORT
Funding Rate < -0.1% → too many shorts → LONG squeeze incoming  → LONG
Funding Rate > +0.3% → extreme → long squeeze imminent → SHORT strongly
```

### Crypto Correlations
```
BTC moves up   → ETH/SOL follow in ~2-4 hours (lag trade opportunity)
ETH moves up   → DeFi tokens (LINK, AAVE, UNI, MKR) follow
BTC drops -5%  → alts drop -8 to -15% (high beta)
Market sideways → L2 (ARB, OP) and DeFi tend to rotate
```

### Liquidation Cascades
```
BTC drops -5% in 1 hour → long cascade → wait for bounce
BTC rises +5% in 1 hour → short squeeze → wait for pullback
After cascade: wait 15-30 min → then trade the reversal
NEVER enter same direction during an active cascade (catching falling knife)
```
"""

# =============================================================================
# FUTURES MECHANICS
# =============================================================================

FUTURES_MECHANICS = """
## FUTURES MECHANICS

### P&L Calculation
```python
# LONG position
pnl = (current_price - entry_price) / entry_price * margin * leverage
# SHORT position
pnl = (entry_price - current_price) / entry_price * margin * leverage

# Example: margin=$500, leverage=10x, price moves +1%
pnl = 0.01 * 500 * 10 = +$50

# Liquidation threshold (this system): loss > 80% of margin
liq_price_long  = entry * (1 - 0.8 / leverage)
liq_price_short = entry * (1 + 0.8 / leverage)
```

### When to LONG
```
✓ Asset dropped > 3% in 24h + reversal signal (RSI < 35, bounce candle)
✓ BTC just broke above ATH with volume confirmation
✓ After short squeeze (funding rate was negative, now normalizing)
✓ Price testing EMA200 and holding
✓ Fear & Greed < 25 (market oversold)
✓ Exchange outflows rising (whales withdrawing = hodling)
```

### When to SHORT
```
✓ Asset pumped > 3% in 24h + no fundamental catalyst
✓ RSI > 80 after strong pump
✓ Funding rate extremely positive (> +0.1%) — too many longs
✓ Bearish divergence: new price high but RSI lower high
✓ Price rejected hard at major resistance (old ATH, round number)
✓ Fear & Greed > 90 (market euphoric = top signal)
✓ "Buy the rumor, sell the news" — event has passed
```

### Position Management Rules
```python
# Stop-loss (this system auto-closes at -30% margin)
if unrealized_pnl < -0.20 * margin:  # -20% threshold
    action = "CLOSE"  # cut early before auto stop-loss

# Profit-taking
if unrealized_pnl > 0.30 * margin:  # +30% threshold
    action = "CLOSE"  # lock in gains

# Stale position
if position_age_hours > 2 and unrealized_pnl < 0.05 * margin:
    action = "CLOSE"  # capital stuck, redeploy

# NEVER do these with leverage:
# - averaging down (adding to losing position)
# - holding through -30%+ loss hoping for recovery
# - opening opposite direction on same asset
```
"""

# =============================================================================
# COMMODITY TRADING RULES
# =============================================================================

COMMODITY_RULES = """
## COMMODITY TRADING RULES

### Gold (XAU) — safe haven
```
LONG  when: USD (DXY) weakening, Fed dovish, inflation rising, geopolitical stress
SHORT when: Fed hawkish/rate hikes, risk-on rally, USD strengthening
Strong support: EMA200 + RSI < 40 → high-conviction LONG entry
```

### Oil (WTI / BRENT)
```
LONG  when: OPEC+ production cuts, Middle East tensions, summer driving season (Jun-Aug)
SHORT when: recession signals, OPEC disagreement/output increase, demand concerns
Key level: WTI $60-70 = shale production cost floor → very strong support
```

### Natural Gas (NATGAS) — most volatile commodity
```
LONG  when: cold winter forecast, summer heatwave, LNG export demand spike
SHORT when: warm winter (El Niño), high storage inventory, record US production
WARNING: NATGAS moves 5-10%/day — use lower leverage (5-8x), smaller margin
```

### Agricultural (WHEAT, CORN, COFFEE)
```
WHEAT:  LONG on Ukraine/Russia/US drought; SHORT at harvest (Jul-Aug)
CORN:   LONG on ethanol demand + Midwest drought; SHORT at US harvest (Sep-Nov)
COFFEE: LONG on El Niño / Brazil drought; SHORT on bumper harvest season
```

### Commodity-Crypto Correlation
```
XAU/XAG rising strongly → BTC often follows (both = inflation hedge)
Oil > $100             → inflation → Fed hikes → crypto BEARISH
COPPER falling         → global recession signal → risk-off → crypto BEARISH
```

### When to prefer Commodity over Crypto
```
Crypto is flat/sideways     → trade commodities with seasonal patterns
Market is risk-off (panic)  → LONG XAU, XAG (safe haven flows)
Global growth story         → LONG COPPER (economic barometer)
```
"""

# =============================================================================
# RISK MANAGEMENT
# =============================================================================

RISK_RULES = """
## RISK MANAGEMENT RULES

### Position Sizing
```python
margin_per_trade = min(800, balance * 0.15)   # 15% of balance, max $800
max_total_margin = balance * 0.60             # never exceed 60% total
min_cash_reserve = balance * 0.20             # always keep 20% free

leverage_map = {
    "very_strong_signal": (15, 20),  # 3+ confirming factors
    "strong_signal":      (10, 15),  # 2 confirming factors
    "weak_signal":        "SKIP",    # 1 or fewer → do not trade
}
```

### Portfolio Rules
```
max_open_positions = 4         # system enforces this
no_duplicate_direction = True  # system enforces: 1 LONG per symbol max
stop_loss_auto = -30%          # system auto-closes at -30% margin loss
stop_loss_manual = -20%        # close manually before auto triggers

After 3 consecutive losses:
  → reduce leverage to 8-10x for next 2 rounds
  → review if market structure changed
```

### Psychological Traps to Avoid
```
FOMO:             price already +20% → do NOT chase → wait for pullback
Revenge trading:  lost last round → do NOT increase size to recover
Sunk cost:        losing position → CLOSE it, do not hold "hoping"
Overconfidence:   winning streak → do NOT increase beyond risk limits
```
"""

# =============================================================================
# MACRO SIGNALS
# =============================================================================

MACRO_SIGNALS = """
## MACRO SIGNALS

### USD & Fed Policy
```
DXY rising  → BTC/Gold/Oil falling (dollar strength = capital to USD)
DXY falling → BTC/Gold/Commodities rising
Fed hawkish (rate hike)  → risk-off → crypto bearish
Fed dovish (rate cut/QE) → risk-on  → crypto bullish
CPI higher than expected → bearish short-term (more hikes coming)
CPI lower than expected  → bullish  (rate cuts sooner)
```

### Halving Cycle
```
Pre-halving (6 months before): accumulation phase, gradual rise
Post-halving (12-18 months):   historically strongest bull run
Current: post-2024 halving cycle → macro tailwind for LONG bias
```

### Geopolitical
```
War/crisis outbreak:          initial selloff → then XAU/BTC recover as safe haven
Major exchange hack:          panic sell all crypto → LONG opportunity after dust settles
ETF/institutional approval:   strong bullish → sustained rally
Regulatory crackdown:         bearish short-term, assess severity
```

### Market Scenarios
```python
scenarios = {
    "BULL_RUN":   "BTC > ATH, Fear&Greed > 75 → prefer LONG everything, higher leverage OK",
    "BEAR":       "BTC < MA200, Fear&Greed < 25 → prefer SHORT alts, LONG XAU/XAG, low leverage",
    "SIDEWAYS":   "BTC in 2-week range → commodity seasonal trades, extreme RSI entries only",
    "MACRO_SHOCK":"unexpected Fed/war/bank → exit positions → LONG XAU → wait 1-3 days",
    "ALTSEASON":  "BTC.D falling, ETH/BTC rising → rotate BTC → ETH → large alts → small alts",
}
```
"""

# =============================================================================
# ADVANCED CONCEPTS (condensed)
# =============================================================================

ADVANCED_CONCEPTS = """
## ADVANCED CONCEPTS (condensed)

### Wyckoff (market phases)
```
ACCUMULATION (smart money buying):
  Selling Climax (SC) → volume spike + big drop → bounce (AR) → re-test low with less volume → BUY

DISTRIBUTION (smart money selling):
  Buying Climax (BC) → volume spike + big pump → drop (AR) → re-test high with less volume → SHORT
```

### Smart Money Concepts
```
Equal highs (liquidity pool above): whales will sweep above → then reverse DOWN → SHORT after sweep
Equal lows (liquidity pool below):  whales will sweep below → then reverse UP   → LONG after sweep
Order Block = last opposing candle before strong move → price returns to test it → entry zone
Fair Value Gap (FVG) = price gap in 3-candle pattern → price tends to fill gaps
```

### Intermarket
```
BTC up + SPX flat    → BTC strong, decoupling → bullish
BTC flat + SPX up    → BTC weak vs risk assets → cautious
XAU up + BTC up      → macro uncertainty hedge (both as stores of value)
US10Y yield rising   → growth stocks + crypto fall → bearish
US10Y yield peaking  → crypto starts recovery → accumulate
```

### Optimal Entry Timing
```
Best entry windows (UTC):
  US Open  14:30-16:00 UTC: highest volume → wait 15min for false breakout to clear
  London   09:00-10:00 UTC: liquidity sweep often reverses
  Asian    00:00-06:00 UTC: low volume → range trading, avoid breakout trades

Weekly: Monday open often sweeps liquidity → wait for direction confirmation
```

### Exit Strategy
```python
# Partial take profit (scale out):
at_r1_1_ratio: close 30%   # near-guaranteed profit
at_r2_1_ratio: close 40%   # strong profit
remainder:     trail_stop  # let it run with trailing stop

# Trailing stop: move stop to breakeven when +R1:R1, then trail 1.5x ATR from peak
```
"""

# =============================================================================
# PRACTICAL SCENARIOS
# =============================================================================

PRACTICAL_SCENARIOS = """
## QUICK REFERENCE: SCENARIO → ACTION

| Scenario | Key Signal | Action |
|----------|-----------|--------|
| BTC drops -5% in 1hr | Liquidation cascade | Wait 15-30min, then LONG |
| Asset pumped +8% today | Overbought | SHORT with 15x, tight stop |
| Asset dumped -8% today | Oversold | LONG with 15x, hold for bounce |
| BTC flat, altcoin +20% | Divergence | SHORT the overextended alt |
| XAU rising, BTC flat | Macro stress | LONG BTC (lagging safe haven) |
| All crypto pumping | Euphoria | Reduce longs, SHORT high-beta alts |
| News event passed | "Sell the news" | SHORT if price already ran up |
| Market sideways 1 week | No momentum | Trade commodities (XAU, WTI) |
| Funding rate > +0.2% | Longs overloaded | SHORT BTC/ETH for squeeze |
| Fear & Greed < 20 | Capitulation | Strong LONG, high conviction |

## GOLDEN RULES
1. Win rate 50% + R:R 2:1 = profitable long-term (positive expectancy)
2. Never risk > 15% of balance on a single position margin
3. The best trades are obvious — if you need to convince yourself, skip it
4. Cut losses fast. Let winners run. This is the entire game.
5. "The market can stay irrational longer than you can stay solvent" — Keynes
"""


# =============================================================================
# PUBLIC API — called by bot definitions
# =============================================================================

def get_crypto_knowledge() -> str:
    """Full knowledge base for crypto spot bots."""
    return (
        TECHNICAL_SIGNALS
        + MARKET_STRUCTURE
        + COMMODITY_RULES
        + MACRO_SIGNALS
        + RISK_RULES
        + ADVANCED_CONCEPTS
        + PRACTICAL_SCENARIOS
    )


def get_futures_knowledge() -> str:
    """Full knowledge base for futures LONG/SHORT bots."""
    return (
        TECHNICAL_SIGNALS
        + MARKET_STRUCTURE
        + FUTURES_MECHANICS
        + COMMODITY_RULES
        + MACRO_SIGNALS
        + RISK_RULES
        + PRACTICAL_SCENARIOS
    )
