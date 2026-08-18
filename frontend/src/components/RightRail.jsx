import React, { useContext } from 'react';
import { AppContext } from '../context/AppContext';

export const RightRail = () => {
  const { 
    jobs, 
    selectedJobId, 
    explainData, 
    companyIntel, 
    activityFeed,
    setActiveTab
  } = useContext(AppContext);

  const selectedJob = jobs.find(j => j.id === selectedJobId);

  const getScoreTier = (score) => {
    const val = Math.round(score || 0);
    return val >= 80 ? 'excellent' : val >= 50 ? 'good' : 'poor';
  };

  const scoreVal = explainData ? Math.round(explainData.combined_score || explainData.match_score) : 0;

  return (
    <aside className="workspace-rail">
      {/* Active Context */}
      <div className="rail-section">
        <div className="rail-header">
          <span>Active Context</span>
          <span className="badge badge-purple" style={{ fontSize: '0.6rem' }}>FOCUSED</span>
        </div>
        {selectedJob ? (
          <div className="card" style={{ padding: '1rem', borderColor: 'rgba(99, 102, 241, 0.4)' }}>
            <div style={{ fontWeight: 800, color: 'white', fontSize: '0.9rem' }}>{selectedJob.title}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--primary-light)', marginTop: '0.15rem' }}>{selectedJob.company}</div>
            <div className="divider" style={{ margin: '0.5rem 0' }}></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
              <span>Source: {selectedJob.platform || 'Direct Scrape'}</span>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.15rem 0.4rem', fontSize: '0.65rem' }} 
                onClick={() => setActiveTab('intelligence')}
              >
                Inspect
              </button>
            </div>
          </div>
        ) : (
          <div className="card" style={{ padding: '1rem', borderColor: 'rgba(255, 255, 255, 0.05)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              No Active Context. Select a job opportunity to mount session.
            </div>
          </div>
        )}
      </div>

      {/* Match Explainer */}
      {explainData && (
        <div className="rail-section">
          <div className="rail-header">
            <span>Match Explainer</span>
            <span 
              style={{ fontSize: '0.75rem', fontWeight: 700 }}
              className={`status-badge ${scoreVal >= 80 ? 'replied' : scoreVal >= 50 ? 'opened' : 'failed'}`}
            >
              {scoreVal >= 80 ? 'Excellent Match' : scoreVal >= 50 ? 'Moderate Match' : 'Weak Match'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div 
              className={`score-ring ${getScoreTier(scoreVal)}`} 
              style={{ width: '60px', height: '60px', fontSize: '1.1rem', borderWidth: '5px' }}
            >
              {scoreVal}%
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'white' }}>Semantic Similarity</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>
                {explainData.explanation_summary ? explainData.explanation_summary.slice(0, 50) + '...' : 'High project overlap.'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Source Attributions */}
      {companyIntel && (
        <div className="rail-section">
          <div className="rail-header">
            <span>Evidence Sources</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span className="status-dot active"></span>
              <span>Company Tech Stack ({(companyIntel.tech_stack || []).length} keywords detected)</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', paddingLeft: '0.75rem' }}>
              Source: Crawled Careers / Team Page
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text)', display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
              <span className="status-dot active"></span>
              <span>Corporate Vision Analysis</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', paddingLeft: '0.75rem' }}>
              Source: About Page semantic model
            </div>
          </div>
        </div>
      )}

      {/* Activity Feed */}
      <div className="rail-section" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '250px' }}>
        <div className="rail-header">
          <span>Activity Feed</span>
        </div>
        <div className="activity-feed" style={{ flex: 1, overflowY: 'auto' }}>
          {activityFeed.length === 0 ? (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textAlign: 'center', padding: '2rem 0' }}>
              No activities logged.
            </div>
          ) : (
            [...activityFeed].reverse().map((log, index) => {
              let iconClass = 'info';
              let iconText = 'ℹ';
              if (log.type === 'action') { iconClass = 'action'; iconText = '⚙'; }
              else if (log.type === 'success') { iconClass = 'success'; iconText = '✓'; }
              else if (log.type === 'error') { iconClass = 'error'; iconText = '⚠'; }

              return (
                <div key={index} className="feed-item" style={{ marginBottom: '0.5rem' }}>
                  <div className={`feed-icon ${iconClass}`}>{iconText}</div>
                  <div>
                    <div style={{ fontWeight: 700, color: 'white' }}>{log.message}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>{log.time}</div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </aside>
  );
};
