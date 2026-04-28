"""Compact professional reference cards for 0DTE SPX inventory work."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceCard:
    topic: str
    what_it_means: str
    why_it_matters_0dte: str
    operating_implication: str
    common_error: str
    verification_inputs: tuple[str, ...]
    deep_dive: str = ""
    mental_model: str = ""
    key_mechanics: tuple[str, ...] = ()


REFERENCE_TOPICS = (
    "Dealer gamma / GEX",
    "Zero-gamma flip",
    "Vanna and charm",
    "Skew and structure selection",
    "Variance risk premium",
    "SPX/SPXW execution microstructure",
    "PM cash settlement",
    "Futures hedging",
    "Cost realism",
    "Behavioral lockouts",
    "Modern 0DTE structural risk",
    "Source / broker verification checklist",
)


def list_reference_topics() -> tuple[str, ...]:
    """Return static reference-card topics."""
    return REFERENCE_TOPICS


def get_reference_cards() -> list[ReferenceCard]:
    """Return compact static professional reference cards."""
    return [
        ReferenceCard(
            topic="Dealer gamma / GEX",
            what_it_means="Positive GEX can dampen movement; negative GEX can amplify trend or whipsaw.",
            why_it_matters_0dte="Same-day expiry can make hedge-flow character dominate short-window path risk.",
            operating_implication="Use GEX as regime context, never as a trade signal.",
            common_error="Reading GEX as a forecast instead of a regime input.",
            verification_inputs=(
                "dealer-flow source timestamp",
                "aggregate GEX estimate",
                "OI and volume context",
            ),
            deep_dive=(
                "When you trade an option, a market maker (dealer) takes the other side. "
                "If you buy a call, the dealer is short that call and must hedge by buying "
                "the underlying as the price rises, or selling as it falls. This hedging "
                "activity is mechanical — it is not a view on direction.\n\n"
                "Gamma Exposure (GEX) aggregates how much hedging activity all dealers are "
                "estimated to need across all strikes and expirations. Positive GEX means "
                "dealers are net long gamma: when price moves up, they sell; when it moves "
                "down, they buy. This creates a dampening effect — a natural mean-reversion "
                "force that tends to compress realized volatility.\n\n"
                "Negative GEX is the opposite. Dealers are net short gamma: price moves up, "
                "they must buy more; price moves down, they must sell more. This is a "
                "volatility-amplifying regime where moves can accelerate and whipsaw.\n\n"
                "Crucially, GEX is an estimate, not a measured fact. Different models produce "
                "different numbers depending on assumptions about customer vs. dealer "
                "positioning. It is a regime descriptor, not a crystal ball."
            ),
            mental_model=(
                "Think of positive GEX like driving with shock absorbers — bumps get "
                "smoothed out. Negative GEX is like driving without shocks on a rough "
                "road — every bump gets amplified and the ride gets increasingly violent."
            ),
            key_mechanics=(
                "Dealer hedging is mechanical (delta-neutral), not directional",
                "Positive GEX = dealers sell rallies and buy dips (dampening)",
                "Negative GEX = dealers buy rallies and sell dips (amplifying)",
                "GEX is an estimate from models, not a directly measured quantity",
                "Same-day 0DTE gamma can dominate the aggregate number near expiry",
            ),
        ),
        ReferenceCard(
            topic="Zero-gamma flip",
            what_it_means="A regime boundary where estimated hedge-flow character may change.",
            why_it_matters_0dte="Acceptance across the flip can shift expected dampening or amplification.",
            operating_implication="Reduce authorization when spot chops around the flip.",
            common_error="Treating the flip as a literal price barrier.",
            verification_inputs=(
                "flip estimate source",
                "current spot reference",
                "model timestamp",
            ),
            deep_dive=(
                "The zero-gamma flip is the price level where aggregate dealer gamma "
                "exposure crosses from positive to negative (or vice versa). Above the "
                "flip, dealers may be in a dampening regime; below it, an amplifying one. "
                "The exact level depends on the model used to estimate dealer positioning.\n\n"
                "This is not a support or resistance level. It does not 'hold' price or "
                "'reject' price. It is a regime boundary — a line where the character of "
                "dealer hedging flow is estimated to change. When price is well above or "
                "below the flip, the regime is relatively clear. When price is chopping "
                "around the flip level, the regime is ambiguous and hedging flow is mixed.\n\n"
                "The practical consequence: when spot oscillates around the flip, you lose "
                "the ability to lean on regime context for your positioning. You do not "
                "know whether the next move will be dampened or amplified. This uncertainty "
                "itself is the risk — and it argues for reducing position authorization, "
                "not trying to trade the flip as a level."
            ),
            mental_model=(
                "Imagine a weather boundary between high and low pressure systems. When "
                "you are clearly in one zone, conditions are predictable. When you are right "
                "on the boundary, weather becomes unstable and hard to forecast. The flip "
                "is that boundary — not a wall, but a zone of regime uncertainty."
            ),
            key_mechanics=(
                "The flip is where aggregate GEX crosses zero — not a fixed number",
                "Above flip (positive GEX): dampening regime expectation",
                "Below flip (negative GEX): amplifying regime expectation",
                "Near the flip: regime is ambiguous, reduce discretionary authorization",
                "Different GEX models can produce different flip estimates",
            ),
        ),
        ReferenceCard(
            topic="Vanna and charm",
            what_it_means="Hedge-flow context from volatility sensitivity and time decay.",
            why_it_matters_0dte="Vol crush and time decay can force hedge changes when positioning is concentrated.",
            operating_implication="Use vanna and charm as context, not standalone entries.",
            common_error="Treating spot movement as the only hedge driver.",
            verification_inputs=(
                "surface snapshot",
                "time to expiry",
                "position Greeks from platform",
            ),
            deep_dive=(
                "Most traders think of delta as the only reason dealers hedge. But delta "
                "itself changes for two additional reasons beyond spot movement: changes in "
                "implied volatility (vanna) and the passage of time (charm).\n\n"
                "Vanna measures how much an option's delta changes when implied volatility "
                "changes. When IV drops (vol crush), out-of-the-money options lose delta "
                "rapidly. Dealers who were hedging that delta must unwind those hedges. If "
                "many dealers unwind in the same direction simultaneously, the resulting "
                "flow can move the market — independent of any change in spot price.\n\n"
                "Charm measures how much delta changes purely from time passing. As expiry "
                "approaches, out-of-the-money options lose delta (they become less likely "
                "to finish in the money). This forces dealers to unwind hedges gradually "
                "throughout the day. On 0DTE specifically, charm is extreme — options that "
                "are even slightly OTM can see their delta collapse in hours.\n\n"
                "Together, vanna and charm mean that significant hedge-flow can occur even "
                "when price is flat. A vol crush after a morning catalyst, or the steady "
                "time-decay of afternoon 0DTE positions, can both generate meaningful "
                "directional flow from dealer rebalancing."
            ),
            mental_model=(
                "Delta is the engine of dealer hedging, but vanna and charm are invisible "
                "hands on the steering wheel. Vanna turns the wheel when the market's fear "
                "level changes; charm turns it simply because the clock is ticking. On 0DTE, "
                "the clock ticks extremely fast."
            ),
            key_mechanics=(
                "Vanna = change in delta per change in implied volatility",
                "Charm = change in delta per passage of time (theta of delta)",
                "Vol crush forces rapid delta unwind via vanna — flow without spot movement",
                "0DTE charm is extreme: OTM options lose delta very fast as hours pass",
                "Concentrated positioning amplifies both effects into visible market flow",
            ),
        ),
        ReferenceCard(
            topic="Skew and structure selection",
            what_it_means="Structure choice must account for skew, not direction alone.",
            why_it_matters_0dte="Rich skew may be compensation for real tail risk.",
            operating_implication="Avoid short premium into negative-gamma movement without regime proof.",
            common_error="Choosing structure from direction while ignoring skew.",
            verification_inputs=(
                "option chain snapshot",
                "skew measure",
                "term and strike comparison",
            ),
            deep_dive=(
                "Volatility skew describes the pattern where out-of-the-money puts trade "
                "at higher implied volatility than equidistant out-of-the-money calls. This "
                "is not a market inefficiency — it reflects the empirical reality that equity "
                "indices crash down, not up. Downside moves are faster, larger, and more "
                "correlated than upside moves.\n\n"
                "When you see a put spread collecting apparently rich credit, that richness "
                "is the market pricing in tail risk. Selling that premium is not 'free money' "
                "— it is accepting the risk that a rare but severe move wipes out many "
                "days of collected credit in a single session.\n\n"
                "Structure selection must respect skew. A directional view alone is "
                "insufficient — if you are bearish and want to use a put credit spread, you "
                "must verify that the skew premium you are collecting is genuinely rich "
                "relative to realized risk, not just nominally high. Comparing implied "
                "volatility across strikes and expirations reveals whether skew is steep "
                "(tail-risk demand is high) or flat (market is complacent).\n\n"
                "On 0DTE, skew dynamics are compressed into hours. A steep morning skew can "
                "flatten rapidly as time decay accelerates, changing the risk profile of "
                "your structure mid-session."
            ),
            mental_model=(
                "Skew is like flood insurance pricing — homes near the river pay more, not "
                "because floods happen daily, but because when they do happen, the damage "
                "is catastrophic. Rich put premiums are the market's flood insurance. "
                "Collecting that premium means you are the insurance company."
            ),
            key_mechanics=(
                "OTM puts trade at higher IV than OTM calls — this is normal, not mispriced",
                "Rich premium on puts reflects real tail-risk compensation",
                "Compare skew across strikes and expirations, not just absolute IV levels",
                "Steep skew = market pricing in fear; flat skew = relative complacency",
                "0DTE skew can shift rapidly intraday as time decay compresses the surface",
            ),
        ),
        ReferenceCard(
            topic="Variance risk premium",
            what_it_means="Implied volatility must be rich versus expected realized volatility after costs.",
            why_it_matters_0dte="Compressed VRP can make short premium unattractive even with time decay.",
            operating_implication="Judge VRP by regime and costs, not theta alone.",
            common_error="Assuming premium decay is enough without realized-vol context.",
            verification_inputs=(
                "implied volatility inputs",
                "realized volatility context",
                "event calendar",
            ),
            deep_dive=(
                "The variance risk premium (VRP) is the historical tendency for implied "
                "volatility to exceed realized volatility. Options tend to be priced for "
                "more movement than actually occurs, creating a structural edge for premium "
                "sellers — on average, over long periods.\n\n"
                "The trap is in those last three words. VRP is a statistical property of "
                "large samples. On any single day, realized vol can massively exceed implied "
                "vol. A 0DTE position that collects theta is not automatically profitable — "
                "it is only profitable if the realized path stays within what the collected "
                "premium can absorb.\n\n"
                "VRP compresses during low-vol regimes when implied vol is already low. "
                "There is less 'cushion' between what you collect and what can happen. It "
                "also compresses ahead of known catalysts (earnings, FOMC, data releases) "
                "where the market has already priced in an expected move. Selling premium "
                "into a compressed VRP means accepting near-fair odds while still bearing "
                "the full tail risk.\n\n"
                "The operating discipline is to assess VRP as a regime input: is implied vol "
                "genuinely rich relative to recent and expected realized vol, net of all "
                "execution costs? If not, theta alone does not justify the position."
            ),
            mental_model=(
                "VRP is like the house edge at a casino — it exists on average over "
                "thousands of hands, but any single hand can lose the table limit. "
                "Theta is not edge; it is the price of a lottery ticket your counterparty "
                "holds. VRP tells you whether that ticket is overpriced or fairly priced."
            ),
            key_mechanics=(
                "VRP = implied volatility minus realized volatility (historically positive)",
                "Positive VRP does not guarantee profit on any single trade",
                "Low-vol regimes compress VRP — less cushion for premium sellers",
                "Event days can invert VRP entirely (realized exceeds implied)",
                "Always subtract friction costs before assessing whether VRP is attractive",
            ),
        ),
        ReferenceCard(
            topic="SPX/SPXW execution microstructure",
            what_it_means="Multi-leg mids can be non-fillable; routing and wing availability matter.",
            why_it_matters_0dte="A valid adjustment can be operationally invalid if it cannot be filled.",
            operating_implication="Verify actual liquidity, route behavior, and wing availability.",
            common_error="Assuming theoretical mid value is executable.",
            verification_inputs=(
                "broker quote display",
                "route availability",
                "market width history",
            ),
            deep_dive=(
                "SPX options are European-style, cash-settled, and trade on Cboe. The "
                "original SPX product settles AM (opening price Friday); SPXW (weeklys, "
                "including 0DTE) settles PM (closing price). This distinction matters for "
                "settlement risk and final-hour behavior.\n\n"
                "When you see a 'mid price' on a multi-leg spread, that mid is a theoretical "
                "construct. It is the average of the composite bid and ask across all legs. "
                "No market maker is obligated to fill at mid. On a 4-leg iron condor, the "
                "composite width can easily be several dollars, and the actual fillable "
                "price may be significantly worse than mid.\n\n"
                "Liquidity in SPX options is concentrated near the money and in high-volume "
                "expirations. Wings (far OTM strikes used as spread boundaries) can have "
                "very wide markets or no displayed size. A spread that looks attractive on "
                "paper may be unfillable if the wing strike has no liquidity.\n\n"
                "Routing matters too. Some brokers use smart routing that may split legs "
                "across exchanges; others require the complex order to fill as a package. "
                "Legging risk (getting filled on one side but not the other) is a real "
                "operational hazard. Always verify that your broker's routing supports the "
                "structure you intend to trade, and confirm actual displayed size before "
                "committing to an adjustment."
            ),
            mental_model=(
                "The mid price is like a Zillow estimate — it is a computed number, not "
                "an actual offer anyone has made. You cannot 'execute at mid' any more than "
                "you can force a home to transact at its Zestimate. The real price is what "
                "someone will actually trade with you at, right now."
            ),
            key_mechanics=(
                "SPX = AM-settled; SPXW (including 0DTE) = PM-settled, European-style",
                "Multi-leg mid price is theoretical — not an executable quote",
                "Composite spread width grows with each additional leg",
                "Wing strikes may have wide markets or zero displayed size",
                "Verify broker routing: package fill vs. leg-by-leg execution risk",
            ),
        ),
        ReferenceCard(
            topic="PM cash settlement",
            what_it_means="Same-day PM cash settlement compresses time into the closing window.",
            why_it_matters_0dte="Final-hour short gamma is not justified by theta alone.",
            operating_implication="Use close-by-time discipline over squeezing final pennies.",
            common_error="Treating final-hour gamma as harmless because settlement is cash.",
            verification_inputs=(
                "exchange product specs",
                "broker expiry notes",
                "position exercise settings",
            ),
            deep_dive=(
                "SPXW 0DTE options settle based on the closing price of SPX at the end of "
                "the regular trading session (PM settlement). Unlike equity options, there "
                "is no physical delivery — settlement is purely cash. This sounds simpler "
                "but creates a specific risk: the entire remaining life of your position "
                "compresses into the final trading hours.\n\n"
                "As expiry approaches, gamma on near-the-money options explodes. A position "
                "that was manageable at 10am can become unmanageable by 3pm, not because "
                "the market moved, but because time decay has made the position hyper-"
                "sensitive to small moves. A 2-point SPX move at 3:30pm can produce the "
                "same P/L swing that would have required a 10-point move at 10am.\n\n"
                "Cash settlement also means there is no exercise decision to manage — but "
                "it does not eliminate risk. The settlement price is determined by a "
                "specific calculation, and your broker may have auto-liquidation rules "
                "that trigger before settlement. The discipline is simple: set a close-by "
                "time and honor it, rather than holding through the final hour hoping to "
                "squeeze out remaining theta."
            ),
            mental_model=(
                "Final-hour gamma is like standing on a see-saw as it gets shorter. Early "
                "in the day, the see-saw is long and stable. As expiry approaches, it "
                "shrinks — the same small step produces a much larger tilt. Cash settlement "
                "does not make the see-saw safer; it just means you fall onto cash, not stock."
            ),
            key_mechanics=(
                "SPXW 0DTE uses PM settlement — based on closing SPX price",
                "Near-expiry gamma explodes: small spot moves create large P/L swings",
                "Cash settlement eliminates exercise risk but not gamma risk",
                "Brokers may auto-liquidate before settlement on their own schedule",
                "Close-by-time discipline overrides the temptation to hold for final theta",
            ),
        ),
        ReferenceCard(
            topic="Futures hedging",
            what_it_means="ES or MES hedging is temporary delta inventory control.",
            why_it_matters_0dte="It can reduce path exposure without changing option structure.",
            operating_implication="Every hedge needs removal, reassessment, or close trigger.",
            common_error="Letting hedge inventory become a directional view.",
            verification_inputs=(
                "current option delta",
                "contract multiplier",
                "futures exposure per point",
            ),
            deep_dive=(
                "When your option position has unwanted delta exposure, you can offset it "
                "temporarily by trading ES (E-mini, 50x multiplier) or MES (Micro E-mini, "
                "5x multiplier) futures. This is not a new trade — it is inventory control "
                "on your existing position.\n\n"
                "The math: if your SPX option position has +15 deltas (equivalent to being "
                "long 15 shares of SPX), and each MES contract gives you 5 deltas of "
                "exposure, you would need 3 MES contracts short to neutralize. The hedge "
                "converts your directional position into a delta-neutral one while you "
                "reassess or wait for conditions to clarify.\n\n"
                "The critical discipline: every futures hedge must have a removal plan. "
                "If the option position is closed, the hedge must come off. If the thesis "
                "changes, the hedge must be reassessed. A futures hedge without a removal "
                "trigger is not a hedge — it is a second unmanaged directional bet that "
                "you will forget about under pressure.\n\n"
                "Futures also have their own margin requirements, which add to your total "
                "capital at risk. The hedge reduces directional risk but increases "
                "operational complexity."
            ),
            mental_model=(
                "A futures hedge is a temporary bandage, not a cure. It stops the bleeding "
                "while you decide whether to close the wound or let it heal. But if you "
                "forget the bandage is there, it becomes part of the problem — you now have "
                "two things to manage instead of one."
            ),
            key_mechanics=(
                "ES = 50x SPX multiplier; MES = 5x SPX multiplier",
                "Hedge size = option delta exposure divided by futures delta per contract",
                "Every hedge must have an explicit removal or reassessment trigger",
                "Forgetting to remove a hedge creates a new unmanaged directional position",
                "Futures margin adds to total capital at risk — hedging is not free",
            ),
        ),
        ReferenceCard(
            topic="Cost realism",
            what_it_means="Every adjustment must survive commissions, fees, and spread crossing.",
            why_it_matters_0dte="Gross credit or debit is not the same as executable edge.",
            operating_implication="If costs do not improve the position, close is superior.",
            common_error="Judging adjustment quality before friction is counted.",
            verification_inputs=(
                "broker fee schedule",
                "actual fills",
                "spread crossing estimate",
            ),
            deep_dive=(
                "Every option trade has friction: commissions, exchange fees, regulatory "
                "fees, and the cost of crossing the spread. On a 4-leg iron condor with "
                "entry and exit, you are paying friction on 8 individual option transactions. "
                "This friction is subtracted from your gross credit or added to your gross "
                "debit — it is real cost that reduces your actual edge.\n\n"
                "The most dangerous moment for cost blindness is during adjustments. When "
                "a position is under pressure, the instinct is to 'fix' it by rolling, "
                "converting, or adding legs. Each adjustment adds another layer of friction. "
                "A roll that collects a small net credit may actually be net-negative after "
                "commissions and spread crossing on all legs.\n\n"
                "Spread crossing is often the largest hidden cost. If each leg of a 4-leg "
                "spread crosses the spread, and each crossing costs you a few cents of "
                "premium, the total cost can consume a meaningful percentage of your gross "
                "target. When friction exceeds 25% of your gross target, the trade or "
                "adjustment requires explicit justification — because you are giving away "
                "a quarter of your expected profit before the market even moves."
            ),
            mental_model=(
                "Friction is like sales tax on trading. You do not notice it on one small "
                "purchase, but if you are buying and returning items all day (adjusting), "
                "the tax alone can exceed the value of what you are trying to save. "
                "Sometimes the cheapest adjustment is closing."
            ),
            key_mechanics=(
                "Total friction = commissions + exchange fees + regulatory fees + spread cost",
                "A 4-leg spread with entry and exit = 8 individual option transactions",
                "Spread crossing cost is often the largest single friction component",
                "Adjustments add new layers of friction on top of existing friction",
                "When friction exceeds 25% of gross target, explicit justification is needed",
            ),
        ),
        ReferenceCard(
            topic="Behavioral lockouts",
            what_it_means="When behavior is impaired, discretion collapses.",
            why_it_matters_0dte="Fast expiry magnifies loss-repair behavior and rushed discretion.",
            operating_implication="Limit actions to reduce, close, temporary hedge, flatten, or stop.",
            common_error="Using conversions, rolls, widening, or added risk under impairment.",
            verification_inputs=(
                "daily rule log",
                "loss limit status",
                "authorization checklist",
            ),
            deep_dive=(
                "Behavioral lockouts are pre-committed rules that restrict your own "
                "discretion when conditions indicate impairment. The logic is simple: when "
                "you are losing money, under time pressure, and emotionally activated, your "
                "decision quality degrades in predictable ways — specifically toward loss-"
                "repair behavior, revenge trading, and widening risk to avoid realizing "
                "losses.\n\n"
                "On 0DTE, these tendencies are amplified by time compression. There is no "
                "'sleep on it' option. A loss at 2pm feels urgent because the position "
                "expires in two hours. This urgency creates pressure to 'do something' — "
                "convert the spread, roll to a different strike, widen the wings — all of "
                "which add risk and friction while your judgment is impaired.\n\n"
                "The lockout system works by pre-defining which actions are available when "
                "certain conditions are met (daily loss exceeded, multiple adjustments made, "
                "thesis invalidated). Under lockout, the only authorized actions are: "
                "reduce size, close the position, apply a temporary futures hedge, flatten "
                "entirely, or stop trading for the day. No new risk, no conversions, no "
                "'just one more adjustment.' The decisions were made when you were calm — "
                "trust them when you are not."
            ),
            mental_model=(
                "Lockouts are like a circuit breaker on your electrical panel. When the "
                "system is overloaded, the breaker trips automatically — you do not get to "
                "override it because you think the toaster 'really needs' more power. The "
                "breaker exists because your judgment under overload is exactly when you "
                "need protection most."
            ),
            key_mechanics=(
                "Lockout triggers: daily loss limit, adjustment count, thesis invalidation",
                "Allowed under lockout: reduce, close, temporary hedge, flatten, stop",
                "Forbidden under lockout: conversions, rolls, widening, adding new risk",
                "Loss-repair behavior is the primary cognitive risk during 0DTE drawdowns",
                "Lockout rules are set when calm and followed when activated — no overrides",
            ),
        ),
        ReferenceCard(
            topic="Modern 0DTE structural risk",
            what_it_means="Modern 0DTE flow can alter intraday dealer positioning quickly.",
            why_it_matters_0dte="Pinning is not guaranteed when flow and gamma shift quickly.",
            operating_implication="Avoid backfitting post-2022 behavior from older option behavior.",
            common_error="Assuming pinning will rescue unmanaged gamma.",
            verification_inputs=(
                "time window",
                "liquidity condition",
                "structure risk map",
            ),
            deep_dive=(
                "Before 2022, 0DTE trading was a niche activity. Since the Cboe expanded "
                "daily SPX expirations to every trading day, 0DTE volume has exploded — "
                "regularly exceeding 40-50% of total SPX option volume. This has "
                "fundamentally changed the microstructure of the market.\n\n"
                "The key structural change: massive 0DTE gamma can now appear and disappear "
                "within a single session. A large 0DTE position opened at 10am creates "
                "dealer gamma exposure that did not exist at 9:30am and will not exist "
                "at 4pm. This means the dealer positioning landscape can shift dramatically "
                "intraday — GEX estimates from the morning may be obsolete by afternoon.\n\n"
                "Older assumptions about option market behavior — especially pinning (price "
                "gravitating toward strikes with high open interest) — were developed when "
                "option positioning was relatively stable day-to-day. In the modern 0DTE "
                "regime, pinning is unreliable because the gamma profile itself is changing "
                "throughout the day as new 0DTE positions are opened and closed.\n\n"
                "The practical risk: do not use backtests or historical patterns from before "
                "2022 as reliable guides for 0DTE behavior today. The market structure has "
                "changed, and strategies that worked in the old regime may behave differently "
                "in a market dominated by same-day expiration flow."
            ),
            mental_model=(
                "Pre-2022 options markets were like a lake — the surface was mostly stable "
                "and patterns repeated. Post-2022 0DTE markets are more like a river with "
                "tidal influence — the current changes direction during the day as massive "
                "flows enter and exit. Fishing techniques from the lake do not automatically "
                "transfer to the river."
            ),
            key_mechanics=(
                "0DTE volume now regularly exceeds 40-50% of total SPX option volume",
                "Intraday gamma can appear and disappear within a single session",
                "Morning GEX estimates may be stale by afternoon due to new 0DTE flow",
                "Pinning assumptions from pre-2022 are unreliable in the new regime",
                "Historical backtests before 2022 may not reflect current microstructure",
            ),
        ),
        ReferenceCard(
            topic="Source / broker verification checklist",
            what_it_means="Product mechanics need Cboe, OCC, OIC, and broker verification.",
            why_it_matters_0dte="Broker rules control margin, routing, spread handling, and liquidation.",
            operating_implication="Verify source, broker rule, symbol, expiry, and position state.",
            common_error="Assuming reference cards have live broker or market-data access.",
            verification_inputs=(
                "Cboe OCC OIC sources",
                "broker rule page",
                "current platform settings",
            ),
            deep_dive=(
                "Options product mechanics are defined by multiple layers of rules: the "
                "exchange (Cboe) defines the product specifications, the OCC (Options "
                "Clearing Corporation) defines clearing and settlement rules, and your "
                "broker adds its own layer of margin, routing, and auto-liquidation rules "
                "on top.\n\n"
                "These layers can conflict or surprise you. For example, Cboe may list a "
                "strike, but your broker may not support it for spreads. The OCC defines "
                "exercise and assignment rules, but your broker may have different thresholds "
                "for auto-exercise. Margin requirements are set by the exchange but your "
                "broker often applies more conservative house requirements.\n\n"
                "Verification means checking each layer independently. Do not assume that "
                "because a trade appears on your platform, it will behave as you expect. "
                "Confirm: What is the exact product symbol and expiry? What are the "
                "settlement terms? Does your broker support the specific spread type? What "
                "are the margin implications? What happens if you hold through expiry — "
                "does the broker auto-close, auto-exercise, or let it settle?\n\n"
                "This workstation does not have live broker or market-data access. Every "
                "product mechanic, rule, and specification mentioned here must be verified "
                "against primary sources before trading."
            ),
            mental_model=(
                "Think of it like checking three different maps before driving: the road map "
                "(exchange rules), the traffic rules (OCC/clearing), and your car's GPS "
                "(broker platform). All three may show slightly different routes and "
                "restrictions. You need to check all three to know what will actually happen."
            ),
            key_mechanics=(
                "Cboe defines product specs; OCC defines clearing; broker adds house rules",
                "Broker margin requirements are often stricter than exchange minimums",
                "Auto-liquidation and auto-exercise rules vary by broker — verify yours",
                "A strike listed on the exchange may not be available for spreads at your broker",
                "This workstation has no live data access — always verify against primary sources",
            ),
        ),
    ]
