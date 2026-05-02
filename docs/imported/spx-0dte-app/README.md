# SPX 0DTE Institutional Decision Support Engine

This application is a real-time decision-support tool designed to operationalize the **SPX 0DTE Institutional Playbook**. It translates complex auction market theory (Market Profile, TPO, Order Flow) into deterministic trading recommendations.

## 🛠 Tech Stack
- **Frontend**: React 18 + Vite
- **Language**: TypeScript (Strict Typing)
- **Styling**: Vanilla CSS (Institutional Dark Mode)
- **Icons**: Lucide-React

## 📂 Project Structure for Developers

The application is structured to decouple the trading logic (the "Engine") from the UI.

### 1. The Core Engine (`/src/engine/DecisionEngine.ts`)
The "Brain" of the app. It contains the heavy lifting logic:
- `classifyRegime()`: Analyzes Tier 1/2 evidence to map current market state to one of the 13 Regimes (R1-R13).
- `checkTier4Constraints()`: The "Governor". Checks portfolio state (Delta, Gamma, PnL) against hard institutional limits.
- `calculateSizing()`: Calculates unit sizing based on setup Grade (A+ to D) and an exponential time-of-day decay.
- `recommendStructures()`: Maps Regimes to specific option structures (Iron Condors, Debit Verticals, etc.) while flagging "bad fits".

### 2. Data Models (`/src/types/index.ts`)
Strict TypeScript definitions for the entire Playbook:
- Enums for **Regimes**, **PathFamilies**, and **Grades**.
- Structured interfaces for **MarketEvidence** (Tiers 1-3) and **PortfolioState** (Tier 4).

### 3. Primary Components (`/src/components/`)
- **Dashboard.tsx**: The "Live" view. Real-time inputs for market state and portfolio limits.
- **Simulator.tsx**: A scenario-based testing tool. Allows developers/traders to step through time-series events (e.g., a "Gap & Failed Repair" scenario) to see how the engine reacts.
- **AuditModule.tsx**: A post-trade grading system. Implements the **15-Dimension Scoring Rubric** from the Playbook to calculate process quality.

## 🎯 Key Functionality
- **Dynamic Reclassification**: The engine handles transitions (e.g., if a Reversion attempt fails, it triggers an R7 reclassification).
- **Hard Stops**: Tier 4 violations (like Orphaned Legs) take precedence over all logic and lock the UI into a "Remediation Required" state.
- **Strike Selection Logic**: Recommendations include specific strike placement math (e.g., "Short strike at IB High", "10pts behind Single Prints").
- **Time-Decay Sizing**: Automatically reduces conviction/sizing as the session progresses toward the 0DTE expiration wall.

## 🚀 Getting Started
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## 📜 Business Logic Source
All logic is derived from the `SPX_0DTE_Institutional_Playbook.md` (Version: Options Auction Matrix Opus).
