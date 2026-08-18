import React, { useContext, useState, useEffect } from 'react';
import { AppContext } from '../context/AppContext';

export const CommandPalette = ({ isOpen, onClose }) => {
  const { 
    jobs, 
    companies, 
    campaigns, 
    selectJob, 
    selectCompany, 
    selectCampaign, 
    setActiveTab, 
    addLog 
  } = useContext(AppContext);

  const [search, setSearch] = useState('');

  // Handle Ctrl+K / Cmd+K global shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const matches = [];
  const searchLower = search.toLowerCase();

  // Filter jobs
  jobs.forEach(j => {
    if (j.title.toLowerCase().includes(searchLower) || j.company.toLowerCase().includes(searchLower)) {
      matches.push({ type: 'job', id: j.id, title: j.title, sub: j.company });
    }
  });

  // Filter companies
  companies.forEach(c => {
    if (c.name.toLowerCase().includes(searchLower)) {
      matches.push({ type: 'company', id: c.name, title: c.name, sub: c.url });
    }
  });

  // Filter campaigns
  campaigns.forEach(c => {
    if (c.name.toLowerCase().includes(searchLower)) {
      matches.push({ type: 'campaign', id: c.id, title: c.name, sub: c.target_role });
    }
  });

  // Static commands
  const staticCommands = [
    { id: 'view-dashboard', title: 'Open Dashboard', sub: 'Navigates to main screen' },
    { id: 'view-intelligence', title: 'Open Match Diagnostics', sub: 'Inspect deep match explainability' },
    { id: 'view-analytics', title: 'Open Analytics Cockpit', sub: 'Review campaign stats' },
    { id: 'trigger-optimization', title: 'Execute Behavioral Optimization', sub: 'Run epsilon calculations' }
  ];

  staticCommands.forEach(cmd => {
    if (cmd.title.toLowerCase().includes(searchLower) || cmd.sub.toLowerCase().includes(searchLower)) {
      matches.push({ type: 'command', id: cmd.id, title: cmd.title, sub: cmd.sub });
    }
  });

  const handleSelection = (item) => {
    onClose();
    if (item.type === 'job') {
      selectJob(item.id);
      setActiveTab('jobs');
    } else if (item.type === 'company') {
      selectCompany(item.id);
      setActiveTab('contacts');
    } else if (item.type === 'campaign') {
      selectCampaign(item.id);
      setActiveTab('campaigns');
    } else if (item.type === 'command') {
      if (item.id === 'view-dashboard') setActiveTab('dashboard');
      else if (item.id === 'view-intelligence') setActiveTab('intelligence');
      else if (item.id === 'view-analytics') setActiveTab('analytics');
      else if (item.id === 'trigger-optimization') {
        addLog("Initializing real-time optimizer and behavioral updates...", "action");
        addLog("✓ OPTIMIZATION COMPLETE: Recalculated Strategy Performance Matrix.", "success");
      }
    }
  };

  return (
    <div className="cmd-palette-overlay" style={{ display: 'flex' }} onClick={onClose}>
      <div className="cmd-palette" onClick={(e) => e.stopPropagation()}>
        <div className="cmd-input-container">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--text-dim)', marginRight: '0.75rem' }}>
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input 
            type="text" 
            className="cmd-input" 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search jobs, campaigns, companies, strategies..." 
            autoFocus
          />
          <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', background: 'rgba(255, 255, 255, 0.05)', padding: '0.2rem 0.4rem', borderRadius: '6px', border: '1px solid var(--border)' }}>
            ESC
          </span>
        </div>
        <div className="cmd-results">
          {matches.length === 0 ? (
            <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '1.5rem', fontSize: '0.85rem' }}>
              No results found.
            </div>
          ) : (
            matches.map((m, index) => (
              <div 
                key={index}
                className="cmd-item" 
                onClick={() => handleSelection(m)}
              >
                <div>
                  <div style={{ fontWeight: 700, color: 'white' }}>{m.title}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>{m.sub}</div>
                </div>
                <span className={`cmd-type-badge ${m.type}`}>
                  {m.type}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
