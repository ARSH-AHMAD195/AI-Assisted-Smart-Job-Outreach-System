import React, { useContext, useState, useEffect } from 'react';
import { AppProvider, AppContext } from './context/AppContext';
import { Auth } from './components/Auth';
import { LandingPage } from './components/LandingPage';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { RightRail } from './components/RightRail';
import { CommandPalette } from './components/CommandPalette';

// Tab imports
import { DashboardTab } from './components/DashboardTab';
import { JobsTab } from './components/JobsTab';
import { CampaignsTab } from './components/CampaignsTab';
import { ContactsTab } from './components/ContactsTab';
import { IntelligenceTab } from './components/IntelligenceTab';
import { AnalyticsTab } from './components/AnalyticsTab';

function MainWorkspace() {
  const { accessToken, activeTab } = useContext(AppContext);
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Keyboard shortcut listener for Cmd/Ctrl + K to toggle command palette
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, []);

  if (!accessToken) {
    return (
      <>
        <LandingPage onSignIn={() => setShowAuthModal(true)} />
        {showAuthModal && (
          <Auth onClose={() => setShowAuthModal(false)} />
        )}
      </>
    );
  }

  const renderActiveTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardTab onOpenCmdPalette={() => setCmdPaletteOpen(true)} />;
      case 'jobs':
        return <JobsTab />;
      case 'campaigns':
        return <CampaignsTab />;
      case 'contacts':
        return <ContactsTab />;
      case 'intelligence':
        return <IntelligenceTab />;
      case 'analytics':
        return <AnalyticsTab />;
      default:
        return <DashboardTab onOpenCmdPalette={() => setCmdPaletteOpen(true)} />;
    }
  };

  return (
    <div className="app-workspace">
      <Sidebar />
      <main className="workspace-body">
        <Header />
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.25rem' }}>
          {renderActiveTabContent()}
        </div>
      </main>
      <RightRail />
      <CommandPalette isOpen={cmdPaletteOpen} onClose={() => setCmdPaletteOpen(false)} />
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <MainWorkspace />
    </AppProvider>
  );
}

export default App;
