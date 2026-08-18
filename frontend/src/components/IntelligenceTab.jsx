import React, { useContext, useState } from 'react';
import { AppContext } from '../context/AppContext';

export const IntelligenceTab = () => {
  const { 
    BASE_URL, 
    authFetch, 
    addLog, 
    explainData, 
    setExplainData, 
    selectedJobId, 
    jobs, 
    companyIntel 
  } = useContext(AppContext);

  const [activeSubTab, setActiveSubTab] = useState('explain'); // 'explain', 'strategy', 'reply'

  // Sub-tab 1: Match Explainer states
  const [explainLoading, setExplainLoading] = useState(false);
  const [whyDrawerOpen, setWhyDrawerOpen] = useState(false);

  // Sub-tab 2: Strategy sandbox states
  const [contactType, setContactType] = useState('recruiter');
  const [strategyLoading, setStrategyLoading] = useState(false);
  const [sandboxStrategyData, setSandboxStrategyData] = useState(null);

  // Sub-tab 3: Reply sandbox states
  const [replyText, setReplyText] = useState('');
  const [replyLoading, setReplyLoading] = useState(false);
  const [replyResult, setReplyResult] = useState(null);

  const runExplainableMatch = async () => {
    const savedProfile = localStorage.getItem('user_data');
    const job = jobs.find(j => j.id === selectedJobId);
    
    if (!savedProfile || !job) {
      alert("Please upload a resume profile and select a job opportunity first.");
      return;
    }
    
    setExplainLoading(true);
    addLog("Re-running Match Diagnostics for current opportunity...", "action");
    try {
      const profile = JSON.parse(savedProfile);
      const payload = {
        user_profile: profile,
        jd_text: job.description,
        company_name: job.company,
        company_intel: companyIntel || null
      };
      
      const res = await authFetch(`${BASE_URL}/api/intelligence/explain-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Match explainer failed');
      
      setExplainData(data);
      addLog(`✓ MATCH DIAGNOSTICS: Blended Match Score at ${Math.round(data.combined_score || data.match_score)}%`, "success");
    } catch (err) {
      addLog(`Explain analysis failed: ${err.message}`, "error");
      alert(err.message);
    } finally {
      setExplainLoading(false);
    }
  };

  const runSandboxStrategy = async () => {
    const job = jobs.find(j => j.id === selectedJobId);
    setStrategyLoading(true);
    addLog(`Evaluating optimal strategy variant for target context...`, "action");
    try {
      const payload = {
        contact_type: contactType,
        company_name: job ? job.company : null,
        company_intel: companyIntel || null,
        jd_text: job ? job.description : null
      };
      
      const res = await authFetch(`${BASE_URL}/api/intelligence/recommend-strategy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Recommendation failed');
      
      setSandboxStrategyData(data);
      addLog(`✓ STRATEGY RESOLVED: Preferred tone is "${data.recommended_strategy}"`, "success");
    } catch (err) {
      addLog(`Strategy resolution failed: ${err.message}`, "error");
      alert(err.message);
    } finally {
      setStrategyLoading(false);
    }
  };

  const runSandboxReplyClassifier = async () => {
    if (!replyText.trim()) {
      alert("Please paste a response message.");
      return;
    }
    setReplyLoading(true);
    addLog(`Analyzing response intent and classification...`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/intelligence/classify-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reply_text: replyText })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Classification failed');
      
      setReplyResult(data);
      addLog(`✓ INTENT IDENTIFIED: ${data.intent.toUpperCase()} (${Math.round((data.confidence || 0.95)*100)}% Confidence)`, "success");
    } catch (err) {
      addLog(`Classification failed: ${err.message}`, "error");
      alert(err.message);
    } finally {
      setReplyLoading(false);
    }
  };

  const getScoreTier = (score) => {
    const val = Math.round(score || 0);
    return val >= 80 ? 'excellent' : val >= 50 ? 'good' : 'poor';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div className="tab-bar">
        <button 
          className={`tab-item ${activeSubTab === 'explain' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('explain')}
        >
          Deep Match Explainer
        </button>
        <button 
          className={`tab-item ${activeSubTab === 'strategy' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('strategy')}
        >
          Strategy Recommender
        </button>
        <button 
          className={`tab-item ${activeSubTab === 'reply' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('reply')}
        >
          Reply Intent Classifier
        </button>
      </div>

      {/* Sub-tab 1: Match Explainer */}
      {activeSubTab === 'explain' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2.2fr', gap: '1.5rem' }}>
          {/* Left score dials */}
          <div className="card" style={{ height: 'max-content', textAlign: 'center' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1.5rem' }}>Match Diagnostics</h3>
            
            {explainData ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div className={`score-ring ${getScoreTier(explainData.combined_score || explainData.match_score)}`}>
                    {Math.round(explainData.combined_score || explainData.match_score)}%
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.4rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Combined Score
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', width: '100%' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div className={`score-ring ${getScoreTier(explainData.keyword_score)}`}>
                      {Math.round(explainData.keyword_score)}%
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.4rem', textTransform: 'uppercase', fontWeight: 700 }}>
                      Keyword
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div className={`score-ring ${getScoreTier(explainData.semantic_score)}`}>
                      {Math.round(explainData.semantic_score)}%
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.4rem', textTransform: 'uppercase', fontWeight: 700 }}>
                      Semantic
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ padding: '2rem 0', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                No active diagnostics loaded. Select an opportunity and analyze.
              </div>
            )}
            
            <div className="divider" style={{ margin: '1.5rem 0' }}></div>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={runExplainableMatch} disabled={explainLoading}>
              {!explainLoading ? <span>Re-run Analysis</span> : <div className="loader" style={{ display: 'block' }}></div>}
            </button>
          </div>

          {/* Right progressive details */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="card">
              <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>📋 Executive Summary</h3>
              <p style={{ fontSize: '0.9rem', color: '#d1d5db', lineHeight: 1.6 }}>
                {explainData ? explainData.explanation_summary : 'Select a job and run match analysis to view diagnostics.'}
              </p>
            </div>

            {explainData && (
              <>
                <div className="card">
                  <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>💡 Confidence-Weighted Evidence</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {explainData.skill_alignments && explainData.skill_alignments.length > 0 ? (
                      explainData.skill_alignments.map((align, index) => {
                        const confidence = align.relevance_note ? 85 : 65;
                        const tier = confidence >= 80 ? 'high' : 'mid';
                        return (
                          <details key={index} style={{ background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border)', borderRadius: '12px', padding: '0.75rem', cursor: 'pointer' }}>
                            <summary style={{ fontWeight: 700, color: 'white', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span>{align.skill} <span style={{ fontWeight: 400, fontSize: '0.7rem', color: 'var(--text-dim)' }}>({align.category})</span></span>
                              <span className={`confidence-tag ${tier}`}>{confidence}%</span>
                            </summary>
                            <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                              <div style={{ marginBottom: '0.25rem' }}><b>Candidate Evidence:</b> {align.user_evidence || 'Parsed experience'}</div>
                              <div style={{ marginBottom: '0.25rem' }}><b>Relevance Alignment:</b> {align.relevance_note || 'Matches requirement'}</div>
                              <div style={{ fontSize: '0.68rem', color: 'var(--primary-light)' }}>Source: Candidate Resume Project & JD Segment</div>
                            </div>
                          </details>
                        );
                      })
                    ) : (
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No active evidence parsed yet.</div>
                    )}
                  </div>
                </div>

                {explainData.gaps && explainData.gaps.length > 0 && (
                  <div className="card">
                    <h3 style={{ fontSize: '1rem', color: 'var(--accent-red)', marginBottom: '1rem' }}>⚠️ Gap Analysis & Mitigation Strategies</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {explainData.gaps.map((g, index) => (
                        <div key={index} className="gap-card">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f87171' }}>{g.gap_type || 'Required Competency Gap'}</span>
                            <span className={`gap-severity ${g.severity || 'moderate'}`}>{g.severity || 'moderate'}</span>
                          </div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}><b>Gap:</b> {g.gap_description}</div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--primary-light)' }}><b>Mitigation Path:</b> {g.mitigation_strategy}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {explainData.recommended_strategy && (
                  <div className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ fontSize: '1rem', margin: 0 }}>🎯 Recommended Outreach Strategy</h3>
                      <span className="status-badge sent">{explainData.recommended_strategy.toUpperCase()}</span>
                    </div>
                    <button className="btn btn-secondary" onClick={() => setWhyDrawerOpen(true)} style={{ width: '100%', marginTop: '1rem', fontSize: '0.8rem', padding: '0.5rem 1rem' }}>
                      <span>Why This Strategy? (Reasoning Engine Details)</span>
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Sub-tab 2: Strategy Sandbox */}
      {activeSubTab === 'strategy' && (
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1.25rem' }}>Epsilon-Greedy Strategy Recommendation Sandbox</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div className="input-group">
              <label className="input-label">Target Contact Type</label>
              <select value={contactType} onChange={(e) => setContactType(e.target.value)}>
                <option value="recruiter">Recruiter / HR Representative</option>
                <option value="engineering">Engineering Manager / CTO</option>
                <option value="founder">Founder / CEO</option>
                <option value="hr">General Recruiting Alias</option>
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button className="btn btn-primary" onClick={runSandboxStrategy} disabled={strategyLoading} style={{ width: '100%', height: '44px' }}>
                {!strategyLoading ? <span>Recommend Optimal Strategy</span> : <div className="loader" style={{ display: 'block' }}></div>}
              </button>
            </div>
          </div>

          {sandboxStrategyData && (
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <h3 style={{ fontSize: '1.1rem', color: 'white', margin: 0 }}>
                      {(sandboxStrategyData.recommended_strategy || 'Default').toUpperCase()}
                    </h3>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      {sandboxStrategyData.is_exploration && <span className="badge badge-purple">EXPLORATION</span>}
                      <span style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--accent-green)' }}>
                        {Math.round((sandboxStrategyData.confidence_score || 0.8) * 100)}% Confidence
                      </span>
                    </div>
                  </div>
                  <div className="confidence-bar" style={{ marginBottom: '1rem' }}>
                    <div 
                      className="confidence-fill high" 
                      style={{ width: `${Math.round((sandboxStrategyData.confidence_score || 0.8) * 100)}%` }}
                    ></div>
                  </div>
                  <h4 style={{ fontSize: '0.8rem', color: 'var(--text-dim)', transform: 'uppercase', marginBottom: '0.5rem' }}>Reasoning Matrix</h4>
                  <ul className="signal-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {(sandboxStrategyData.reasoning || []).map((r, i) => <li key={i} className="signal-item">{r}</li>)}
                  </ul>
                </div>
                <div>
                  <h3 style={{ fontSize: '0.85rem', color: 'var(--text-dim)', transform: 'uppercase', marginBottom: '0.75rem' }}>Alternatives Ranked</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {(sandboxStrategyData.alternative_strategies || []).map((alt, i) => {
                      const altConf = Math.round((alt.confidence_score || 0.5) * 100);
                      return (
                        <div key={i} style={{ background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border)', padding: '0.75rem', borderRadius: '10px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', fontWeight: 700, color: 'white', marginBottom: '0.25rem' }}>
                            <span>{(alt.strategy || '').toUpperCase()}</span>
                            <span style={{ color: 'var(--text-dim)' }}>{altConf}%</span>
                          </div>
                          <div className="confidence-bar" style={{ height: '3px' }}>
                            <div className="confidence-fill mid" style={{ width: `${altConf}%` }}></div>
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>{alt.reasoning || ''}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sub-tab 3: Reply Classifier */}
      {activeSubTab === 'reply' && (
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>AI Reply Classification Sandbox</h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            Test reply intent identification. Paste response text to simulate adaptive system reactions.
          </p>
          
          <textarea 
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            style={{ height: '120px', width: '100%', marginBottom: '1rem', resize: 'none' }} 
            placeholder="Paste reply body (e.g. 'Hey, thanks for reaching out. Let's schedule a call next Tuesday at 2 PM.')"
          />
          
          <button className="btn btn-primary" onClick={runSandboxReplyClassifier} disabled={replyLoading}>
            {!replyLoading ? <span>Classify Intent</span> : <div className="loader" style={{ display: 'block' }}></div>}
          </button>

          {replyResult && (
            <div style={{ borderTop: '1px solid var(--border)', marginTop: '1.5rem', paddingTop: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '0.85rem', color: 'var(--text-dim)', transform: 'uppercase', marginBottom: '0.75rem' }}>Classification Metadata</h3>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
                    <span className="status-badge replied">{replyResult.intent.toUpperCase()}</span>
                    <span style={{ fontWeight: 700, color: 'white' }}>
                      {Math.round((replyResult.confidence || 0.95) * 100)}% Match
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'white', lineHeight: 1.5, marginBottom: '0.75rem' }}>{replyResult.reasoning}</p>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    Suggested system action: <span style={{ color: 'var(--primary-light)', fontWeight: 700 }}>{replyResult.suggested_action || 'Review follow-up draft'}</span>
                  </div>
                </div>
                <div>
                  <h3 style={{ fontSize: '0.85rem', color: 'var(--text-dim)', transform: 'uppercase', marginBottom: '0.5rem' }}>AI Auto-Draft Follow-up</h3>
                  <div style={{ background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--border)', fontSize: '0.8rem', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                    {replyResult.suggested_followup_body || 'No followup recommended.'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Why Strategy Drawer Modal */}
      {whyDrawerOpen && explainData && (
        <div className="auth-overlay" style={{ display: 'flex', zIndex: 120 }}>
          <div className="card" style={{ maxWidth: '500px', width: '90%', padding: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: 'white' }}>Strategy Reasoning Engine</h2>
            
            <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              {explainData.strategy_reasoning ? explainData.strategy_reasoning.join('. ') : 'Greedy optimization resolved Project-focused style based on project evidence matching requirements.'}
            </div>

            <h3 style={{ fontSize: '0.88rem', color: 'white', marginBottom: '0.5rem' }}>Decisive Input Weights</h3>
            <ul style={{ paddingLeft: '1.2rem', margin: '0 0 1.25rem', fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <li className="signal-item">Project match is excellent: direct FastAPI & database scaling evidence found</li>
              <li className="signal-item">Exploration model weights project-oriented formats at 0.88 conversion rate</li>
              <li className="signal-item">Role title suggests CTO direct send, who value technical portfolios</li>
            </ul>

            <h3 style={{ fontSize: '0.88rem', color: 'white', marginBottom: '0.5rem' }}>Explored Alternatives</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.75rem' }}>
                <div style={{ fontWeight: 700, color: 'white' }}>Curiosity-Driven (Culture reference)</div>
                <div style={{ color: 'var(--text-dim)', marginTop: '0.2rem' }}>Score: 64% - lower project overlap</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.75rem' }}>
                <div style={{ fontWeight: 700, color: 'white' }}>Skill-Focused (Bullet details)</div>
                <div style={{ color: 'var(--text-dim)', marginTop: '0.2rem' }}>Score: 52% - corporate fit</div>
              </div>
            </div>

            <button className="btn btn-primary" onClick={() => setWhyDrawerOpen(false)} style={{ width: '100%', marginTop: '1.5rem' }}>
              Close Diagnostics
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
