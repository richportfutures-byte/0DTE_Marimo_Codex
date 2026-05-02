// src/engine/DecisionEngine.ts

import { Regime, PathFamily, Grade } from '../types';
import type { DecisionOutput, MarketEvidence, Tier4PortfolioState } from '../types';

export function checkTier4Constraints(portfolio: Tier4PortfolioState): string[] {
  const stops: string[] = [];

  if (portfolio.orphanedLegs) {
    stops.push('ORPHANED LEG PROTOCOL: Immediate remediation required. All other activity stops.');
  }
  if (Math.abs(portfolio.netDelta) >= 75) {
    stops.push('NET DELTA CAP: +/- 75 max. Distribute or hedge.');
  }
  if (portfolio.netGamma >= 50 || portfolio.netGamma <= -50) {
    stops.push('NET GAMMA CAP: +/- 50 max.');
  }
  if (portfolio.openStructuresCount >= 5) {
    stops.push('PORTFOLIO COMPLEXITY: Max 5 open structures. Close stale inventory.');
  }
  if (portfolio.distinctStrikesCount >= 12) {
    stops.push('PORTFOLIO COMPLEXITY: Max 12 distinct strikes. Strip outer legs.');
  }
  if (portfolio.openContractsCount >= 30) {
    stops.push('PORTFOLIO COMPLEXITY: Max 30 contracts total.');
  }
  if (portfolio.sessionPnLPercent >= 25) {
    stops.push('SESSION COMPLETE THRESHOLD: +25% reached. Active closure of all positions.');
  } else if (portfolio.sessionPnLPercent <= -5) {
    stops.push('EMERGENCY HARD STOP: -5% absolute account loss hit. Session complete.');
  }
  if (portfolio.cashDeployedPercent > 70) {
    stops.push('CAPITAL COMPRESSION: Free cash below 30%. No new deployment.');
  }

  return stops;
}

export function classifyRegime(evidence: MarketEvidence): { regime: Regime; path: PathFamily; conf: Grade } {
  const { tier1, tier3 } = evidence;
  
  let regime: Regime = Regime.NONE;
  let path: PathFamily = PathFamily.NONE;
  let conf: Grade = Grade.D;

  if (tier1.scenarioContext === 'failed_repair') {
    regime = Regime.R7; path = PathFamily.INITIATIVE_CONTINUATION; conf = Grade.A;
  } else if (tier1.scenarioContext === 'late_short_covering') {
    regime = Regime.R11; path = PathFamily.NONE; conf = Grade.D; // Management only
  } else if (tier1.scenarioContext === 'late_long_liquidation') {
    regime = Regime.R12; path = PathFamily.NONE; conf = Grade.D;
  } else if (tier1.scenarioContext === 'late_compression') {
    regime = Regime.R13; path = PathFamily.LATE_COMPRESSION_PIN_RISK; conf = Grade.D;
  } else if (tier1.scenarioContext === 'post_decline_bounce') {
    regime = Regime.R9; path = PathFamily.RESPONSIVE_BOUNCE; conf = Grade.B;
  } else if (tier1.scenarioContext === 'reclaim_attempt') {
    regime = Regime.R10; path = PathFamily.RESTORATION_RECLAIM; conf = Grade.A;
  } else if (tier1.insidePriorVA && !tier1.ibExtension && tier1.pocAlignment === 'stable') {
    regime = Regime.R1;
    path = PathFamily.CONTAINMENT_ROTATION;
    conf = (tier3.absorptionAtEdges && tier3.deltaConfirming) ? Grade.A_PLUS : Grade.A;
  } else if (!tier1.insidePriorVA) {
    // OPEN OUTSIDE VA BRANCH
    if (tier1.volumeQuality === 'responsive') {
      // R2: Open Outside, Rejected
      // Playbook Rule: Gap < 8 pts is No-Trade (Section 3.2)
      if (evidence.tier2.gapSize < 8) {
          regime = Regime.NONE;
          conf = Grade.D; 
      } else {
          regime = Regime.R2;
          path = PathFamily.RESPONSIVE_BOUNCE;
          conf = (tier3.deltaConfirming) ? Grade.A : Grade.B;
      }
    } else if (tier1.volumeQuality === 'initiative') {
      // R3: Open Outside, Accepted
      if (tier1.oneTimeFraming !== 'none') {
        regime = Regime.R6;
        path = PathFamily.INITIATIVE_CONTINUATION;
        conf = Grade.A_PLUS;
      } else {
        regime = Regime.R3;
        path = PathFamily.INITIATIVE_CONTINUATION; 
        conf = Grade.A;
      }
    }
  } else if (tier1.oneTimeFraming === 'down' && tier1.pocAlignment === 'migrating_down') {
    regime = Regime.R4;
    path = PathFamily.VALUE_MIGRATION;
    conf = Grade.A;
  } else if (tier1.oneTimeFraming === 'up' && tier1.pocAlignment === 'migrating_up') {
    regime = Regime.R5;
    path = PathFamily.VALUE_MIGRATION;
    conf = Grade.A;
  } else if (tier1.timeHorizontal >= 2 && tier1.pocAlignment === 'stable') {
    regime = Regime.R8;
    path = PathFamily.CONTAINMENT_ROTATION;
    conf = Grade.A;
  } else {
    regime = Regime.NONE;
    path = PathFamily.NONE;
    conf = Grade.D; // Was Grade.C - C should still get a probe, D means no read
  }
  
  return { regime, path, conf };
}

export function calculateSizing(grade: Grade, timeOfDayMins: number, existingPnl: number): string {
  let timeMultiplier = 1.0;
  if (timeOfDayMins > 60 && timeOfDayMins <= 150) timeMultiplier = 0.75; 
  else if (timeOfDayMins > 150 && timeOfDayMins <= 240) timeMultiplier = 0.50; 
  else if (timeOfDayMins > 240 && timeOfDayMins <= 330) timeMultiplier = 0.25; 
  else if (timeOfDayMins > 330) timeMultiplier = 0.0; 

  if (existingPnl >= 20) return "0.0 Units (Max Session PnL achieved, management only)";

  let base = 0;
  if (grade === Grade.A_PLUS) base = 2.0;
  else if (grade === Grade.A) base = 1.5;
  else if (grade === Grade.B) base = 1.0;
  else if (grade === Grade.C) base = 0.5;

  const final = base * timeMultiplier;
  
  if (final === 0.0) return "0.0 Units (NO TRADE)";
  if (final <= 0.25) return `${final.toFixed(2)} Units (PROBE ONLY) - No adds permitted`;
  
  const starter = (final * 0.5).toFixed(2);
  const add = (final * 0.5).toFixed(2);
  return `Total: ${final.toFixed(2)} Units. (Starter: ${starter}u | Confirmation Add: ${add}u)`;
}

export function recommendStructures(regime: Regime, evidence: MarketEvidence): { best: string[], bad: string[] } {
  const result = { best: [] as string[], bad: [] as string[] };
  
  switch (regime) {
    case Regime.R1:
      result.best = [
        'Iron Condors: Short strikes explicitly at IB High / IB Low.', 
        'Iron Butterflies: Centered exactly at developing POC.', 
        'Credit Spreads: Fading IB touches.'
      ];
      result.bad = ['Naked Singles', 'Wide Debit Spreads'];
      break;
    case Regime.R2:
      result.best = [
        'ATM Debit Verticals: Long ATM, Short at Prior VA edge (the expected stall). Width usually 15-25 pts.', 
        'Directional Butterflies: Center strike at Prior VA edge.'
      ];
      result.bad = ['Iron Condors', 'Credit Spreads betting on continuation'];
      break;
    case Regime.R3:
      result.best = ['Wide debit spreads in continuation', 'Iron Condors around new POC'];
      result.bad = ['Mean-reversion structures back toward prior VA'];
      break;
    case Regime.R4:
    case Regime.R5:
      result.best = [
        'ITM Debit Spreads: High delta, theta-efficient.', 
        'ATM Debit Verticals: Long ATM, Short 20-30 pts in migration direction.', 
        'Credit Spreads: Short strike 10+ pts BEHIND the migration pullback low/high.'
      ];
      result.bad = ['Call Spreads (if R4)', 'Iron Condors', 'Butterflies at abandoned levels'];
      break;
    case Regime.R6:
      result.best = [
        'Wide Debit Spreads: 50+ pt width, capture the tail. (Requires time)', 
        'Naked ATM Singles: For maximum delta capture.', 
        'OTM Runners: Small size only.'
      ];
      result.bad = ['Iron Condors', 'Butterflies', 'Narrow Debit Spreads'];
      break;
    case Regime.R7:
      result.best = [
        'ATM Debit Verticals: In displacement direction.', 
        'Wide Debit Spreads'
      ];
      result.bad = ['Any structure expressing reversion', 'Credit spreads in displacement direction'];
      break;
    case Regime.R8:
      result.best = ['Iron Condors at new balance edges', 'Butterflies at new POC'];
      result.bad = ['Wide Directional Debit Spreads'];
      break;
    case Regime.R9:
      result.best = ['Narrow ATM call debit verticals targeting first resistance', 'Small probe-size naked calls'];
      result.bad = ['Wide debit spreads', 'Any structure embedding large bullish path'];
      break;
    case Regime.R10:
      result.best = ['ATM debit verticals (20-30 pt width)', 'ITM debit spreads', 'Credit spreads behind reclaim'];
      result.bad = ['Structures positioned for bounce to fail', 'Naked singles'];
      break;
    case Regime.R11:
    case Regime.R12:
      result.best = ['No new deployment', 'Manage existing inventory'];
      result.bad = ['New long positions', 'New short positions'];
      break;
    case Regime.R13:
      result.best = ['Hold butterflies near current price', 'Close structures far from max-gain'];
      result.bad = ['New deployment', 'Structures with negligible time value'];
      break;
    case Regime.NONE:
      result.best = ['NO TRADE'];
      result.bad = ['ALL'];
      break;
    default:
      result.best = ['Consult specific Playbook section'];
      result.bad = ['Structures with large delta exposure'];
  }
  
  if (evidence.tier2.singlePrintsPresent) {
    result.best.push('🛑 SINGLE PRINTS DETECTED: Any Credit Spread short strikes must be placed minimum 10 pts BEHIND the nearer edge of Single Prints.');
  }
  if (evidence.tier3.trappedTradersActive) {
    result.best.push('🔥 TRAPPED TRADERS: Supports aggressive directional verticals targeting forced liquidity.');
  }
  if (evidence.tier2.excessAtExtreme) {
    result.best.push('⚖️ EXCESS DETECTED: Structural high/low is secure. Ideal anchor for credit spread short strikes or stops.');
  }

  return result;
}

export function processDecisionChain(evidence: MarketEvidence, portfolio: Tier4PortfolioState): DecisionOutput {
  const hardStops = checkTier4Constraints(portfolio);

  const { regime, path, conf } = classifyRegime(evidence);
  const sizing = calculateSizing(conf, portfolio.timeOfDayMinutes, portfolio.sessionPnLPercent);
  const { best, bad } = recommendStructures(regime, evidence);

  // Any hard stop blocks new deployment, but we still show the regime read
  if (hardStops.length > 0) {
      return {
          regime,
          path,
          grade: conf,
          sizing: '0.0 (NO TRADE)',
          structuresRecommended: [],
          inappropriateStructures: bad,
          managementAdvice: 'HARD STOP ACTIVE. Address Tier 4 violations before any new deployment.',
          hardStopsTriggered: hardStops
      };
  }

  if (conf === Grade.D || regime === Regime.NONE) {
      return {
          regime,
          path,
          grade: conf,
          sizing: '0.0 (NO TRADE)',
          structuresRecommended: [],
          inappropriateStructures: [],
          managementAdvice: 'No high-confidence regime read. Wait for clearer auction structure.',
          hardStopsTriggered: []
      };
  }

  const managementMap: Partial<Record<string, string>> = {
    [Regime.R1]: 'Range bound. First monetize at 50-70% max gain. Exit if IB extends with acceptance.',
    [Regime.R2]: 'First target: Prior VA edge. Scale 50-70% there. Stop: gap extreme retested with volume.',
    [Regime.R3]: 'If continuation: trail by prior 30-min TPO extreme. If new balance: pivot to theta structures.',
    [Regime.R4]: 'Strike centers must migrate with value. Bounces are monetization events, not reversals.',
    [Regime.R5]: 'Mirror R4. Trail by prior TPO period low. Pullbacks are adds, not stops.',
    [Regime.R6]: 'Trail stop: prior 30-min TPO exact extreme. Flatten gamma the instant OTF breaks.',
    [Regime.R7]: 'Close all R2 reversion positions immediately. Express new thesis in displacement direction.',
    [Regime.R8]: 'Theta-positive structures at new balance edges. Probe directional fades at extremes only.',
    [Regime.R9]: 'Target: first resistance only. Monetize 100% at target. Do NOT convert to R10 trade here.',
    [Regime.R10]: 'Allow 60+ minutes for reclaim to build. First partial at prior POC, full at prior VA edge.',
    [Regime.R11]: 'No new deployment. Manage existing bearish inventory — reduce against the squeeze.',
    [Regime.R12]: 'No new deployment. Manage existing bullish inventory — reduce against the liquidation.',
    [Regime.R13]: 'Hold butterflies near pin. Close structures far from max-gain zone. Extreme gamma risk.',
  };

  return {
    regime,
    path,
    grade: conf,
    sizing,
    structuresRecommended: best,
    inappropriateStructures: bad,
    managementAdvice: managementMap[regime] ?? 'Follow stage lifecycle. First monetization at 50-70% max gain.',
    hardStopsTriggered: []
  };
}
