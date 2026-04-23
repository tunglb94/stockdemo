"""
Kiến thức trading chuyên nghiệp — dùng chung cho crypto spot và futures bots.
Được tổng hợp từ: technical analysis, on-chain metrics, macro, market psychology,
risk management và đặc thù thị trường crypto 24/7.
"""

TECHNICAL_ANALYSIS = """
=== PHÂN TÍCH KỸ THUẬT CHUYÊN SÂU ===

--- RSI (Relative Strength Index) ---
- RSI < 20: EXTREME oversold — khủng hoảng / capitulation, cơ hội LONG mạnh nhất
- RSI 20-30: Oversold — cân nhắc LONG, chờ confirmation
- RSI 30-45: Bearish territory — thận trọng, không mua mạnh
- RSI 45-55: Neutral / Sideways — không có edge rõ ràng
- RSI 55-70: Bullish territory — giữ LONG, có thể add
- RSI 70-80: Overbought — tích lũy lợi nhuận, giảm size
- RSI > 80: EXTREME overbought — cân nhắc SHORT hoặc thoát toàn bộ
- RSI Divergence TĂNG: giá tạo đáy mới NHƯNG RSI tạo đáy cao hơn → reversal sắp tới (BUY signal)
- RSI Divergence GIẢM: giá tạo đỉnh mới NHƯNG RSI tạo đỉnh thấp hơn → phân phối (SELL signal)

--- MACD (Moving Average Convergence Divergence) ---
- MACD cắt lên Signal: tín hiệu BUY (bullish crossover)
- MACD cắt xuống Signal: tín hiệu SELL (bearish crossover)
- Histogram tăng dần: momentum đang tăng → giữ hoặc thêm vị thế
- Histogram giảm dần: momentum đang yếu → chuẩn bị thoát
- MACD Divergence: giống RSI divergence, rất mạnh khi kết hợp

--- Bollinger Bands ---
- Giá chạm Lower Band + RSI < 35: tín hiệu BUY mạnh (mean reversion)
- Giá chạm Upper Band + RSI > 65: tín hiệu SELL / SHORT
- Band thu hẹp (Squeeze): sắp có biến động lớn, chuẩn bị cho breakout
- Band giãn rộng đột ngột: breakout đang xảy ra, theo đà
- Giá đi dọc Upper Band liên tục: trend mạnh, KHÔNG short ngược

--- Moving Averages ---
- EMA20 > EMA50 > EMA200: uptrend mạnh — chỉ BUY, không SHORT
- EMA20 < EMA50 < EMA200: downtrend mạnh — chỉ SHORT, không BUY
- Golden Cross (EMA50 cắt lên EMA200): bullish dài hạn, tín hiệu mạnh
- Death Cross (EMA50 cắt xuống EMA200): bearish dài hạn
- Giá pullback về EMA20 trong uptrend: điểm mua tốt nhất (buy the dip)
- Giá bounce từ EMA200: hỗ trợ cực mạnh, thường đảo chiều

--- Volume Analysis ---
- Volume > 200% trung bình + giá tăng = REAL BREAKOUT (vào mạnh)
- Volume > 200% trung bình + giá giảm = PANIC SELL / CAPITULATION (cân nhắc buy dip)
- Volume thấp < 50% trung bình + giá tăng = FAKE PUMP (không tin)
- Volume cạn dần trong uptrend = distribution (smart money đang xả)
- Volume spike đột biến 1 nến rồi về bình thường = stop hunt / whale manipulation

--- Candlestick Patterns ---
- Doji tại đỉnh: exhaustion, sắp giảm
- Doji tại đáy: capitulation, sắp tăng
- Hammer (bóng dưới dài, thân nhỏ trên): reversal tăng mạnh
- Shooting Star (bóng trên dài, thân nhỏ dưới): reversal giảm mạnh
- Engulfing xanh nuốt đỏ: mua mạnh, xác nhận đảo chiều
- Engulfing đỏ nuốt xanh: bán mạnh, xác nhận đảo chiều
- Pin Bar (rejection wick dài): từ chối vùng giá, đảo chiều
- Marubozu xanh không bóng: trend tăng cực mạnh, không do dự

--- Support & Resistance ---
- Vùng giá từng là đỉnh → khi phá lên thành hỗ trợ (support becomes resistance)
- Vùng giá từng là đáy → khi phá xuống thành kháng cự (resistance becomes support)
- Số tròn (BTC $80,000 / ETH $3,000): tâm lý mạnh, nhiều lệnh đặt tại đây
- ATH (All-Time High): kháng cự mạnh nhất, khi phá = FOMO cực mạnh
- Previous weekly/monthly close: hỗ trợ/kháng cự quan trọng

--- Fibonacci Retracement ---
- 0.236 (23.6%): hỗ trợ yếu trong uptrend mạnh
- 0.382 (38.2%): hỗ trợ phổ biến nhất trong uptrend
- 0.500 (50%): tâm lý quan trọng
- 0.618 (61.8%): "Golden Ratio" — hỗ trợ mạnh nhất, smart money thường mua đây
- 0.786 (78.6%): gần như retest toàn bộ — nếu phá là downtrend
"""

CRYPTO_MARKET_STRUCTURE = """
=== CẤU TRÚC THỊ TRƯỜNG CRYPTO ===

--- BTC Dominance (BTC.D) ---
- BTC.D tăng + BTC giá tăng: BULL RUN BTC, altcoin lag → mua BTC
- BTC.D giảm + BTC giá tăng: ALTSEASON → mua altcoin mạnh
- BTC.D tăng + BTC giá giảm: RISK OFF, mọi thứ bán → giữ tiền mặt / USDT
- BTC.D < 40%: altseason đỉnh điểm, cẩn thận reversal
- BTC.D > 60%: BTC season, altcoin underperform

--- Market Cycles (Chu kỳ thị trường) ---
- Accumulation: giá nằm ngang sau downtrend dài → smart money mua gom (BUY dần)
- Markup (Uptrend): breakout, FOMO, retail vào → giữ, add vị thế
- Distribution: giá sideway tại đỉnh → smart money xả hàng (bắt đầu bán)
- Markdown (Downtrend): đổ dốc, panic sell → tránh bắt đáy sớm

--- Altcoin Correlations ---
- BTC tăng → Layer 1 (ETH, SOL, AVAX, NEAR) tăng chậm hơn ~2-4 giờ
- ETH tăng → DeFi tokens (UNI, LINK, AAVE, MKR) tăng theo
- BTC giảm mạnh → altcoin giảm 1.5-3x mạnh hơn (cao beta)
- Khi thị trường sideway: Layer 2 (ARB, OP) và DeFi rotate

--- Funding Rate (Futures Market) ---
- Funding Rate > +0.1%: thị trường quá bullish, nhiều người LONG → cân nhắc SHORT
- Funding Rate < -0.1%: thị trường quá bearish, nhiều người SHORT → cân nhắc LONG
- Funding Rate gần 0%: cân bằng, không có edge từ funding
- Funding Rate cực cao (+0.3%): LONG bị siết mạnh, sắp có long squeeze

--- Liquidation Cascades ---
- Khi BTC tăng nhanh qua vùng giá nhiều lệnh SHORT: SHORT squeeze → tăng cực nhanh
- Khi BTC giảm nhanh qua vùng giá nhiều lệnh LONG: LONG cascade → giảm không đáy
- Sau liquidation cascade: thường có pullback/bounce ngược chiều mạnh
- KHÔNG vào lệnh cùng chiều sau khi liquidation cascade đã xảy ra (đã muộn)

--- Fear & Greed Index ---
- 0-10 (Extreme Fear): capitulation, đáy thị trường → BUY mạnh
- 10-25 (Fear): cơ hội mua, người khác đang sợ
- 25-50 (Neutral): thị trường cân bằng
- 50-75 (Greed): thị trường tích cực, giữ vị thế
- 75-90 (Greed cao): cẩn thận, cân nhắc take profit
- 90-100 (Extreme Greed): TOPPING signal, bán mạnh, market sắp đỉnh

--- On-Chain Metrics ---
- Exchange Inflows tăng đột biến: cá voi chuẩn bị bán → bearish
- Exchange Outflows tăng: cá voi rút về cold wallet → bullish (HODL)
- Whale accumulation (ví lớn mua): bullish signal dài hạn
- Miner selling: bear market signal (miners cần tiền mặt)
- Stablecoin supply tăng: tiền mới vào sẵn sàng mua → bullish

--- Crypto-Specific Patterns ---
- "Buy the rumor, sell the news": giá tăng trước event (halving, ETF approval), bán khi tin ra
- Weekend pump/dump: thanh khoản thấp, dễ bị manipulation
- Asia session (2h-8h UTC): thường có volume thấp hơn
- US session (13h-20h UTC): volume cao nhất, quyết định trend ngày
- Month-end/Quarter-end: tái cân bằng quỹ, hay có biến động
"""

FUTURES_KNOWLEDGE = """
=== KIẾN THỨC FUTURES TRADING CHUYÊN SÂU ===

--- Cơ Chế Futures ---
- LONG: cược giá tăng. Lợi nhuận = (giá_ra - giá_vào) × size
- SHORT: cược giá giảm. Lợi nhuận = (giá_vào - giá_ra) × size
- Leverage 2x: lời/lỗ nhân 2, liquidation khi lỗ 50% margin (hệ thống này: 80%)
- Leverage 5x: lời/lỗ nhân 5, liquidation khi lỗ 20% margin (hệ thống này: 80%/5 = 16%)
- Margin = số tiền thực bỏ ra đặt cọc
- Position size = Margin × Leverage

--- Liquidation Price ---
- LONG liquidation = entry_price × (1 - 1/leverage × 0.8)
- SHORT liquidation = entry_price × (1 + 1/leverage × 0.8)
- Ví dụ LONG BTC $80,000 leverage 5x: liq tại $80,000 × (1 - 0.16) = $67,200
- Càng high leverage → liq price càng gần → rủi ro cao hơn

--- Khi Nào Nên LONG ---
- BTC vừa breakout ATH, volume xác nhận
- Sau short squeeze (funding rate âm rồi đột ngột về 0)
- Giá test lại EMA200 và giữ vững
- RSI oversold (< 35) trong uptrend dài hạn
- On-chain: exchange outflows tăng (cá voi rút coin về)
- Fear & Greed < 25 (thị trường sợ quá mức)

--- Khi Nào Nên SHORT ---
- RSI > 80 sau pump mạnh không có fundamental
- Funding rate cực cao (> 0.1%), quá nhiều người LONG
- Bearish divergence: giá tạo đỉnh mới, RSI không theo
- Giá reject mạnh tại vùng kháng cự lớn (old ATH, số tròn)
- Exchange inflows đột biến (cá voi chuẩn bị bán)
- Fear & Greed > 90 (extreme greed = gần đỉnh)
- Tin tức tốt đã ra nhưng giá không tăng thêm (sell the news)

--- Position Management ---
- Không bao giờ để 1 vị thế chiếm > 30% balance
- Nếu uPnL âm > 20% margin: xem xét đóng sớm để bảo toàn
- Partial take profit: đóng 50% khi +15%, để 50% chạy tiếp
- Không add vào vị thế thua (averaging down với leverage = rất nguy hiểm)
- Stop loss mềm: nếu thesis sai (BTC đảo chiều), đóng không cần đợi liq

--- Long/Short Hedge Strategy ---
- Khi thị trường không rõ hướng: LONG BTC + SHORT altcoin rủi ro cao
- Market neutral: LONG asset mạnh + SHORT asset yếu cùng ngành
- Hedge portfolio: giữ spot coin + SHORT futures để bảo vệ giá trị

--- Risk:Reward Ratio ---
- Chỉ vào lệnh khi R:R >= 2:1 (tiềm năng lời 2x so với rủi ro thua)
- Target LONG: +15-25% | Stop loss: -8%
- Target SHORT: +10-20% | Stop loss: -8%
- Với leverage 3x: +5% giá = +15% margin → R:R tốt hơn spot nhiều
"""

MACRO_SIGNALS = """
=== TÍN HIỆU VĨ MÔ (MACRO) ===

--- USD & Fed Policy ---
- DXY (Dollar Index) tăng → BTC/Gold giảm (ngược chiều)
- DXY giảm → BTC/Gold tăng (thuận chiều)
- Fed tăng lãi suất: risk-off, crypto giảm
- Fed giảm lãi suất / dovish: risk-on, crypto tăng
- CPI cao hơn dự báo: có thể bearish ngắn hạn (Fed phải tăng lãi)
- CPI thấp hơn dự báo: bullish (Fed có thể giảm lãi sớm hơn)

--- Bitcoin Halving Cycle ---
- Halving xảy ra mỗi ~4 năm, giảm phần thưởng mining 50%
- Pattern lịch sử: tăng mạnh 12-18 tháng SAU halving
- Pre-halving: tích lũy (accumulation phase)
- Post-halving bull run: thường đạt ATH mới

--- Geopolitical Risk ---
- Chiến tranh / bất ổn: ban đầu bán tháo, sau đó gold/BTC tăng (safe haven)
- Regulations crypto: bearish ngắn hạn, dài hạn tùy nội dung
- ETF approval / institutional adoption: bullish mạnh và bền vững
- Hack exchange lớn: panic sell toàn thị trường (cơ hội mua đáy)

--- Commodity Markets (12 tài sản) ---

PRECIOUS METALS (Kim loại quý — trú ẩn an toàn):
- XAU (Gold): tăng khi USD yếu, lạm phát cao, bất ổn địa chính trị, Fed dovish
- XAG (Silver): tăng cùng gold nhưng biến động mạnh hơn 2-3x; còn dùng trong công nghiệp (pin mặt trời, chip)
- XPT (Platinum): hiếm hơn gold, dùng trong xe hơi (catalytic converter) & hydrogen fuel cell; tăng khi auto sector phục hồi
- COPPER (Đồng): "Dr. Copper" — phong vũ biểu kinh tế toàn cầu; tăng khi kinh tế tăng trưởng, construction boom

ENERGY (Năng lượng):
- WTI (Dầu thô Mỹ): tăng khi OPEC+ cắt sản lượng, địa chính trị Trung Đông căng thẳng, mùa hè (driving season)
- BRENT (Dầu thô quốc tế): giá tham chiếu toàn cầu, thường cao hơn WTI $2-5; theo cùng động lực WTI
- NATGAS (Khí tự nhiên): cực kỳ biến động theo mùa; tăng mạnh mùa đông (sưởi ấm), giảm mùa hè

AGRICULTURAL (Nông sản):
- WHEAT (Lúa mì): tăng khi hạn hán Mỹ/Ukraine/Úc, chiến tranh Nga-Ukraine (2 nước xuất khẩu lớn nhất)
- CORN (Ngô): tăng theo nhu cầu ethanol (xăng sinh học), thời tiết Midwest Mỹ (corn belt)
- COFFEE (Cà phê): tăng khi El Niño gây hạn hán Brazil/Colombia; biến động mạnh theo thời tiết
- SUGAR (Đường): theo sản lượng Brazil & Ấn Độ; tăng khi hạn hán, giảm khi được mùa
- COTTON (Bông): theo nhu cầu dệt may toàn cầu; tăng khi kinh tế tốt, giảm khi recession

TƯƠNG QUAN COMMODITY VỚI CRYPTO:
- Gold/Silver tăng mạnh → BTC thường tăng theo (cùng là "store of value" chống lạm phát)
- Oil > $100 → lạm phát tăng → Fed tăng lãi → crypto bearish
- NATGAS, WHEAT, CORN tăng mạnh → lạm phát toàn cầu → risk-off → crypto giảm ngắn hạn
- Copper giảm → kinh tế suy thoái → risk-off → crypto bearish

CHIẾN LƯỢC TRADE COMMODITY:
- Precious metals: mua khi USD (DXY) yếu hoặc Fed tín hiệu dovish; giữ dài hơn crypto
- Energy: mua WTI/BRENT trước mùa hè (Apr-May), trước mùa đông (Oct-Nov)
- NATGAS: biến động cực mạnh, vị trí nhỏ, chốt lời nhanh
- Agricultural: theo dõi thời tiết El Niño/La Niña; mùa vụ (harvest season) hay gây bán tháo

--- Nhóm tài sản mở rộng (30 mã mới) ---
- Large-cap alt: BCH (Bitcoin Cash), XMR (Monero/privacy), HBAR (Hedera/enterprise)
- DeFi blue-chip: AAVE (lending), CRV (DEX liquidity), COMP (lending), SNX (synthetic), GRT (indexing)
- Meme coins (rủi ro cao, biến động mạnh): PEPE, WIF, BONK, FLOKI, NOT → theo sentiment & social, vị trí nhỏ, chốt lời nhanh
- AI / Infra: RENDER (GPU on-chain), PYTH (oracle), JUP (DEX aggregator Solana)
- New L1/L2: KAS (Kaspa/PoW nhanh), SEI (DeFi L1), TIA (Celestia/modular), STRK (Starknet/ZK), FTM (Fantom/EVM)
- Gaming/Metaverse: MANA, SAND, AXS, FLOW → tăng khi có game event, giảm mạnh khi thị trường down
- Privacy coins: ZEC, DASH → tăng khi regulatory pressure cao
- Bitcoin ecosystem: STX (Stacks/BTC L2), EGLD (MultiversX)
"""

RISK_MANAGEMENT = """
=== QUẢN LÝ RỦI RO CHUYÊN NGHIỆP ===

--- Position Sizing ---
- Kelly Criterion: stake% = (win_rate × avg_win - avg_loss) / avg_win
- Thực tế: dùng 25-50% Kelly để an toàn hơn
- Không bao giờ risk > 2% tổng balance cho 1 giao dịch
- Ví dụ: balance $5000, risk 2% = $100 per trade max loss

--- Portfolio Heat ---
- Total risk đang mở không vượt 10-15% balance
- Nếu đang lỗ 3 lệnh liên tiếp: giảm size 50%, review strategy
- Drawdown > 20%: dừng giao dịch, không double down để gỡ

--- Correlation Risk ---
- Khi mở nhiều vị thế: kiểm tra correlation (BTC & ETH corr ~0.85)
- 3 LONG khác nhau nhưng đều crypto = không diversified thực sự
- Hedge thực sự: LONG crypto + LONG gold + SHORT high-beta altcoin

--- Psychological Traps ---
- FOMO (Fear of Missing Out): mua đuổi sau khi đã tăng 20% → tránh
- Revenge trading: lỗ rồi vào lệnh lớn hơn để gỡ → tự hủy
- Confirmation bias: chỉ tìm tin ủng hộ luận điểm mình muốn → nguy hiểm
- Sunk cost fallacy: giữ lỗ vì "đã mất rồi, bán thì xác nhận thua" → cắt lỗ luôn

--- Quản Lý Danh Mục Tối Ưu ---
- Cash buffer 20-30%: luôn có tiền để bắt cơ hội bất ngờ
- Pyramid into winners: thêm vị thế khi đang lời (không khi đang lỗ)
- Trim losers early: cắt lỗ sớm, đừng để lỗ lớn
- Let winners run: đừng chốt lời quá sớm khi trend còn mạnh
"""

MARKET_PSYCHOLOGY = """
=== TÂM LÝ THỊ TRƯỜNG ===

--- Smart Money vs Retail ---
- Smart money tích lũy khi sideway/downtrend (khi retail sợ)
- Smart money phân phối khi uptrend/euphoria (khi retail FOMO)
- Dấu hiệu smart money vào: volume tăng đột biến khi giá sideways
- Dấu hiệu smart money thoát: volume tăng nhưng giá không tăng thêm

--- Market Sentiment Phases ---
1. Disbelief: "đây là bear trap" sau khi tăng mạnh từ đáy
2. Hope: bắt đầu tin có thể uptrend
3. Optimism: mua thêm, kỳ vọng tốt
4. Belief: trend rõ ràng, mọi người tự tin
5. Thrill: cảm giác thiên tài, tăng leverage
6. Euphoria: TOPPING — đây là điểm nguy hiểm nhất
7. Complacency: "chỉ là điều chỉnh nhỏ"
8. Anxiety: bắt đầu lo lắng
9. Denial: "sẽ hồi lại thôi"
10. Panic: bán tháo
11. Capitulation: bán hết, bỏ cuộc → ĐÂY LÀ ĐÁY
12. Anger/Depression: "crypto xong rồi"

--- Contrarian Thinking ---
- Khi 90% người bullish → thường là đỉnh
- Khi 90% người bearish → thường là đáy
- Twitter/Reddit toàn tin xấu? → Đáy gần
- Mainstream media cover crypto là tin tốt? → Đỉnh gần
- Altcoins mọi thứ đều tăng kể cả rác? → SELL EVERYTHING, đỉnh sắp tới

--- Seasonal Patterns ---
- "Sell in May and go away": tháng 5-6 thường yếu
- Q4 (Oct-Dec): historically strongest quarter cho BTC
- January effect: altcoin thường tăng đầu năm
- Pre-halving accumulation: 6 tháng trước halving thường tăng dần
"""

COMMODITY_TRADING = """
=== COMMODITY TRADING THỰC CHIẾN ===

--- PRECIOUS METALS: Vàng (XAU) & Bạc (XAG) ---
LONG XAU khi:
✅ DXY (Dollar Index) giảm xuống dưới MA20 → vàng tăng ngược chiều USD
✅ Fed tuyên bố dovish (giảm lãi suất, QE) → real yield âm → vàng hưởng lợi
✅ Lạm phát CPI vượt kỳ vọng → vàng là hedge lạm phát
✅ Bất ổn địa chính trị (chiến tranh, khủng hoảng ngân hàng) → safe haven
✅ XAU/USD giảm về MA200 (hỗ trợ cực mạnh) + RSI < 40
✅ Tháng 8-9: mùa cưới Ấn Độ → nhu cầu vàng tăng theo mùa
SHORT XAU khi:
❌ Fed hawkish, tăng lãi suất mạnh → USD tăng → vàng giảm
❌ Risk-on toàn cầu (chứng khoán tăng mạnh) → dòng tiền rời safe haven
❌ XAU vượt ATH quá nhanh không có fundamental → overbought

LONG XAG (Bạc) khi:
✅ XAU tăng nhưng XAG chưa tăng theo → bạc lag, cơ hội catch-up
✅ Nhu cầu công nghiệp tăng: pin mặt trời, xe điện, chip bán dẫn
✅ XAU/XAG ratio > 80 → bạc rẻ tương đối so với vàng → mua bạc
SHORT XAG khi: ratio < 60 (bạc đắt tương đối), recession risk cao

PLATINUM (XPT):
- Dùng trong catalytic converter xe hơi → tăng khi auto sales tốt
- Hydrogen economy growth → XPT là catalyst → dài hạn bullish
- Thường thấp hơn vàng → bất thường, thường sẽ hồi về trên XAU

COPPER (Đồng):
- "Dr. Copper" dự báo GDP toàn cầu: tăng = kinh tế khỏe
- LONG khi: China PMI > 50, infrastructure spending tăng, EV boom
- SHORT khi: China slowdown, recession signals, inventory tồn kho cao

--- ENERGY: Dầu (WTI & BRENT) & Khí Đốt (NATGAS) ---
LONG WTI/BRENT khi:
✅ OPEC+ cắt sản lượng (thường thông báo tháng 6 và 11)
✅ Mùa hè Mỹ (Jun-Aug): driving season, nhu cầu xăng tăng
✅ Mùa đông (Nov-Jan): nhu cầu heating oil tăng
✅ Căng thẳng Trung Đông (Iran, Saudi Arabia) → supply disruption
✅ EIA Weekly Inventory Report: tồn kho giảm mạnh hơn dự báo → bullish
✅ WTI giảm về $60-70: production cost của shale oil → sàn hỗ trợ mạnh
SHORT WTI/BRENT khi:
❌ Recession signals (GDP âm, thất nghiệp tăng) → nhu cầu giảm
❌ OPEC+ bất đồng, tăng sản lượng → supply glut
❌ USD mạnh lên nhanh (dầu định giá bằng USD)
❌ EIA báo tồn kho tăng đột biến

BRENT vs WTI: BRENT thường cao hơn $2-5 do logistics. Khi spread giãn rộng > $10 → cơ hội arbitrage.

NATGAS (Khí Tự Nhiên) — biến động nhất trong các commodity:
LONG khi:
✅ Mùa đông lạnh hơn dự báo (La Niña winters)
✅ Heatwave mùa hè → điện điều hòa → gas cho điện
✅ Tồn kho gas thấp hơn 5-year average
✅ LNG export demand tăng (châu Âu thiếu gas)
SHORT khi:
❌ Mùa đông ấm hơn bình thường (El Niño)
❌ Tồn kho cao hơn 5-year average
❌ Sản lượng shale gas Mỹ tăng kỷ lục
⚠️ NATGAS biến động 5-10%/ngày thường xuyên → leverage thấp, position nhỏ

--- AGRICULTURAL: Nông Sản ---
WHEAT (Lúa Mì):
LONG khi: Hạn hán tại Mỹ/Ukraine/Nga/Úc (4 nước xuất khẩu lớn nhất)
LONG khi: Chiến sự Ukraine leo thang → supply disruption
SHORT khi: Mùa thu hoạch tốt (Jul-Aug Bắc bán cầu)
KEY: USDA World Agriculture Supply and Demand Estimates (WASDE) report hàng tháng

CORN (Ngô):
LONG khi: Nhu cầu ethanol tăng (giá dầu cao) + hạn hán Midwest Mỹ
SHORT khi: Mùa thu hoạch Mỹ (Sep-Nov) → nguồn cung dồi dào
CORRELATION: Corn và Ethanol cùng chiều với WTI oil

COFFEE (Cà Phê):
LONG khi: El Niño gây hạn hán Brazil (xuất khẩu 40% thế giới)
LONG khi: Frost ở Minas Gerais, Brazil (tháng 6-7) → mất mùa
SHORT khi: Được mùa Brazil + Colombia, tồn kho ICE tăng

SUGAR (Đường):
LONG khi: Brazil chuyển mía sang ethanol thay vì đường (khi oil cao)
LONG khi: Hạn hán Ấn Độ (xuất khẩu #2 thế giới)
SHORT khi: Brazil được mùa + giá dầu thấp (ít ethanol demand)

COTTON (Bông):
LONG khi: Kinh tế toàn cầu khỏe mạnh → nhu cầu dệt may tăng
SHORT khi: Recession → tiêu dùng giảm; polyester (từ dầu) thay thế

--- KEY REPORTS CẦN THEO DÕI ---
- EIA Petroleum Status Report: thứ 4 hàng tuần (US oil inventory)
- EIA Natural Gas Storage Report: thứ 5 hàng tuần
- USDA WASDE Report: ngày 10-12 hàng tháng (grains & oilseeds)
- CFTC Commitment of Traders (COT): thứ 6 hàng tuần (ai đang long/short)
- US Dollar Index (DXY): ngược chiều với XAU, XAG, dầu, hầu hết commodity
- China PMI: ngày 1 hàng tháng (chỉ số nhu cầu commodity từ China)

--- COMMODITY CORRELATION MATRIX ---
XAU ↑ ↔ DXY ↓ (ngược chiều mạnh nhất, r ≈ -0.8)
XAU ↑ ↔ XAG ↑ (cùng chiều, bạc lag ~2-4 giờ)
WTI ↑ ↔ BRENT ↑ (gần như song song, r > 0.95)
WTI ↑ ↔ CORN ↑ (ethanol demand link)
WTI ↑ ↔ XAU ↑ (cùng tăng khi lạm phát, nhưng không phải lúc nào)
COPPER ↑ ↔ AUD/USD ↑ (Australia xuất khẩu đồng lớn)
NATGAS ↑ ↔ XAU ↑ (inflation hedge cùng chiều)

--- COMMODITY vs CRYPTO: KHI NÀO CHỌN CÁI NÀO ---
Chọn XAU/XAG khi: thị trường crypto bearish, USD yếu, risk-off
Chọn WTI/BRENT khi: kinh tế toàn cầu tăng trưởng, crypto sideways
Chọn NATGAS khi: mùa đông/hè rõ rệt, tìm cơ hội ngắn hạn nhanh
Chọn WHEAT/CORN khi: geopolitical shock, weather events rõ ràng
Kết hợp: LONG XAU + SHORT meme coin = hedge portfolio hiệu quả
"""

ADVANCED_TECHNICALS = """
=== KỸ THUẬT NÂNG CAO (THỰC CHIẾN) ===

--- Wyckoff Method (Phân tích cung/cầu) ---
ACCUMULATION PHASE (tích lũy — smart money mua):
1. Preliminary Support (PS): volume tăng, giảm bắt đầu chậm lại
2. Selling Climax (SC): volume khổng lồ + giá drop mạnh = capitulation
3. Automatic Rally (AR): bounce mạnh sau SC
4. Secondary Test (ST): retest vùng SC, volume thấp hơn = bullish
5. Last Point of Support (LPS): đáy cao hơn đáy trước → BUY
6. Sign of Strength (SOS): breakout khỏi range + volume cao → confirm

DISTRIBUTION PHASE (phân phối — smart money bán):
1. Preliminary Supply (PSY): volume tăng, giá khó tăng thêm
2. Buying Climax (BC): volume khổng lồ + giá spike = blow-off top
3. Automatic Reaction (AR): drop nhanh sau BC
4. Secondary Test (ST): retest BC, volume thấp = bearish
5. Upthrust After Distribution (UTAD): fake breakout lên → SHORT
6. Sign of Weakness (SOW): breakdown + volume cao → confirm bearish

--- Smart Money Concepts (ICT/SMC) ---
LIQUIDITY POOLS: Vùng tập trung stop loss của retail
- Equal highs: nhiều đỉnh cùng mức → stop loss của shorts ở đó → smart money sweep lên rồi đảo chiều
- Equal lows: nhiều đáy cùng mức → stop loss của longs ở đó → smart money sweep xuống rồi đảo chiều
- Wick extremes (cái đuôi nến dài): nơi stop loss bị hunt nhiều nhất

ORDER BLOCKS: Vùng giá smart money đặt lệnh lớn
- Bullish OB: nến đỏ cuối cùng trước khi có impulse tăng mạnh → hỗ trợ mạnh
- Bearish OB: nến xanh cuối cùng trước khi có impulse giảm mạnh → kháng cự mạnh
- Price thường quay lại test OB trước khi tiếp tục xu hướng

FAIR VALUE GAPS (FVG) / Imbalance:
- Khoảng trống giá (3 nến: nến 1 high < nến 3 low) = không có giao dịch ở đó
- Price có xu hướng "fill the gap" — quay lại lấp đầy FVG
- Bullish FVG: support; Bearish FVG: resistance

BREAK OF STRUCTURE (BOS) & CHANGE OF CHARACTER (CHoCH):
- BOS: giá phá đỉnh/đáy trước → xu hướng tiếp tục
- CHoCH: giá phá ngược (đang uptrend nhưng phá đáy trước) → đảo chiều
- CHoCH là signal sớm nhất để nhận biết reversal

--- Volume Profile & Market Profile ---
Point of Control (POC): mức giá giao dịch nhiều nhất trong session
- Giá về POC thường tìm hỗ trợ/kháng cự
- Breakout khỏi POC với volume cao = trend mạnh

Value Area (VA): 70% volume giao dịch trong vùng này
- Value Area High (VAH): kháng cự
- Value Area Low (VAL): hỗ trợ
- Giá nằm ngoài VA thường quay lại (mean reversion)

High Volume Node (HVN): vùng giá tập trung volume → hỗ trợ/kháng cự
Low Volume Node (LVN): vùng giá ít giao dịch → giá đi qua nhanh (air pocket)

--- Order Flow & Tape Reading ---
Delta (Buy volume - Sell volume):
- Delta dương cao + giá tăng = buying pressure thật sự
- Delta âm + giá tăng = sellers đang absorb buyers → sắp đảo chiều (bearish)
- Delta dương + giá giảm = buyers bị overwhelmed → tiếp tục giảm

Absorption: giá không di chuyển dù có volume lớn
- Buy absorption tại hỗ trợ: sellers đang bán nhưng buyers absorb hết → sắp tăng
- Sell absorption tại kháng cự: buyers đang mua nhưng sellers absorb hết → sắp giảm

--- Intermarket Analysis (Phân tích đa thị trường) ---
BTC vs SPX (S&P 500):
- Correlation cao (r > 0.7) khi macro risk-on/off dominate
- Khi SPX tăng + BTC không tăng: BTC yếu, cẩn thận
- Khi SPX giảm + BTC đứng vững: BTC đang decoupling → bullish signal

BTC vs Gold:
- Cùng tăng: risk-off + inflation hedge đồng thời → macro uncertainty
- Ngược chiều: BTC risk-on, Gold safe-haven (phổ biến hơn)

DXY vs Crypto vs Gold:
- DXY tăng → tất cả giảm (dollar mạnh = tiền về Mỹ)
- DXY giảm → BTC + Gold + Oil + Commodity tăng đồng loạt

US10Y (Treasury Yield) vs Crypto:
- Yield tăng nhanh → crypto giảm (cost of capital tăng)
- Yield peak và bắt đầu giảm → crypto bắt đầu recovery

--- Specific Entry Techniques ---
PULLBACK ENTRY (an toàn nhất):
1. Xác nhận trend (EMA20 > EMA50 > EMA200)
2. Đợi pullback về EMA20 hoặc 38.2% Fibonacci
3. Đợi nến confirmation (Hammer, Bullish Engulfing)
4. Vào với stop loss dưới swing low gần nhất
5. Target: 2x risk (R:R = 2:1 tối thiểu)

BREAKOUT ENTRY:
1. Xác định vùng consolidation (range rõ ràng 3+ nến)
2. Chờ close TRÊN kháng cự (không vào khi chỉ wick qua)
3. Volume phải > 150% trung bình 20 phiên
4. Vào khi retest lại vùng breakout (giá quay về test support mới)
5. Stop loss: ngay dưới vùng breakout

REVERSAL ENTRY (rủi ro cao hơn):
1. Xác nhận divergence (RSI hoặc MACD)
2. Đợi nến reversal mạnh (Engulfing, Pin Bar dài)
3. Volume spike khi reversal
4. Chỉ vào 30-50% position, add thêm khi confirm
5. Invalidation rõ ràng: nếu giá tiếp tục phá đáy/đỉnh cũ → out

--- Thời Điểm Vào Lệnh Tối Ưu ---
US Market Open (14:30-16:00 UTC+7): volume cao nhất ngày
- Hay có false breakout đầu phiên → đợi 15 phút sau open
- Trending moves thường bắt đầu sau 15:00 UTC+7

Asian Session (00:00-08:00 UTC+7):
- Volume thấp, hay sideway
- Tốt cho range trading, không tốt cho breakout

London Open (15:00-17:00 UTC+7):
- Volume tăng đột biến
- Hay sweep liquidity (stop hunt) rồi đảo chiều

Weekly Open (Monday 00:00 UTC):
- Hay có gap và stop hunt → đợi confirm hướng trước khi vào

--- Thoát Lệnh Thông Minh ---
Partial Take Profit (chốt từng phần):
- Chốt 30% tại R:R 1:1 → gần như chắc thắng
- Chốt 40% tại R:R 2:1 → lợi nhuận tốt
- Để 30% chạy với trailing stop → bắt big move

Trailing Stop:
- Trailing 1.5x ATR (Average True Range) từ đỉnh
- Hoặc: move stop lên breakeven khi đạt R:R 1:1
- Hoặc: đặt stop dưới swing low mới nhất mỗi khi giá tạo high mới

KHÔNG nên:
- Chốt lời quá sớm khi trend còn mạnh (volume chưa cạn)
- Giữ lệnh qua major news events nếu không chắc hướng
- Chốt lời vì "sợ lỗ" khi đang lời — cảm xúc kill profits
"""

PRACTICAL_STRATEGIES = """
=== CHIẾN LƯỢC THỰC CHIẾN THEO TỪNG ĐIỀU KIỆN ===

--- Scenario 1: THỊ TRƯỜNG BULL RUN (BTC > ATH, fear&greed > 75) ---
✅ Ưu tiên LONG mọi thứ
✅ Mua altcoin (SOL, AVAX, NEAR) lag sau BTC
✅ Tăng leverage futures lên 2-3x
✅ Không SHORT trừ khi có divergence rõ ràng
✅ Meme coins (PEPE, WIF, DOGE): mua khi pullback về EMA20
✅ Commodity: XAU, XAG cùng tăng → mua dip
❌ Không giữ quá nhiều cash → tiền mặt lạm phát nhanh trong bull market

--- Scenario 2: THỊ TRƯỜNG BEAR (BTC < MA200, fear&greed < 25) ---
✅ Ưu tiên SHORT hoặc giữ tiền mặt
✅ LONG XAU, XAG (safe haven flows)
✅ SHORT altcoin yếu (chúng giảm 2-3x BTC)
✅ SHORT meme coin (không có fundamental, giảm 80-90%)
✅ Leverage thấp (1-2x tối đa) — drawdown rất nhanh
❌ Không "bắt đáy" sớm — bear market kéo dài hơn dự kiến
❌ Không buy dip altcoin vô tội vạ

--- Scenario 3: SIDEWAYS/CONSOLIDATION (BTC trong range 2-3 tuần) ---
✅ Range trading: mua tại support, bán tại resistance
✅ LONG commodity có seasonal pattern rõ (NATGAS mùa đông, CORN mùa hè)
✅ Chú ý commodity reports (EIA, USDA) → breakout cơ bản
✅ Spot: tích lũy BTC, ETH từng đợt nhỏ (DCA)
✅ Futures: lower size, vào tại extreme (RSI <25 or >75)
❌ Tránh leverage cao khi sideways — theta decay và fake breakout costly

--- Scenario 4: MACRO SHOCK (Fed bất ngờ, war, bank crisis) ---
✅ Thoát vị thế ngay (preserve capital)
✅ LONG XAU mạnh (safe haven #1 trong shock)
✅ LONG XAG nếu XAU đã tăng nhanh
✅ Sau shock 1-3 ngày: tìm cơ hội LONG BTC (recovery trade)
❌ Không SHORT quá muộn sau khi đã drop 20%+ (đã quá muộn)
❌ Không LONG khi chưa biết shock kéo dài bao lâu

--- Scenario 5: COMMODITY SUPPLY SHOCK ---
Oil supply shock (war, OPEC cut):
✅ LONG WTI + BRENT ngay
✅ LONG XAU (lạm phát kỳ vọng tăng)
✅ SHORT tech stocks (chi phí sản xuất tăng)
✅ SHORT NATGAS nếu WTI > $100 (switching fuels)

Grain supply shock (drought/war):
✅ LONG WHEAT + CORN ngay
✅ LONG COFFEE nếu El Niño được xác nhận
✅ LONG XAU (inflation hedge)

Metal supply shock (mine strike, export ban):
✅ LONG COPPER, XAG nhanh
✅ LONG XPT nếu liên quan auto sector

--- Scenario 6: ALTSEASON (BTC.D giảm, ETH/BTC tăng) ---
Dấu hiệu altseason:
✅ BTC.D giảm từ >60% xuống <50%
✅ ETH/BTC tăng liên tục 2+ tuần
✅ SOL, AVAX, NEAR, INJ lead thị trường
✅ DeFi TVL tăng đột biến

Chiến lược:
✅ Chuyển từ BTC → ETH → Large cap alts → Small cap alts (theo thứ tự)
✅ Gaming tokens (AXS, SAND, MANA) thường pump cuối altseason
✅ AI tokens (RENDER, GRT) pump khi AI narrative hot
✅ Chốt lời altcoin nhanh hơn BTC — altcoin dump mạnh hơn khi kết thúc

--- Scenario 7: LIQUIDATION CASCADE ---
Khi BTC giảm 5-8% trong 1 giờ:
✅ Chờ cascade kết thúc (volume spike + giá dừng giảm)
✅ Đợi 15-30 phút sau khi bounce xuất hiện
✅ LONG nhỏ với stop loss chặt (3% dưới entry)
✅ Target: 50-61.8% Fibonacci retracement của cú drop
❌ Không LONG trong khi đang cascading (dao rơi)
❌ Không SHORT sau khi đã drop 10%+ (đã muộn, bounce risk cao)

--- KIM NGẠCH THỰC TIỄN CỦA TRADER THÀNH CÔNG ---
1. Risk/Reward: KHÔNG vào lệnh nếu R:R < 1.5:1
2. Win rate 50% + R:R 2:1 = profitable dài hạn (expectancy dương)
3. Không bao giờ risk > 2% balance trên 1 trade
4. Nếu thua 3 lệnh liên tiếp: dừng, nghỉ ngơi, review
5. Ghi chép journal: entry, exit, lý do, bài học → cải thiện liên tục
6. Best trades thường đơn giản và rõ ràng — phức tạp thường sai
7. "The market can stay irrational longer than you can stay solvent" — Keynes
8. Đừng predict, hãy react: đợi confirmation rồi mới vào
"""


def get_crypto_knowledge() -> str:
    """Knowledge base đầy đủ cho crypto spot bots."""
    return (
        TECHNICAL_ANALYSIS
        + ADVANCED_TECHNICALS
        + CRYPTO_MARKET_STRUCTURE
        + COMMODITY_TRADING
        + MACRO_SIGNALS
        + RISK_MANAGEMENT
        + MARKET_PSYCHOLOGY
        + PRACTICAL_STRATEGIES
    )


def get_futures_knowledge() -> str:
    """Knowledge base đầy đủ cho futures long/short bots."""
    return (
        TECHNICAL_ANALYSIS
        + ADVANCED_TECHNICALS
        + CRYPTO_MARKET_STRUCTURE
        + FUTURES_KNOWLEDGE
        + COMMODITY_TRADING
        + MACRO_SIGNALS
        + RISK_MANAGEMENT
        + MARKET_PSYCHOLOGY
        + PRACTICAL_STRATEGIES
    )
