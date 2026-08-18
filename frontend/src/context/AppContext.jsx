import React, { createContext, useState, useEffect } from 'react';

export const AppContext = createContext();

const getLocalStorageItem = (key, defaultValue) => {
  const value = localStorage.getItem(key);
  if (!value) return defaultValue;
  try {
    return JSON.parse(value);
  } catch (e) {
    return value;
  }
};

export const AppProvider = ({ children }) => {
  // Base API configuration
  const BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? 'http://127.0.0.1:8000'
    : window.location.origin;

  // Global app states
  const [user, setUser] = useState(() => getLocalStorageItem('current_user', null));
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('access_token'));
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('refresh_token'));
  
  const [jobs, setJobs] = useState(() => getLocalStorageItem('app_jobs', []));
  const [campaigns, setCampaigns] = useState(() => getLocalStorageItem('app_campaigns', []));
  const [companies, setCompanies] = useState(() => getLocalStorageItem('app_companies', [
    { name: 'Infosys', url: 'https://infosys.com', data: { tech_stack: ['Java', 'Cloud Infra', 'FastAPI'], vision: 'Service excellence and modernization' } },
    { name: 'TCS', url: 'https://tcs.com', data: { tech_stack: ['AWS', 'SAP', 'Python'], vision: 'Global digital integration leadership' } }
  ]));
  const [history, setHistory] = useState(() => getLocalStorageItem('outreach_history', []));
  const [activityFeed, setActivityFeed] = useState(() => getLocalStorageItem('app_activity_feed', []));

  const [selectedJobId, setSelectedJobId] = useState(() => {
    const val = localStorage.getItem('selected_job_id');
    return val ? parseInt(val) : null;
  });
  const [selectedCompanyName, setSelectedCompanyName] = useState(() => localStorage.getItem('selected_company_name'));
  
  const [companyIntel, setCompanyIntel] = useState(() => getLocalStorageItem('company_intel', null));
  const [matchData, setMatchData] = useState(() => getLocalStorageItem('match_data', null));
  const [explainData, setExplainData] = useState(() => getLocalStorageItem('explain_data', null));
  const [strategyData, setStrategyData] = useState(() => getLocalStorageItem('strategy_data', null));

  const [activeTab, setActiveTab] = useState(() => localStorage.getItem('active_tab') || 'dashboard');
  const [focusedCampaignId, setFocusedCampaignId] = useState(() => {
    const val = localStorage.getItem('focused_campaign_id');
    return val ? parseInt(val) : null;
  });

  // State synchronization to localStorage
  useEffect(() => {
    if (user) localStorage.setItem('current_user', JSON.stringify(user));
    else localStorage.removeItem('current_user');
  }, [user]);

  useEffect(() => {
    if (accessToken) localStorage.setItem('access_token', accessToken);
    else localStorage.removeItem('access_token');
  }, [accessToken]);

  useEffect(() => {
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
    else localStorage.removeItem('refresh_token');
  }, [refreshToken]);

  useEffect(() => {
    localStorage.setItem('app_jobs', JSON.stringify(jobs));
  }, [jobs]);

  useEffect(() => {
    localStorage.setItem('app_campaigns', JSON.stringify(campaigns));
  }, [campaigns]);

  useEffect(() => {
    localStorage.setItem('app_companies', JSON.stringify(companies));
  }, [companies]);

  useEffect(() => {
    localStorage.setItem('outreach_history', JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    localStorage.setItem('app_activity_feed', JSON.stringify(activityFeed));
  }, [activityFeed]);

  useEffect(() => {
    if (selectedJobId) localStorage.setItem('selected_job_id', selectedJobId);
    else localStorage.removeItem('selected_job_id');
  }, [selectedJobId]);

  useEffect(() => {
    if (selectedCompanyName) localStorage.setItem('selected_company_name', selectedCompanyName);
    else localStorage.removeItem('selected_company_name');
  }, [selectedCompanyName]);

  useEffect(() => {
    if (companyIntel) localStorage.setItem('company_intel', JSON.stringify(companyIntel));
    else localStorage.removeItem('company_intel');
  }, [companyIntel]);

  useEffect(() => {
    if (matchData) localStorage.setItem('match_data', JSON.stringify(matchData));
    else localStorage.removeItem('match_data');
  }, [matchData]);

  useEffect(() => {
    if (explainData) localStorage.setItem('explain_data', JSON.stringify(explainData));
    else localStorage.removeItem('explain_data');
  }, [explainData]);

  useEffect(() => {
    if (strategyData) localStorage.setItem('strategy_data', JSON.stringify(strategyData));
    else localStorage.removeItem('strategy_data');
  }, [strategyData]);

  useEffect(() => {
    localStorage.setItem('active_tab', activeTab);
  }, [activeTab]);

  useEffect(() => {
    if (focusedCampaignId) localStorage.setItem('focused_campaign_id', focusedCampaignId);
    else localStorage.removeItem('focused_campaign_id');
  }, [focusedCampaignId]);

  // Logging system
  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setActivityFeed((prev) => {
      const updated = [...prev, { time, message, type }];
      if (updated.length > 40) updated.shift();
      return updated;
    });
  };

  // Activity feed initializer
  useEffect(() => {
    if (activityFeed.length === 0) {
      addLog("Outreach OS initialized. Ready for job discovery.", "info");
    }
  }, []);

  // Token refresh logic
  const attemptTokenRefresh = async () => {
    const rt = localStorage.getItem('refresh_token');
    if (!rt) return false;
    try {
      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt })
      });
      if (res.ok) {
        const data = await res.json();
        setAccessToken(data.access_token);
        setRefreshToken(data.refresh_token);
        setUser(data.user);
        return true;
      }
    } catch (err) {
      console.error("Token refresh failure", err);
    }
    return false;
  };

  // Auth fetch wrapper
  const authFetch = async (url, options = {}) => {
    const token = localStorage.getItem('access_token') || accessToken;
    const headers = Object.assign({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }, options.headers || {});
    
    const opt = Object.assign({}, options, { headers });
    let res = await fetch(url, opt);
    
    if (res.status === 401) {
      const refreshed = await attemptTokenRefresh();
      if (refreshed) {
        opt.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
        res = await fetch(url, opt);
      } else {
        logout();
        throw new Error("Session expired. Please log in again.");
      }
    }
    return res;
  };

  // Handle Logout
  const logout = () => {
    localStorage.clear();
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setJobs([]);
    setCampaigns([]);
    setSelectedJobId(null);
    setSelectedCompanyName(null);
    setCompanyIntel(null);
    setMatchData(null);
    setExplainData(null);
    setStrategyData(null);
    setHistory([]);
    setActivityFeed([]);
    setFocusedCampaignId(null);
    setActiveTab('dashboard');
    addLog("Session terminated. User logged out.", "info");
  };

  // Select focus campaign
  const selectCampaign = (campaignId) => {
    setFocusedCampaignId(campaignId);
    if (campaignId) {
      const camp = campaigns.find(c => c.id === campaignId);
      addLog(`Workspace focus set to Campaign: ${camp ? camp.name : campaignId}`, "action");
    } else {
      addLog("Workspace focus cleared.", "info");
    }
  };

  // Select job context
  const selectJob = (jobId) => {
    setSelectedJobId(jobId);
    const job = jobs.find(j => j.id === jobId);
    if (job) {
      setSelectedCompanyName(job.company);
      addLog(`Context Opportunity loaded: ${job.title} at ${job.company}`, "action");
      
      // Auto enrichment
      const cleanDomain = job.company.toLowerCase().replace(/[^a-z0-9]/g, '') + '.com';
      triggerCompanyEnrichment(job.company, `https://${cleanDomain}`);
    }
  };

  // Select company context
  const selectCompany = (companyName) => {
    setSelectedCompanyName(companyName);
    addLog(`Context Company selected: ${companyName}`, "action");
    
    const comp = companies.find(c => c.name === companyName);
    if (comp && comp.data) {
      setCompanyIntel(comp.data);
    }
  };

  // Company enrichment call
  const triggerCompanyEnrichment = async (companyName, url) => {
    addLog(`Gathering company intelligence memory for: ${companyName}...`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/company/enrich?name=${encodeURIComponent(companyName)}&url=${encodeURIComponent(url)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Enrichment failed');
      
      setCompanyIntel(data);
      addLog(`✓ INTEL RETRIEVED: Found tech stack details for ${companyName}`, "success");
      
      setCompanies((prev) => {
        const idx = prev.findIndex(c => c.name === companyName);
        const updated = [...prev];
        if (idx === -1) {
          updated.push({ name: companyName, url, data });
        } else {
          updated[idx] = { name: companyName, url, data };
        }
        return updated;
      });
    } catch (err) {
      addLog(`Intel gather failed: ${err.message}`, "error");
    }
  };

  return (
    <AppContext.Provider value={{
      BASE_URL,
      user, setUser,
      accessToken, setAccessToken,
      refreshToken, setRefreshToken,
      jobs, setJobs,
      campaigns, setCampaigns,
      companies, setCompanies,
      history, setHistory,
      activityFeed, setActivityFeed,
      selectedJobId, setSelectedJobId,
      selectedCompanyName, setSelectedCompanyName,
      companyIntel, setCompanyIntel,
      matchData, setMatchData,
      explainData, setExplainData,
      strategyData, setStrategyData,
      activeTab, setActiveTab,
      focusedCampaignId, setFocusedCampaignId,
      addLog,
      authFetch,
      logout,
      selectCampaign,
      selectJob,
      selectCompany,
      triggerCompanyEnrichment
    }}>
      {children}
    </AppContext.Provider>
  );
};
