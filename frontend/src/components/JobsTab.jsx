import React, { useContext, useState, useEffect } from 'react';
import { AppContext } from '../context/AppContext';

export const JobsTab = () => {
  const { 
    BASE_URL, 
    authFetch, 
    addLog, 
    jobs, 
    setJobs, 
    selectedJobId, 
    selectJob,
    explainData,
    setExplainData,
    setActiveTab
  } = useContext(AppContext);

  const [uploading, setUploading] = useState(false);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [skillsCount, setSkillsCount] = useState(0);
  const [inferredRoles, setInferredRoles] = useState([]);
  const [searchRole, setSearchRole] = useState('');
  const [searching, setSearching] = useState(false);

  // Restore resume profile state on mount
  useEffect(() => {
    const savedProfile = localStorage.getItem('user_data');
    const savedRoles = localStorage.getItem('inferred_roles');
    if (savedProfile) {
      try {
        const profile = JSON.parse(savedProfile);
        setProfileLoaded(true);
        setSkillsCount(profile.skills ? profile.skills.length : 0);
      } catch (e) {
        console.error(e);
      }
    }
    if (savedRoles) {
      try {
        setInferredRoles(JSON.parse(savedRoles));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    addLog(`Uploading resume: ${file.name}`, "action");
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${BASE_URL}/api/uploadfile/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const profile = await res.json();
      if (!res.ok) throw new Error(profile.detail || 'Resume parsing failed');
      
      localStorage.setItem('user_data', JSON.stringify(profile));
      setProfileLoaded(true);
      setSkillsCount(profile.skills.length);
      addLog(`✓ PROFILE PARSED: Extracted ${profile.skills.length} skills.`, "success");

      // Infer target roles
      addLog("Inferring target roles from profile...", "action");
      const inferRes = await fetch(`${BASE_URL}/api/jobs/infer-roles`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(profile)
      });
      
      if (inferRes.ok) {
        const rolesData = await inferRes.json();
        setInferredRoles(rolesData);
        localStorage.setItem('inferred_roles', JSON.stringify(rolesData));
        addLog(`✓ ROLE INFERENCE: Successfully inferred target roles.`, "success");
        
        const rolesArray = Array.isArray(rolesData) ? rolesData : (rolesData.roles || []);
        if (rolesArray.length > 0) {
          setSearchRole(rolesArray[0].role);
        }
      }
    } catch (err) {
      addLog(`Parsing failed: ${err.message}`, "error");
      alert('Resume parsing failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const clearResumeProfile = () => {
    localStorage.removeItem('user_data');
    localStorage.removeItem('inferred_roles');
    setProfileLoaded(false);
    setSkillsCount(0);
    setInferredRoles([]);
    setSearchRole('');
    addLog('✓ RESUME REMOVED: Resume profile and inferred roles cleared.', 'success');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--primary)';
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--border)';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--border)';
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const triggerJobDiscovery = async () => {
    if (!searchRole.trim()) {
      alert("Please enter a role keyword.");
      return;
    }
    setSearching(true);
    addLog(`Querying global job portals for: ${searchRole}...`, "action");
    try {
      const res = await authFetch(`${BASE_URL}/api/jobs/discover?role=${encodeURIComponent(searchRole)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Discovery failed');
      
      setJobs(data);
      addLog(`✓ DISCOVERY SUCCESS: Found ${data.length} matched listings.`, "success");
    } catch (err) {
      addLog(`Job search failed: ${err.message}`, "error");
      alert('Discovery search failed: ' + err.message);
    } finally {
      setSearching(false);
    }
  };

  const runExplainableMatch = async (job) => {
    const savedProfile = localStorage.getItem('user_data');
    if (!savedProfile || !job) return;
    
    addLog(`Initiating Match Diagnostics for ${job.title}...`, "action");
    try {
      const profile = JSON.parse(savedProfile);
      const payload = {
        user_profile: profile,
        jd_text: job.description,
        company_name: job.company,
        company_intel: null // AppContext's companyIntel is fetched on job selection
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
      setActiveTab('intelligence');
    } catch (err) {
      addLog(`Explain analysis failed: ${err.message}`, "error");
    }
  };

  const selectedJob = jobs.find(j => j.id === selectedJobId);
  const rolesArray = Array.isArray(inferredRoles) ? inferredRoles : (inferredRoles.roles || []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '1.5rem' }}>
        {/* Resume Analysis Left */}
        <div className="card" style={{ height: 'max-content' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Career Profile</h2>
            {profileLoaded && (
              <button 
                className="btn" 
                style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '6px', cursor: 'pointer' }}
                onClick={clearResumeProfile}
              >
                Remove Resume
              </button>
            )}
          </div>
          <p style={{ color: 'var(--text-dim)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
            Upload resume PDF to extract skills and infer target roles.
          </p>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <div 
              className={`upload-area ${profileLoaded ? 'success' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('resumeFileInput').click()}
              style={{ cursor: 'pointer' }}
            >
              <div className="upload-icon">📄</div>
              <h3 style={{ fontSize: '1rem', color: 'white', margin: '0.5rem 0 0' }}>
                {profileLoaded ? 'Profile Loaded' : 'Drop Resume here'}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
                {profileLoaded ? `✓ ${skillsCount} skills detected.` : 'PDF format only • Max 5MB'}
              </p>
              {uploading && <div className="loader" style={{ display: 'block', marginTop: '1rem' }}></div>}
            </div>
            <input 
              type="file" 
              id="resumeFileInput" 
              accept=".pdf" 
              style={{ display: 'none' }} 
              onChange={(e) => handleFileUpload(e.target.files[0])}
            />
          </div>

          {profileLoaded && rolesArray.length > 0 && (
            <div>
              <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem', color: 'white' }}>🎯 Recommended Roles</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {rolesArray.map((role, idx) => (
                  <div 
                    key={idx}
                    className="interactive-row" 
                    onClick={() => {
                      setSearchRole(role.role);
                      triggerJobDiscovery();
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, color: 'var(--primary-light)', fontSize: '0.9rem' }}>{role.role}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>{role.reason || role.reasoning || ''}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="confidence-tag high">{Math.round((role.confidence || 0.8) * 100)}%</span>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)', marginTop: '0.15rem', textTransform: 'uppercase' }}>Confidence</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Job Discovery Right */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Job Discovery Engine</h2>
          <p style={{ color: 'var(--text-dim)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
            Discover live job listings matched against inferred skills.
          </p>
          
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <input 
              type="text" 
              value={searchRole} 
              onChange={(e) => setSearchRole(e.target.value)}
              placeholder="Role title (e.g. Backend Engineer)" 
              style={{ flex: 1 }}
            />
            <button className="btn btn-primary" onClick={triggerJobDiscovery} disabled={searching}>
              {!searching ? <span>Discover</span> : <div className="loader" style={{ display: 'block' }}></div>}
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            {jobs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>
                Enter a role to query multi-portal discovery engine.
              </div>
            ) : (
              jobs.map((job) => (
                <div 
                  key={job.id} 
                  className={`interactive-row ${selectedJobId === job.id ? 'active' : ''}`} 
                  onClick={() => selectJob(job.id)}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: 'white', fontSize: '0.95rem' }}>{job.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--primary-light)', fontWeight: 600, marginTop: '0.15rem' }}>
                      {job.company} • {job.location || 'Remote'}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.25rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {job.description}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: '1rem' }}>
                    <span className="status-badge sent" style={{ fontSize: '0.6rem' }}>{job.platform || 'Naukri'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Expanded Selected Job Panel */}
      {selectedJob && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ color: 'white', fontSize: '1.25rem', margin: 0 }}>{selectedJob.title}</h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--primary-light)', fontWeight: 700, marginTop: '0.25rem' }}>
                {selectedJob.company} • {selectedJob.location || 'Remote'}
              </div>
            </div>
            {profileLoaded && (
              <button className="btn btn-primary" onClick={() => runExplainableMatch(selectedJob)}>
                <span>🧠 Deep Analyze Match</span>
              </button>
            )}
          </div>
          <div className="divider"></div>
          <div style={{ fontSize: '0.88rem', color: 'var(--text-dim)', lineHeight: '1.6', whiteSpace: 'pre-wrap', maxHeight: '250px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            {selectedJob.description}
          </div>
        </div>
      )}
    </div>
  );
};
