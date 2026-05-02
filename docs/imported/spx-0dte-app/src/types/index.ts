// src/types/index.ts

export const Regime = {
  R1: 'R1: Open In Value, Rotational',
  R2: 'R2: Open Outside Value, Rejected',
  R3: 'R3: Open Outside Value, Accepted',
  R4: 'R4: Value Migration Lower',
  R5: 'R5: Value Migration Higher',
  R6: 'R6: Trend Continuation',
  R7: 'R7: Failed Repair Into Prior Value',
  R8: 'R8: Established New Balance',
  R9: 'R9: Responsive Bounce',
  R10: 'R10: Restoration / Reclaim',
  R11: 'R11: Late Short-Covering Distortion',
  R12: 'R12: Late Long-Liquidation Distortion',
  R13: 'R13: Late Compression / Pin Risk',
  NONE: 'Grade D / No Regime / Ambiguous'
} as const;

export type Regime = typeof Regime[keyof typeof Regime];

export const PathFamily = {
  CONTAINMENT_ROTATION: 'Containment / Rotation',
  RESPONSIVE_BOUNCE: 'Responsive Bounce',
  INITIATIVE_CONTINUATION: 'Initiative Continuation',
  VALUE_MIGRATION: 'Value Migration',
  RESTORATION_RECLAIM: 'Restoration / Reclaim',
  FAILED_CONTINUATION_SNAPBACK: 'Failed Continuation / Snapback',
  LATE_COMPRESSION_PIN_RISK: 'Late Compression / Pin Risk',
  LIQUIDATION_EXTENSION: 'Liquidation Extension',
  NONE: 'None'
} as const;

export type PathFamily = typeof PathFamily[keyof typeof PathFamily];

export const Grade = {
  A_PLUS: 'A+',
  A: 'A',
  B: 'B',
  C: 'C',
  D: 'D'
} as const;

export type Grade = typeof Grade[keyof typeof Grade];

export const LifecycleStage = {
  STARTER: 'STARTER',
  CONFIRMATION_ADD: 'CONFIRMATION_ADD',
  FINAL_ADD: 'FINAL_ADD',
  MONETIZE_DISTRIBUTE: 'MONETIZE_DISTRIBUTE',
  EXIT: 'EXIT'
} as const;

export type LifecycleStage = typeof LifecycleStage[keyof typeof LifecycleStage];

export interface Tier1Evidence {
  insidePriorVA: boolean;
  ibExtension: boolean;
  pocAlignment: 'stable' | 'migrating_up' | 'migrating_down' | 'none';
  volumeQuality: 'initiative' | 'responsive' | 'low';
  oneTimeFraming: 'up' | 'down' | 'none';
  timeHorizontal: number; // hours
  scenarioContext: 'none' | 'failed_repair' | 'post_decline_bounce' | 'reclaim_attempt' | 'late_short_covering' | 'late_long_liquidation' | 'late_compression';
}

export interface Tier2Evidence {
  ibWidth: number; // pts
  gapSize: number; // pts
  excessAtExtreme: boolean;
  singlePrintsPresent: boolean;
}

export interface Tier3Evidence {
  absorptionAtEdges: boolean;
  deltaConfirming: boolean;
  higherLowLowerHigh: boolean;
  trappedTradersActive: boolean;
}

export interface Tier4PortfolioState {
  netDelta: number;
  netGamma: number;
  netTheta: number;
  openStructuresCount: number;
  distinctStrikesCount: number;
  openContractsCount: number;
  cashDeployedPercent: number;
  orphanedLegs: boolean;
  sessionPnLPercent: number;
  timeOfDayMinutes: number; // minutes from 9:30 AM (e.g., 60 = 10:30 AM)
}

export interface MarketEvidence {
  tier1: Tier1Evidence;
  tier2: Tier2Evidence;
  tier3: Tier3Evidence;
}

export interface SessionAudit {
  id: string;
  date: string;
  pnl: number;
  scores: Record<string, number>; // Dimensions 1 to 15 mapped to 0-10 score
  finalGrade: string;
}

export interface DecisionOutput {
  regime: Regime;
  path: PathFamily;
  grade: Grade;
  sizing: string;
  structuresRecommended: string[];
  inappropriateStructures: string[];
  managementAdvice: string;
  hardStopsTriggered: string[];
}
