import React, { useContext } from 'react';
import { AppContext } from '../context/AppContext';

export const Header = () => {
  const { 
    activeTab, 
    focusedCampaignId, 
    campaigns, 
    selectCampaign 
  } = useContext(AppContext);

  // Map tabs to titles and subtitles
  const titleMap = {
    dashboard: {
      title: 'Dashboard',
      subtitle: 'Overview of intelligent pipeline telemetry'
    },
    jobs: {
      title: 'Jobs & Profile',
      subtitle: 'Analyze resumes and discover new matches'
    },
    campaigns: {
      title: 'Campaigns',
      subtitle: 'Orchestrate outreach campaigns and queues'
    },
    contacts: {
      title: 'Contacts & Memory',
      subtitle: 'Historical relationships, company signals and contacts'
    },
    intelligence: {
      title: 'Intelligence Engine',
      subtitle: 'Deep match explanations and strategic outreach generation'
    },
    analytics: {
      title: 'Analytics Cockpit',
      subtitle: 'Performance indicators and strategic conversion metrics'
    }
  };

  const { title, subtitle } = titleMap[activeTab] || { title: 'Workspace', subtitle: 'Outreach OS Management' };

  const focusedCampaign = campaigns.find(c => c.id === focusedCampaignId);

  return (
    <div className="workspace-header">
      <div>
        <h1 className="workspace-title">{title}</h1>
        <p className="workspace-subtitle">{subtitle}</p>
      </div>
      {focusedCampaignId && (
        <div id="focusBadgeContainer">
          <div className="focus-badge">
            <span>Focused Campaign: <b>{focusedCampaign ? focusedCampaign.name : focusedCampaignId}</b></span>
            <span className="focus-close" onClick={() => selectCampaign(null)}>&times;</span>
          </div>
        </div>
      )}
    </div>
  );
};
