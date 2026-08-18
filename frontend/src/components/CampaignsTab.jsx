import React, { useContext, useState, useEffect } from 'react';
import { AppContext } from '../context/AppContext';

export const CampaignsTab = () => {
  const { 
    BASE_URL, 
    authFetch, 
    addLog, 
    campaigns, 
    setCampaigns,
    jobs,
    focusedCampaignId,
    selectCampaign
  } = useContext(AppContext);

  // Form states
  const [campName, setCampName] = useState('');
  const [campRole, setCampRole] = useState('');
  const [maxPerHour, setMaxPerHour] = useState(10);
  const [maxContacts, setMaxContacts] = useState(3);
  const [stagger, setStagger] = useState(15);

  // Modal / Queue states
  const [populateModalOpen, setPopulateModalOpen] = useState(false);
  const [popCampaignId, setPopCampaignId] = useState(null);
  const [popJobsChecked, setPopJobsChecked] = useState([]);
  const [popProfileContext, setPopProfileContext] = useState('');
  const [popSubmitLoading, setPopSubmitLoading] = useState(false);

  // Queue explorer filter
  const [queueCampaignFilter, setQueueCampaignFilter] = useState('');
  const [queueItems, setQueueItems] = useState([]);
  const [queueLoading, setQueueLoading] = useState(false);

  // Suppression Fallback Modal state
  const [suppressionModalOpen, setSuppressionModalOpen] = useState(false);
  const [fallbackDetail, setFallbackDetail] = useState(null);

  const fetchCampaigns = async () => {
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/`);
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchQueue = async () => {
    let activeId = queueCampaignFilter;
    if (!activeId) {
      activeId = focusedCampaignId;
    }
    if (!activeId && campaigns.length > 0) {
      activeId = campaigns[0].id;
    }
    if (!activeId) {
      setQueueItems([]);
      return;
    }
    setQueueLoading(true);
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/${activeId}/queue`);
      if (res.ok) {
        const data = await res.json();
        setQueueItems(data);
      }
    } catch (e) {
      console.error("Queue fetch failure", e);
    } finally {
      setQueueLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [queueCampaignFilter, focusedCampaignId, campaigns]);

  const handleCreateCampaignSubmit = async (e) => {
    e.preventDefault();
    addLog(`Creating Campaign: "${campName}"`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/`, {
        method: 'POST',
        body: JSON.stringify({
          name: campName,
          target_role: campRole,
          max_emails_per_hour: maxPerHour,
          max_contacts_per_company: maxContacts,
          stagger_interval_minutes: stagger
        })
      });
      if (res.ok) {
        addLog(`✓ CAMPAIGN CREATED: "${campName}" initialized.`, "success");
        setCampName('');
        setCampRole('');
        fetchCampaigns();
      } else {
        const data = await res.json();
        throw new Error(data.detail || 'Creation failed');
      }
    } catch (err) {
      alert("Failed creating campaign: " + err.message);
    }
  };

  const toggleCampaignState = async (id, status) => {
    const endpoint = status === 'active' ? 'pause' : 'start';
    addLog(`Toggling status of Campaign ${id} to ${status === 'active' ? 'paused' : 'active'}`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/${id}/${endpoint}`, { method: 'POST' });
      if (res.ok) {
        addLog(`✓ CAMPAIGN STATE MUTATED: Status updated.`, "success");
        fetchCampaigns();
      } else {
        throw new Error("Failed toggling status.");
      }
    } catch (err) {
      alert("State toggle failed: " + err.message);
    }
  };

  const triggerDeleteCampaign = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete campaign "${name}"? This will delete all of its queue items as well.`)) {
      return;
    }
    addLog(`Deleting campaign ${id} ("${name}")...`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/${id}`, { method: 'DELETE' });
      if (res.ok) {
        addLog(`✓ CAMPAIGN DELETED: Campaign "${name}" has been deleted.`, "success");
        if (focusedCampaignId === id) {
          selectCampaign(null);
        }
        fetchCampaigns();
      } else {
        const data = await res.json();
        throw new Error(data.detail || 'Delete failed');
      }
    } catch (err) {
      addLog(`✗ DELETE FAILURE: ${err.message}`, "error");
      alert("Delete failed: " + err.message);
    }
  };

  const openPopulateQueueModal = (campaignId) => {
    setPopCampaignId(campaignId);
    setPopulateModalOpen(true);
    setPopJobsChecked([]);
    const savedProfile = localStorage.getItem('user_data');
    if (savedProfile) {
      try {
        const profile = JSON.parse(savedProfile);
        setPopProfileContext(profile.summary || '');
      } catch (e) {}
    }
  };

  const handlePopulateSubmit = async () => {
    if (popJobsChecked.length === 0) {
      alert("Please select at least one job opportunity.");
      return;
    }
    setPopSubmitLoading(true);
    addLog(`Enqueuing outreach items for Campaign ${popCampaignId}...`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/${popCampaignId}/populate`, {
        method: 'POST',
        body: JSON.stringify({
          job_ids: popJobsChecked,
          user_profile_summary: popProfileContext
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Queue population failed');
      
      addLog(`✓ QUEUE POPULATED: Generated ${data.total || 0} scheduled variants staggered.`, "success");
      setPopulateModalOpen(false);
      fetchCampaigns();
      fetchQueue();
    } catch (err) {
      alert("Enqueuing failed: " + err.message);
      addLog(`Enqueuing failed: ${err.message}`, "error");
    } finally {
      setPopSubmitLoading(false);
    }
  };

  const triggerManualQueueSend = async (campaignId, queueItemId) => {
    addLog(`Executing queue outreach item ${queueItemId} immediately...`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/campaigns/${campaignId}/queue/${queueItemId}/send`, {
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) {
        if (data.detail && data.detail.error_type === "SUPPRESSED_FALLBACK") {
          setFallbackDetail(data.detail);
          setSuppressionModalOpen(true);
          addLog(`⚠️ GMass suppression block for ${data.detail.recipient}. Preserved message body.`, "error");
          addLog(`💡 Active fallback option: Redirecting user to manual outreach.`, "info");
          fetchQueue();
          return;
        }
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Send failed');
      }
      addLog(`✓ SEND SUCCESS: Item ${queueItemId} sent via GMass API.`, "success");
      fetchQueue();
    } catch (err) {
      addLog(`✗ SEND FAILURE: Item ${queueItemId} failed: ${err.message}`, "error");
      alert("Send failed: " + err.message);
      fetchQueue();
    }
  };

  const copyToClipboard = (text, successMsg) => {
    navigator.clipboard.writeText(text);
    addLog(successMsg, "info");
  };

  const openManualLinkedInSearch = (email) => {
    const domain = email.split('@')[1] || "";
    const companyName = domain.split('.')[0] || "";
    const searchUrl = `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(companyName + ' recruiting')}`;
    window.open(searchUrl, '_blank');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem' }}>
        {/* Create Campaign Left */}
        <div className="card" style={{ height: 'max-content' }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Create Outreach Campaign</h2>
          <form onSubmit={handleCreateCampaignSubmit}>
            <div className="input-group">
              <label className="input-label">Campaign Name</label>
              <input 
                type="text" 
                value={campName} 
                onChange={(e) => setCampName(e.target.value)}
                required 
                placeholder="Q2 Backend Engineering Outreach" 
              />
            </div>
            <div className="input-group">
              <label className="input-label">Target Role</label>
              <input 
                type="text" 
                value={campRole} 
                onChange={(e) => setCampRole(e.target.value)}
                required 
                placeholder="Python Developer" 
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div className="input-group">
                <label className="input-label">Hourly Email Cap</label>
                <input 
                  type="number" 
                  value={maxPerHour} 
                  onChange={(e) => setMaxPerHour(parseInt(e.target.value))}
                  min="1" 
                  max="50" 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Contacts / Company</label>
                <input 
                  type="number" 
                  value={maxContacts} 
                  onChange={(e) => setMaxContacts(parseInt(e.target.value))}
                  min="1" 
                  max="10" 
                />
              </div>
            </div>
            <div className="input-group">
              <label className="input-label">Stagger Interval (min)</label>
              <input 
                type="number" 
                value={stagger} 
                onChange={(e) => setStagger(parseInt(e.target.value))}
                min="5" 
                max="120" 
              />
            </div>
            <button className="btn btn-primary" type="submit" style={{ width: '100%', marginTop: '0.5rem' }}>
              <span>Create Campaign</span>
            </button>
          </form>
        </div>

        {/* Active Campaigns Right */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Active Campaigns</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {campaigns.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '3rem' }}>
                No campaigns found. Create one.
              </div>
            ) : (
              campaigns.map((c) => {
                const isFocus = focusedCampaignId === c.id;
                return (
                  <div key={c.id} className={`card ${isFocus ? 'active' : ''}`} style={{ padding: '1.25rem', borderColor: isFocus ? 'var(--primary)' : 'var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                      <div>
                        <div style={{ fontWeight: 800, color: 'white', fontSize: '1.05rem' }}>{c.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--primary-light)', fontWeight: 700, marginTop: '0.15rem' }}>
                          Role: {c.target_role || 'General'}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span className={`status-badge ${c.status === 'active' ? 'replied' : 'pending'}`}>
                          {c.status === 'active' ? 'Active' : 'Paused'}
                        </span>
                        <button 
                          className="btn" 
                          style={{ padding: '0.25rem 0.4rem', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '6px', cursor: 'pointer' }} 
                          title="Delete Campaign"
                          onClick={() => triggerDeleteCampaign(c.id, c.name)}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', textAlign: 'center', fontSize: '0.75rem', marginBottom: '1rem', background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: '10px' }}>
                      <div><div style={{ color: 'white', fontWeight: 700 }}>{c.queue_size}</div><div style={{ color: 'var(--text-dim)', fontSize: '0.6rem' }}>Queue</div></div>
                      <div><div style={{ color: 'white', fontWeight: 700 }}>{c.sent_count}</div><div style={{ color: 'var(--text-dim)', fontSize: '0.6rem' }}>Sent</div></div>
                      <div><div style={{ color: 'white', fontWeight: 700 }}>{c.pending_count}</div><div style={{ color: 'var(--text-dim)', fontSize: '0.6rem' }}>Pending</div></div>
                      <div><div style={{ color: 'white', fontWeight: 700 }}>{c.failed_count}</div><div style={{ color: 'var(--text-dim)', fontSize: '0.6rem' }}>Failed</div></div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.72rem', flex: 1 }} onClick={() => selectCampaign(isFocus ? null : c.id)}>
                        <span>{isFocus ? 'Focus Mode Active' : 'Focus Mode'}</span>
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.72rem' }} onClick={() => toggleCampaignState(c.id, c.status)}>
                        <span>{c.status === 'active' ? 'Pause' : 'Start'}</span>
                      </button>
                      <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.72rem' }} onClick={() => openPopulateQueueModal(c.id)}>
                        <span>Populate</span>
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Queue Explorer */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.1rem', margin: 0 }}>📊 Live Outreach Queue Explorer</h2>
          <select 
            value={queueCampaignFilter}
            onChange={(e) => setQueueCampaignFilter(e.target.value)}
            style={{ padding: '0.4rem 0.75rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border)', borderRadius: '8px' }}
          >
            <option value="">All Campaigns</option>
            {campaigns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        
        {queueLoading ? (
          <div style={{ textRendering: 'center', padding: '2rem', color: 'var(--text-dim)' }}><div className="loader" style={{ display: 'block', margin: '0 auto' }}></div></div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="queue-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                  <th style={{ padding: '0.75rem' }}>Time</th>
                  <th style={{ padding: '0.75rem' }}>Recipient</th>
                  <th style={{ padding: '0.75rem' }}>Style</th>
                  <th style={{ padding: '0.75rem' }}>Subject</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Priority</th>
                  <th style={{ padding: '0.75rem' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {queueItems.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '2rem' }}>
                      Queue is empty. Trigger campaign population.
                    </td>
                  </tr>
                ) : (
                  queueItems.map((item) => {
                    const date = item.scheduled_at 
                      ? new Date(item.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
                      : 'Immediate';
                    return (
                      <tr key={item.id} style={{ borderBottom: '1px solid var(--border)', fontSize: '0.82rem' }}>
                        <td style={{ padding: '0.75rem', fontWeight: 700, color: 'white' }}>{date}</td>
                        <td style={{ padding: '0.75rem' }}>
                          <div style={{ fontWeight: 700, color: 'white' }}>{item.recipient_email}</div>
                          <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>{item.recipient_type || 'Alias'}</div>
                        </td>
                        <td style={{ padding: '0.75rem' }}><span className="badge badge-purple">{item.outreach_style || 'Technical'}</span></td>
                        <td style={{ padding: '0.75rem', color: 'var(--text-dim)', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {item.subject || 'Outreach Title'}
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <span className={`status-badge ${item.status === 'sent' ? 'replied' : (item.status === 'suppressed' || item.status === 'failed') ? 'failed' : 'pending'}`}>
                            {item.status}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem', fontWeight: 800, color: 'white' }}>P{item.priority || 1}</td>
                        <td style={{ padding: '0.75rem' }}>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.68rem' }}
                            onClick={() => triggerManualQueueSend(item.campaign_id, item.id)}
                          >
                            Send Now
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Populate Queue Modal */}
      {populateModalOpen && (
        <div className="auth-overlay" style={{ display: 'flex', zIndex: 100 }}>
          <div className="card" style={{ maxWidth: '500px', width: '90%', padding: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: 'white' }}>Populate Outreach Queue</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '1.5rem' }}>
              Generate staggered, highly personalized outreach drafts using the cognitive match explainer model.
            </p>

            <div style={{ marginBottom: '1rem' }}>
              <label className="input-label">Select Opportunities to Target</label>
              <div style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '0.75rem', maxHeight: '180px', overflowY: 'auto' }}>
                {jobs.length === 0 ? (
                  <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem', textAlign: 'center' }}>
                    No jobs parsed. Search for roles first.
                  </div>
                ) : (
                  jobs.map(job => (
                    <label key={job.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'white', fontSize: '0.8rem', marginBottom: '0.4rem', cursor: 'pointer' }}>
                      <input 
                        type="checkbox" 
                        value={job.id}
                        checked={popJobsChecked.includes(job.id)}
                        onChange={(e) => {
                          const id = parseInt(e.target.value);
                          if (e.target.checked) {
                            setPopJobsChecked(prev => [...prev, id]);
                          } else {
                            setPopJobsChecked(prev => prev.filter(x => x !== id));
                          }
                        }}
                      />
                      <span>{job.title} at <b>{job.company}</b></span>
                    </label>
                  ))
                )}
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Override User Profile Context (Optional)</label>
              <textarea 
                value={popProfileContext}
                onChange={(e) => setPopProfileContext(e.target.value)}
                placeholder="Include custom achievements or project highlights..." 
                rows="3"
                style={{ width: '100%', resize: 'none' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setPopulateModalOpen(false)}>
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                style={{ flex: 1 }} 
                onClick={handlePopulateSubmit}
                disabled={popSubmitLoading}
              >
                {popSubmitLoading ? <div className="loader" style={{ display: 'block' }}></div> : <span>Confirm & Enqueue</span>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Suppression Fallback Modal */}
      {suppressionModalOpen && fallbackDetail && (
        <div className="auth-overlay" style={{ display: 'flex', zIndex: 110 }}>
          <div className="card" style={{ maxWidth: '600px', width: '95%', padding: '2rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>⚠️ GMass Suppression Triggered</span>
            </h2>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
              Recipient: <b>{fallbackDetail.recipient}</b> ({fallbackDetail.reason || 'Suppressed Channel'})
            </div>

            <div className="input-group">
              <label className="input-label">Preserved Subject Line</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                  type="text" 
                  value={fallbackDetail.preserved_subject || ''} 
                  readOnly 
                  style={{ flex: 1 }}
                />
                <button 
                  className="btn btn-secondary" 
                  style={{ padding: '0.5rem 0.75rem', fontSize: '0.75rem' }}
                  onClick={() => copyToClipboard(fallbackDetail.preserved_subject || '', '✓ Subject copied')}
                >
                  Copy
                </button>
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Preserved Outreach Message Body</label>
              <textarea 
                value={fallbackDetail.preserved_body || ''} 
                readOnly
                rows="6"
                style={{ width: '100%', resize: 'none', fontSize: '0.8rem', fontFamily: 'monospace' }}
              />
              <button 
                className="btn btn-secondary" 
                style={{ width: '100%', marginTop: '0.5rem', padding: '0.5rem', fontSize: '0.75rem' }}
                onClick={() => copyToClipboard(fallbackDetail.preserved_body || '', '✓ Message body copied')}
              >
                Copy Message Body
              </button>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setSuppressionModalOpen(false)}>
                Dismiss Fallback
              </button>
              <button 
                className="btn btn-primary" 
                style={{ flex: 1 }} 
                onClick={() => openManualLinkedInSearch(fallbackDetail.recipient)}
              >
                Open Manual LinkedIn Search
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
