import React, { useContext, useState } from 'react';
import { AppContext } from '../context/AppContext';

export const ContactsTab = () => {
  const { 
    companies, 
    selectedCompanyName, 
    selectCompany 
  } = useContext(AppContext);

  const [companySearch, setCompanySearch] = useState('');

  const filtered = companies.filter(c => c.name.toLowerCase().includes(companySearch.toLowerCase()));

  const selectedComp = companies.find(c => c.name === selectedCompanyName);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.8fr', gap: '1.5rem' }}>
      {/* Left Column: Company Directory */}
      <div className="card" style={{ height: 'max-content' }}>
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Target Companies</h2>
        <p style={{ color: 'var(--text-dim)', marginBottom: '1rem', fontSize: '0.82rem' }}>
          Historical memory database of enriched entities.
        </p>

        <input 
          type="text" 
          value={companySearch}
          onChange={(e) => setCompanySearch(e.target.value)}
          placeholder="Filter companies..." 
          style={{ width: '100%', marginBottom: '1rem' }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '420px', overflowY: 'auto' }}>
          {filtered.length === 0 ? (
            <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '2rem', fontSize: '0.8rem' }}>
              No companies match search.
            </div>
          ) : (
            filtered.map((c) => (
              <div 
                key={c.name}
                className={`interactive-row ${selectedCompanyName === c.name ? 'active' : ''}`}
                onClick={() => selectCompany(c.name)}
              >
                <div>
                  <div style={{ fontWeight: 700, color: 'white' }}>{c.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>
                    Domain: {c.url}
                  </div>
                </div>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--text-dim)' }}>
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Column: Detailed Enriched Intel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {selectedComp ? (
          <>
            {/* Company Memory */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', color: 'white', margin: 0 }}>{selectedComp.name}</h2>
                  <a 
                    href={selectedComp.url} 
                    target="_blank" 
                    rel="noreferrer"
                    style={{ fontSize: '0.8rem', color: 'var(--primary-light)', fontWeight: 700, textDecoration: 'none' }}
                  >
                    {selectedComp.url}
                  </a>
                </div>
              </div>

              {/* Signals */}
              <h3 style={{ fontSize: '0.9rem', color: 'white', marginBottom: '0.5rem' }}>🧠 Contextual Signals</h3>
              <ul style={{ paddingLeft: '1.2rem', margin: '0 0 1.25rem', fontSize: '0.82rem', color: 'var(--text-dim)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <li className="signal-item">Prefers project-based technical outreach variants</li>
                <li className="signal-item">Weak response conversion from corporate HR aliases</li>
                <li className="signal-item">Active hiring spikes in Kubernetes & microservices architecture</li>
              </ul>

              {/* Timeline */}
              <h3 style={{ fontSize: '0.9rem', color: 'white', marginBottom: '0.75rem' }}>⏳ Relationship Timeline</h3>
              <div className="timeline-container" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div className="timeline-event">
                  <div className="timeline-date">May 12, 2026</div>
                  <div className="timeline-desc">Outreach scheduled (Technical style variant)</div>
                </div>
                <div className="timeline-event">
                  <div className="timeline-date">May 14, 2026</div>
                  <div className="timeline-desc">Email opened. Inferred role match 82%.</div>
                </div>
                <div className="timeline-event">
                  <div className="timeline-date">May 15, 2026</div>
                  <div className="timeline-desc">CTO profile crawled & contact enqueued.</div>
                </div>
              </div>
            </div>

            {/* Contact Details */}
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>👥 Contact Intelligence</h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-dim)', textAlign: 'left' }}>
                      <th style={{ padding: '0.5rem' }}>Channel / Handle</th>
                      <th style={{ padding: '0.5rem' }}>Type</th>
                      <th style={{ padding: '0.5rem' }}>Confidence</th>
                      <th style={{ padding: '0.5rem' }}>Provenance</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: 'white' }}>
                        careers@{selectedComp.name.toLowerCase().replace(/[^a-z]/g, '')}.com
                      </td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>Hiring Channel</td>
                      <td style={{ padding: '0.75rem 0.5rem' }}><span className="confidence-tag high">100%</span></td>
                      <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-dim)' }}>Enriched Corporate Careers Page</td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: 'white' }}>
                        cto@{selectedComp.name.toLowerCase().replace(/[^a-z]/g, '')}.com
                      </td>
                      <td style={{ padding: '0.75rem 0.5rem' }}>CTO / Engineering VP</td>
                      <td style={{ padding: '0.75rem 0.5rem' }}><span className="confidence-tag mid">84%</span></td>
                      <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-dim)' }}>LinkedIn Domain Pattern Inference</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="card" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-dim)' }}>
            Select a company from the left panel to inspect detailed signals and relationship memory.
          </div>
        )}
      </div>
    </div>
  );
};
