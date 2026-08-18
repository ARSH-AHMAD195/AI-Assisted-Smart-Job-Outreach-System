import React, { useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { 
  LayoutGrid, 
  Briefcase, 
  Flag, 
  Users, 
  Brain, 
  BarChart3, 
  LogOut 
} from 'lucide-react';

export const Sidebar = ({ onOpenCmdPalette }) => {
  const { 
    user, 
    activeTab, 
    setActiveTab, 
    logout 
  } = useContext(AppContext);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
    { id: 'jobs', label: 'Jobs & Profile', icon: Briefcase },
    { id: 'campaigns', label: 'Campaigns', icon: Flag },
    { id: 'contacts', label: 'Contacts & Memory', icon: Users },
    { id: 'intelligence', label: 'Intelligence Engine', icon: Brain },
    { id: 'analytics', label: 'Analytics Cockpit', icon: BarChart3 }
  ];

  return (
    <aside className="workspace-sidebar">
      <div className="sidebar-brand">
        <a 
          href="#" 
          className="sidebar-logo" 
          onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          <span>Outreach OS</span>
        </a>
        <button className="cmd-palette-btn" onClick={onOpenCmdPalette}>
          <span>⌘K</span>
        </button>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button 
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={16} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicators">
          <div className="status-indicator">
            <span className="status-dot active"></span>
            <span>Outreach Queue Scheduler (5m)</span>
          </div>
          <div className="status-indicator">
            <span className="status-dot active"></span>
            <span>Epsilon Exploration Engine</span>
          </div>
        </div>
        {user && (
          <div className="user-widget-compact">
            <div className="user-avatar-compact">
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div style={{ flex: 1, overflow: 'hidden', textAlign: 'left' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'white', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.full_name || 'User Name'}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.email || 'user@domain.com'}
              </div>
            </div>
            <button onClick={logout} style={{ background: 'transparent', border: 'none', color: 'var(--accent-red)', cursor: 'pointer' }}>
              <LogOut size={14} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
