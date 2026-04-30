"""Copy-ready session prompt templates for explicit 0DTE inputs."""

from dataclasses import dataclass


DATA_GUARDRAIL = (
    "Use only explicitly sourced inputs: user-supplied data or approved adapter "
    "data with source, timestamp, and freshness status. Mark missing, stale, "
    "partial, or unverifiable fields unknown or require manual confirmation. "
    "Do not invent fake data. Provide bounded decision support only; do not "
    "place, route, or imply automated order execution. Do not generate batch "
    "examples unless explicitly requested."
)


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
                "Classify the current 0DTE SPX session regime from explicit "
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
            template=f"""You are a professional 0DTE SPX/SPXW inventory reviewer.

{DATA_GUARDRAIL}

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
            template=f"""You are interpreting dealer-flow context for 0DTE SPX/SPXW inventory.

{DATA_GUARDRAIL}

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
                "Generate one data-anchored adjustment drill from explicit context, "
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
            template=f"""Create one 0DTE SPX/SPXW inventory adjustment drill.

{DATA_GUARDRAIL} Generate one scenario only.

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
            template=f"""Audit this proposed 0DTE SPX/SPXW strategy as a professional risk reviewer.

{DATA_GUARDRAIL}

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
            template=f"""Stress-test this claimed 0DTE SPX/SPXW edge. Default to insufficient evidence unless the edge survives cost, sample-size, regime, and execution tests.

{DATA_GUARDRAIL}

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
            template=f"""Review this completed 0DTE SPX/SPXW session as a hostile but fair professional risk reviewer.

{DATA_GUARDRAIL}

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
