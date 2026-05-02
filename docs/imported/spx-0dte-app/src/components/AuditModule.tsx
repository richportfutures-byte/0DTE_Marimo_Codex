import { useState, useMemo } from 'react';
import type { SessionAudit } from '../types';

const dimensions = [
  "1. Regime Classification Quality",
  "2. Path Classification Quality",
  "3. Location Quality",
  "4. Order Flow Confirmation Quality",
  "5. Structure Selection Quality",
  "6. Size Discipline",
  "7. Timing Discipline for 0DTE",
  "8. Lifecycle Discipline",
  "9. Management Discipline",
  "10. Monetization Discipline",
  "11. Packaging Discipline",
  "12. Session Architecture Discipline",
  "13. Structural Integrity Quality",
  "14. Portfolio Awareness Quality",
  "15. Session Completion Quality"
];

export default function AuditModule() {
  const initialScores = useMemo(() => {
    const s: Record<string, number> = {};
    dimensions.forEach(d => (s[d] = 10));
    return s;
  }, []);

  const [scores, setScores] = useState<Record<string, number>>(initialScores);
  const [pnl, setPnl] = useState<number>(0);
  const [savedAudits, setSavedAudits] = useState<SessionAudit[]>([]);

  const handleScoreChange = (dim: string, val: number) => {
    setScores(prev => ({ ...prev, [dim]: val }));
  };

  const handleReset = () => {
    setScores(initialScores);
    setPnl(0);
  };

  // Rule: Overall grade is the LOWEST individual dimension score
  const lowestScore = Math.min(...Object.values(scores));
  let finalGrade = '';
  if (lowestScore >= 8) finalGrade = 'Excellent';
  else if (lowestScore >= 6) finalGrade = 'Acceptable';
  else if (lowestScore >= 4) finalGrade = 'Needs Improvement';
  else if (lowestScore >= 2) finalGrade = 'Poor';
  else finalGrade = 'Failed';

  const isFailed = finalGrade === 'Failed';

  const handleSave = () => {
    const newAudit: SessionAudit = {
      id: Math.random().toString(36).substr(2, 9),
      date: new Date().toISOString().split('T')[0],
      pnl,
      scores: { ...scores },
      finalGrade
    };
    setSavedAudits(prev => [newAudit, ...prev]);
  };

  return (
    <div className="main-content fade-in" style={{ gridTemplateColumns: '1fr 400px' }}>
      <div className="panel" style={{ maxHeight: '80vh', overflowY: 'auto' }}>
        <div className="panel-header">15-Dimension Scoring System</div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 24 }}>
          Each dimension represents a failure domain. The overall session grade is the LOWEST score, not the average.
        </p>

        {dimensions.map(dim => (
          <div key={dim} style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <label className="form-label" style={{ marginBottom: 0 }}>{dim}</label>
              <span className={`badge ${scores[dim] === 10 ? 'success' : scores[dim] >= 6 ? 'info' : scores[dim] >= 4 ? 'warning' : 'danger'}`}>
                {scores[dim]} / 10
              </span>
            </div>
            <input 
              type="range" 
              className="form-input" 
              min="0" max="10" step="2" 
              value={scores[dim]}
              onChange={e => handleScoreChange(dim, Number(e.target.value))}
            />
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div className="panel">
          <div className="panel-header">Session Conclusion</div>
          <div className="form-group">
            <label className="form-label">Session PnL ($)</label>
            <input 
              type="number" 
              className="form-input" 
              value={pnl}
              onChange={e => setPnl(Number(e.target.value))}
            />
          </div>

          <div style={{ marginTop: 24, marginBottom: 24 }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 4 }}>FINAL PROCESS GRADE</div>
            <div className={`output-value ${isFailed ? '' : 'fade-in'}`} style={{ color: isFailed ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
              {finalGrade}
            </div>
            <div className="output-subtitle">Lowest score overrides PnL</div>
          </div>

          {isFailed && pnl > 0 && (
             <div className="stops-alert fade-in" style={{ marginBottom: 24 }}>
               <div className="title">PROCESS FAILURE</div>
               <ul style={{ listStyle: 'none', marginLeft: 0 }}>
                 <li>The positive PnL was earned despite broken risk architecture. Fix the structural leak before scaling.</li>
               </ul>
             </div>
          )}

          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave}>
              Log Session Audit
            </button>
            <button className="btn" onClick={handleReset}>
              Reset
            </button>
          </div>
        </div>

        {savedAudits.length > 0 && (
          <div className="panel">
            <div className="panel-header">Past Audits</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {savedAudits.map(audit => (
                <div key={audit.id} style={{ padding: 12, backgroundColor: 'var(--bg-tertiary)', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                   <div>
                     <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{audit.date}</div>
                     <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>${audit.pnl.toLocaleString()}</div>
                   </div>
                   <span className={`badge ${audit.finalGrade === 'Failed' ? 'danger' : audit.finalGrade === 'Excellent' ? 'success' : 'info'}`}>
                     {audit.finalGrade}
                   </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
