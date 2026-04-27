"""Copy-ready session prompt templates for user-supplied 0DTE inputs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    purpose: str
    required_inputs: tuple[str, ...]
    template: str


PROMPT_WORKFLOWS = (
    "pre_session_regime_synthesis",
    "dealer_flow_interpretation",
    "adjustment_drill",
    "strategy_audit",
    "edge_hypothesis_stress_test",
    "post_session_review",
)


def list_prompt_workflows() -> tuple[str, ...]:
    """Return planned prompt workflow identifiers."""
    return PROMPT_WORKFLOWS


def get_session_prompt_templates() -> list[PromptTemplate]:
    """Return compact session prompt templates with explicit data guardrails."""
    return [
        PromptTemplate(
            name="Pre-session regime synthesis",
            purpose=(
                "Classify the current 0DTE SPX session regime from user-supplied "
                "dealer-flow, volatility, auction, and event inputs."
            ),
            required_inputs=(
                "aggregate GEX",
                "zero-gamma flip",
                "current SPX or ES level",
                "call wall",
                "put wall",
                "max-gamma strike",
                "VIX",
                "VIX1D",
                "VIX9D",
                "VVIX",
                "ES overnight range",
                "prior SPX high low close",
                "VWAP or auction context",
                "economic calendar",
                "overnight catalyst",
                "realized volatility context",
            ),
            template="""You are a professional 0DTE SPX/SPXW inventory reviewer.

Use only user-supplied data. Mark missing fields unknown. Do not invent fake data. Do not make live trade recommendations. Do not generate batch examples unless explicitly requested.

Inputs:
- aggregate GEX:
- zero-gamma flip:
- current SPX or ES level:
- call wall:
- put wall:
- max-gamma strike:
- VIX:
- VIX1D:
- VIX9D:
- VVIX:
- ES overnight range:
- prior SPX high low close:
- VWAP or auction context:
- economic calendar:
- overnight catalyst:
- realized volatility context:

Output:
- regime classification
- explicit reasoning
- relevant levels
- structures that fit
- structures forbidden
- no-trade conditions
- hedge and adjustment implications""",
        ),
        PromptTemplate(
            name="Dealer-flow interpretation",
            purpose=(
                "Interpret dealer-flow context without treating dealer levels as ordinary "
                "support/resistance."
            ),
            required_inputs=(
                "aggregate GEX",
                "zero-gamma flip",
                "current SPX",
                "distance from flip",
                "max-gamma strike",
                "call wall",
                "put wall",
                "day-over-day OI changes",
                "VIX1D VIX9D VIX VVIX",
                "auction context",
                "time of day",
            ),
            template="""You are interpreting dealer-flow context for 0DTE SPX/SPXW inventory.

Use only user-supplied data. Mark missing fields unknown. Do not invent fake data. Do not make live trade recommendations. Do not generate batch examples unless explicitly requested.

Inputs:
- aggregate GEX:
- zero-gamma flip:
- current SPX:
- distance from flip:
- max-gamma strike:
- call wall:
- put wall:
- day-over-day OI changes:
- VIX1D VIX9D VIX VVIX:
- auction context:
- time of day:

Do not treat dealer levels as ordinary support/resistance.

Output:
- dealer-flow regime
- expected hedge behavior
- whether spot is pulled toward or away from a magnetic strike
- auction confirmation or contradiction
- favored structures
- disfavored structures
- adjustment implications
- close/reduce triggers
- confidence and why""",
        ),
        PromptTemplate(
            name="One adjustment drill",
            purpose=(
                "Generate one data-anchored adjustment drill from user-supplied context, "
                "not a batch."
            ),
            required_inputs=(
                "dealer-gamma regime",
                "zero-gamma flip",
                "current spot relationship",
                "time of day",
                "VIX1D VIX9D VIX VVIX",
                "original structure",
                "entry fill",
                "original thesis",
                "current Greeks",
                "current bid/ask conditions",
                "current P/L",
                "risk remaining",
                "updated evidence",
            ),
            template="""Create one 0DTE SPX/SPXW inventory adjustment drill.

Use only user-supplied data. Mark missing fields unknown. If a required numeric field is missing, mark it unknown. Do not invent fake data. Do not make live trade recommendations. Do not generate batch examples unless explicitly requested. Generate one scenario only.

Inputs:
- dealer-gamma regime:
- zero-gamma flip:
- current spot relationship:
- time of day:
- VIX1D VIX9D VIX VVIX:
- original structure:
- entry fill:
- original thesis:
- current Greeks:
- current bid/ask conditions:
- current P/L:
- risk remaining:
- updated evidence:

Evaluate choices:
- close
- reduce
- hedge
- convert/restructure
- hold
- stop

Output:
- one scenario only
- correct decision
- why wrong answers are dangerous
- why adjustment is not the default answer
- fields that remain unknown""",
        ),
        PromptTemplate(
            name="Strategy audit",
            purpose="Audit a proposed 0DTE SPX strategy for professional viability.",
            required_inputs=(
                "strategy description",
                "structure",
                "regime assumption",
                "entry rule",
                "exit rule",
                "stop rule",
                "adjustment plan",
                "cost assumptions",
                "sample size",
                "observed win rate",
                "average win",
                "average loss",
                "dealer-flow assumption",
                "volatility assumption",
            ),
            template="""Audit this proposed 0DTE SPX/SPXW strategy as a professional risk reviewer.

Use only user-supplied data. Mark missing fields unknown. Do not invent fake data. Do not make live trade recommendations. Do not generate batch examples unless explicitly requested.

Inputs:
- strategy description:
- structure:
- regime assumption:
- entry rule:
- exit rule:
- stop rule:
- adjustment plan:
- cost assumptions:
- sample size:
- observed win rate:
- average win:
- average loss:
- dealer-flow assumption:
- volatility assumption:

Output:
- pass/fail by category
- critical flaws
- hidden assumptions
- data required
- modifications required
- status: tradable, simulation only, rejected, or needs more evidence""",
        ),
        PromptTemplate(
            name="Edge hypothesis stress test",
            purpose=(
                "Stress-test a claimed edge and default to insufficient evidence unless it "
                "survives cost, sample-size, regime, and execution tests."
            ),
            required_inputs=(
                "hypothesis",
                "typical structure",
                "per-leg cost",
                "spread crossing estimate",
                "average credit or debit",
                "claimed win rate",
                "average win",
                "average loss",
                "sample size",
                "regime filter",
                "dealer-flow assumption",
                "volatility assumption",
            ),
            template="""Stress-test this claimed 0DTE SPX/SPXW edge. Default to insufficient evidence unless the edge survives cost, sample-size, regime, and execution tests.

Use only user-supplied data. Mark missing fields unknown. Do not invent fake data. Do not make live trade recommendations. Do not generate batch examples unless explicitly requested.

Inputs:
- hypothesis:
- typical structure:
- per-leg cost:
- spread crossing estimate:
- average credit or debit:
- claimed win rate:
- average win:
- average loss:
- sample size:
- regime filter:
- dealer-flow assumption:
- volatility assumption:

Output:
- cost-adjusted breakeven
- embedded dealer-flow assumption
- embedded VRP assumption
- required volatility regime
- sample-size concerns
- worst drawdown regime
- survivorship-bias risk
- post-2022 0DTE regime risk
- execution friction risk
- evidence required
- rejection criteria""",
        ),
        PromptTemplate(
            name="Post-session review",
            purpose=(
                "Review a completed 0DTE SPX session as a hostile but fair professional "
                "risk reviewer."
            ),
            required_inputs=(
                "date",
                "trades taken",
                "structures",
                "entry times",
                "exit times",
                "entry thesis",
                "dealer-flow regime",
                "zero-gamma flip",
                "spot relative to flip",
                "VIX VIX1D VIX9D VVIX",
                "event calendar",
                "auction structure",
                "execution fills",
                "costs",
                "adjustments",
                "futures hedges",
                "final P/L",
                "screenshots or notes",
            ),
            template="""Review this completed 0DTE SPX/SPXW session as a hostile but fair professional risk reviewer.

Use only user-supplied data. Mark missing fields unknown. Do not invent fake data. Do not make live trade recommendations. Do not generate batch examples unless explicitly requested.

Inputs:
- date:
- trades taken:
- structures:
- entry times:
- exit times:
- entry thesis:
- dealer-flow regime:
- zero-gamma flip:
- spot relative to flip:
- VIX VIX1D VIX9D VVIX:
- event calendar:
- auction structure:
- execution fills:
- costs:
- adjustments:
- futures hedges:
- final P/L:
- screenshots or notes:

Output:
- regime call accuracy
- structure-selection quality
- entry quality
- execution quality
- cost-adjusted P/L
- adjustment quality
- hedge quality
- no-trade discipline
- rule adherence
- behavioral errors
- what to repeat
- what to prohibit next session
- one process rule to add or revise""",
        ),
    ]
