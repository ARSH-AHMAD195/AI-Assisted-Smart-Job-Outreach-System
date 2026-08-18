import React, { useState, useEffect, useRef } from 'react';
import { 
  ArrowRight, Mail, FileText, Layers, Activity, Zap, 
  Search, Database, Sparkles, Code, CheckCircle2, Play, 
  Cpu, MousePointerClick, RefreshCw, BarChart2, ShieldAlert,
  Send, Eye, MessageSquare, AlertCircle
} from 'lucide-react';

const COMPANIES_DATA = {
  Stripe: {
    name: 'Stripe',
    industry: 'Financial Technology',
    focus: 'payment infrastructure for the internet',
    fact: 'expanding API-first billing pipelines and global multi-currency scaling',
    culture: 'relentless developer experience, clean APIs, and elegant user-facing design',
    keywords: ['Stripe Billing', 'API Integration', 'DevEx', 'Global Scaling']
  },
  OpenAI: {
    name: 'OpenAI',
    industry: 'Artificial Intelligence',
    focus: 'artificial general intelligence and model infrastructure',
    fact: 'optimizing low-latency serving pipelines for GPT-4 and Gemini APIs',
    culture: 'rapid scaling of compute networks, safety engineering, and high-throughput systems',
    keywords: ['LLM Serving', 'Latency Optimization', 'AI Pipelines', 'Compute Scaling']
  },
  Google: {
    name: 'Google',
    industry: 'Search & Cloud Platforms',
    focus: 'organizing the world\'s information at multi-million QPS scale',
    fact: 'modernizing distributed Kubernetes clusters and core search retrieval indices',
    culture: 'engineering reliability at planet-scale, structured data pipelines, and low-level optimizations',
    keywords: ['Kubernetes', 'Search Indexing', 'Planet-Scale QPS', 'Performance Tuning']
  }
};

const ROLES_DATA = {
  'Frontend Engineer': {
    title: 'Frontend Engineer',
    skills: 'React, TypeScript, Vite, High-Performance Canvas, DOM-free rendering systems',
    outreachHook: 'I love building ultra-fluid, zero-reflow UIs that load in microseconds.'
  },
  'FastAPI Backend Engineer': {
    title: 'FastAPI Backend Engineer',
    skills: 'FastAPI, PostgreSQL, AsyncIO, Python, spaCy NLP models, background workers',
    outreachHook: 'I specialize in low-latency async services, robust database schemas, and scraping automation.'
  },
  'ML Platform Engineer': {
    title: 'ML Platform Engineer',
    skills: 'Model deployment, API caching, latency optimization, vector search indexing',
    outreachHook: 'I focus on building resilient model orchestration pipelines and optimizing token inference times.'
  }
};

export const LandingPage = ({ onSignIn }) => {
  // Playground 1 State (AI Customizer)
  const [selectedCompany, setSelectedCompany] = useState('Stripe');
  const [selectedRole, setSelectedRole] = useState('Frontend Engineer');

  // Playground 2 State (Webhook Feed Simulator)
  const [logs, setLogs] = useState([
    { id: 1, time: '12:04:10', type: 'info', text: 'Playwright scraper cluster initialized: 4 headless instances ready' },
    { id: 2, time: '12:04:12', type: 'success', text: 'Naukri Crawler: Discovered 12 active job postings matching credentials' },
    { id: 3, time: '12:04:15', type: 'info', text: 'spaCy NLP Pipeline: Parsed PDF resume -> Extracted 18 target skills' }
  ]);
  const logCounter = useRef(4);
  const logContainerRef = useRef(null);

  // Webhook log simulation loop
  useEffect(() => {
    const mockEvents = [
      { type: 'success', text: 'Gemini reasoning: Matches candidates to Stripe DevEx team (Relevance: 94%)' },
      { type: 'info', text: 'Gemini reasoning: Generating tailored outreach email subject and payload' },
      { type: 'success', text: 'GMass API dispatch: Sent transactional message (ID: msg_stripe_91823)' },
      { type: 'success', text: 'GMass Webhook: Received Event=Open (ID: msg_stripe_91823, Recipient: dev-recruiting@stripe.com)' },
      { type: 'warning', text: 'GMass Webhook: Received Event=Click (Link: resume_pdf_link)' },
      { type: 'success', text: 'GMass Webhook: Received Event=Reply (ID: msg_stripe_91823, Status: Reply tracked)' },
      { type: 'info', text: 'Database sync: Upgraded dev-recruiting@stripe.com contact state to [REPLIED]' },
      { type: 'success', text: 'Naukri Crawler: Discovered 8 new jobs for Google ML Platform' },
      { type: 'success', text: 'Gemini reasoning: Matches candidates to Google ML Platform (Relevance: 88%)' },
      { type: 'info', text: 'GMass API dispatch: Sent transactional message (ID: msg_google_81923)' },
      { type: 'success', text: 'GMass Webhook: Received Event=Open (ID: msg_google_81923, Recipient: eng-hiring@google.com)' }
    ];

    const interval = setInterval(() => {
      const randomEvent = mockEvents[Math.floor(Math.random() * mockEvents.length)];
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];
      
      setLogs(prev => [
        ...prev.slice(-30), // Keep last 30 logs
        {
          id: logCounter.current++,
          time: timeStr,
          type: randomEvent.type,
          text: randomEvent.text
        }
      ]);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Auto-scroll logs container internally (without scrolling the main page viewport)
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Highlight blocks inside the editor preview
  const comp = COMPANIES_DATA[selectedCompany];
  const role = ROLES_DATA[selectedRole];

  return (
    <div className="landing-page" style={{ width: '100%', height: '100vh', overflowY: 'auto', background: '#07090e', color: '#f3f4f6', fontFamily: 'Outfit, Inter, sans-serif' }}>
      
      {/* 1. Header Navigation */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 3rem', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, background: 'rgba(7, 9, 14, 0.85)', backdropFilter: 'blur(12px)', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 800, fontSize: '1.25rem', color: '#fff' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent-purple) 100%)' }}>
            <Sparkles size={16} color="#fff" />
          </div>
          Outreach AI
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: '2.5rem' }}>
          <a href="#editor-sandbox" style={{ color: 'var(--text-dim)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600, transition: 'color 0.2s' }} className="nav-link">Personalization</a>
          <a href="#webhook-dashboard" style={{ color: 'var(--text-dim)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600, transition: 'color 0.2s' }} className="nav-link">Campaign Tracking</a>
          <a href="#pipeline-specs" style={{ color: 'var(--text-dim)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600, transition: 'color 0.2s' }} className="nav-link">Architecture</a>
        </nav>
        <button className="btn btn-primary" onClick={onSignIn} style={{ boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)' }}>
          Launch Workspace <ArrowRight size={16} />
        </button>
      </header>

      {/* 2. Hero Section */}
      <section style={{ position: 'relative', padding: '7rem 3rem 5rem 3rem', maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
        {/* Glow Effects */}
        <div style={{ position: 'absolute', width: '350px', height: '350px', background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)', top: '10%', left: '50%', transform: 'translateX(-50%)', pointerEvents: 'none', zIndex: 0 }} />
        
        <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', borderRadius: '20px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', color: 'var(--primary-light)', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '1.5rem' }}>
            <Zap size={12} /> Autonomous Job Outreach System
          </div>
          <h1 style={{ fontSize: '3.75rem', fontWeight: 800, lineHeight: 1.15, letterSpacing: '-1.5px', marginBottom: '1.5rem', maxWidth: '850px', background: 'linear-gradient(135deg, #fff 50%, var(--text-dim) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Automate Job Discovery, AI Alignment, & Cold Email Outreach
          </h1>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-dim)', lineHeight: 1.6, marginBottom: '2.5rem', maxWidth: '720px' }}>
            A production-grade pipeline running background crawls on Naukri, extracting PDF skills via spaCy, matching candidates with Gemini LLM reasoning, and dispatching cold outreach via GMass with real-time webhook analytics.
          </p>
          <div style={{ display: 'flex', gap: '1.25rem', marginBottom: '4rem' }}>
            <button className="btn btn-primary" onClick={onSignIn} style={{ padding: '0.9rem 2rem', fontSize: '1rem' }}>
              Launch Console Workspace <ArrowRight size={18} />
            </button>
            <a href="#editor-sandbox" className="btn btn-secondary" style={{ padding: '0.9rem 2rem', fontSize: '1rem', textDecoration: 'none' }}>
              Explore Sandbox Demos
            </a>
          </div>

          {/* Core Metrics Badges */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', width: '100%', maxWidth: '880px' }}>
            <div className="card" style={{ padding: '1.5rem', background: 'rgba(11, 15, 25, 0.6)', border: '1px solid var(--border)', borderRadius: '16px', backdropFilter: 'blur(10px)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>Campaigns Launched</div>
              <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary-light)', marginTop: '0.5rem' }}>12</div>
            </div>
            <div className="card" style={{ padding: '1.5rem', background: 'rgba(11, 15, 25, 0.6)', border: '1px solid var(--border)', borderRadius: '16px', backdropFilter: 'blur(10px)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>Emails Dispatched</div>
              <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary-light)', marginTop: '0.5rem' }}>3,420</div>
            </div>
            <div className="card" style={{ padding: '1.5rem', background: 'rgba(11, 15, 25, 0.6)', border: '1px solid var(--border)', borderRadius: '16px', backdropFilter: 'blur(10px)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>Open Rate</div>
              <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '0.5rem' }}>68%</div>
            </div>
            <div className="card" style={{ padding: '1.5rem', background: 'rgba(11, 15, 25, 0.6)', border: '1px solid var(--border)', borderRadius: '16px', backdropFilter: 'blur(10px)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' }}>Replies Received</div>
              <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '0.5rem' }}>142</div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Playground 1: AI Customizer Sandbox */}
      <section id="editor-sandbox" style={{ padding: '5rem 3rem', background: '#0a0d17', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '4rem', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', borderRadius: '20px', background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)', color: 'var(--accent-purple)', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '1.5rem' }}>
              <Sparkles size={12} /> Customizer Sandbox
            </div>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-1px', marginBottom: '1.25rem', lineHeight: 1.2 }}>
              Dynamic Personalization Playground
            </h2>
            <p style={{ color: 'var(--text-dim)', lineHeight: 1.6, marginBottom: '2rem', fontSize: '1rem' }}>
              The system merges your parsed qualifications with company details fetched by Gemini. Select different targets and roles to observe the dynamic payload generation.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '2rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Target Company</label>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  {Object.keys(COMPANIES_DATA).map(name => (
                    <button 
                      key={name}
                      onClick={() => setSelectedCompany(name)}
                      className={`btn ${selectedCompany === name ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', flex: 1 }}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Candidate Role</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {Object.keys(ROLES_DATA).map(name => (
                    <button 
                      key={name}
                      onClick={() => setSelectedRole(name)}
                      className={`btn ${selectedRole === name ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', textAlign: 'left' }}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1rem 1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <CheckCircle2 size={14} style={{ color: 'var(--accent-green)' }} />
                <span style={{ fontSize: '0.8rem', fontWeight: 700 }}>Gemini Enrichment Active</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', lineHeight: 1.5 }}>
                Outreach hook automatically aligns with <strong style={{ color: '#fff' }}>{comp.name}</strong>'s cultural theme: <em>{comp.culture}</em>.
              </div>
            </div>
          </div>

          {/* Email Preview IDE Mockup */}
          <div className="card" style={{ background: '#07090e', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 12px 24px rgba(0,0,0,0.3)', display: 'flex', flexDirection: 'column', gap: '1rem', alignSelf: 'stretch', minHeight: '420px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }} />
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }} />
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }} />
              <span style={{ marginLeft: '1rem', fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'monospace' }}>outreach_template.json</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.88rem', lineHeight: 1.6, flex: 1, fontFamily: 'monospace', color: '#cbd5e1' }}>
              <div>
                <span style={{ color: 'var(--accent-purple)' }}>"subject":</span> <span style={{ color: 'var(--accent-green)' }}>"Outreach — {role.title} alignment at {comp.name}"</span>
              </div>
              <div>
                <span style={{ color: 'var(--accent-purple)' }}>"body":</span> <span style={{ color: '#94a3b8' }}>{"{"}</span>
              </div>
              <div style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <p style={{ margin: 0 }}>
                  "Dear {comp.name} Recruitment,
                </p>
                <p style={{ margin: 0 }}>
                  I noticed your development focusing on <span style={{ borderBottom: '2px solid var(--primary)', padding: '0.1rem 0.3rem', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary-light)', borderRadius: '4px' }}>{comp.focus}</span>, specifically {comp.fact}. Having reviewed your tech stack, I resonate with your engineering theme of {comp.culture}.
                </p>
                <p style={{ margin: 0 }}>
                  As a <span style={{ borderBottom: '2px solid var(--accent-purple)', padding: '0.1rem 0.3rem', background: 'rgba(168, 85, 247, 0.1)', color: 'var(--accent-purple-light)', borderRadius: '4px' }}>{role.title}</span> skilled in {role.skills}, {role.outreachHook}
                </p>
                <p style={{ margin: 0 }}>
                  I would love to explore how my automation projects align with {comp.name}'s open pipeline roles."
                </p>
              </div>
              <div>
                <span style={{ color: '#94a3b8' }}>{"}"}</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              <span>Target matches: {comp.keywords.join(', ')}</span>
              <span style={{ color: 'var(--accent-green)' }}>Relevance Score: 94%</span>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Playground 2: Webhook Dashboard & Console */}
      <section id="webhook-dashboard" style={{ padding: '5rem 3rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '4rem', alignItems: 'center' }}>
          
          {/* Live scrolling logger terminal */}
          <div className="card" style={{ background: '#030508', border: '1px solid var(--border)', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 12px 30px rgba(0,0,0,0.4)', height: '360px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={14} style={{ color: 'var(--primary-light)', animation: 'pulse 2s infinite' }} />
                <span style={{ fontSize: '0.8rem', fontWeight: 700, fontFamily: 'monospace' }}>gmass_webhook_daemon.log</span>
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--accent-green)', fontWeight: 700, background: 'rgba(16, 185, 129, 0.1)', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>LISTENING ON PORT 8000</span>
            </div>

            {/* Logs area */}
            <div ref={logContainerRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.65rem', fontFamily: 'monospace', fontSize: '0.8rem' }}>
              {logs.map((log) => {
                let badgeColor = 'var(--text-dim)';
                if (log.type === 'success') badgeColor = 'var(--accent-green)';zz
                if (log.type === 'warning') badgeColor = 'var(--accent-yellow)';
                
                return (
                  <div key={log.id} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', borderLeft: `2px solid ${badgeColor}`, paddingLeft: '0.5rem' }}>
                    <span style={{ color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>[{log.time}]</span>
                    <span style={{ color: log.type === 'success' ? '#e2e8f0' : '#cbd5e1' }}>{log.text}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', borderRadius: '20px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', color: 'var(--accent-green)', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '1.5rem' }}>
              <Activity size={12} /> Live Event Analytics
            </div>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-1px', marginBottom: '1.25rem', lineHeight: 1.2 }}>
              Real-time Webhook Campaigns
            </h2>
            <p style={{ color: 'var(--text-dim)', lineHeight: 1.6, marginBottom: '2rem', fontSize: '1rem' }}>
              Our GMass Webhook receiver captures transactional email events (opens, links clicked, replies) and links them back to candidate outreach templates instantly.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1rem 1.25rem' }}>
              <div>
                <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.25rem' }}>Webhook Endpoint</span>
                <code style={{ fontSize: '0.85rem', color: 'var(--primary-light)' }}>/webhooks/gmass</code>
              </div>
              <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: '1.5rem' }}>
                <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.25rem' }}>Database Sync</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Async SQLite / Postgres</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. System Core Specifications Section */}
      <section id="pipeline-specs" style={{ padding: '6rem 3rem', background: '#0a0d17', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4.5rem' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-1px', marginBottom: '1rem' }}>
              Autonomous Technical Pipeline
            </h2>
            <p style={{ color: 'var(--text-dim)', maxWidth: '640px', margin: '0 auto', lineHeight: 1.6, fontSize: '1rem' }}>
              How the underlying scraping, extraction, and message delivery channels coordinate.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '2rem' }}>
            
            <div className="card" style={{ padding: '2rem', background: 'rgba(7, 9, 14, 0.4)' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--primary-light)' }}>
                <Search size={20} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Playwright Discovery</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Headless browser instances crawl Naukri.com, filter listings dynamically, and store raw target information.
              </p>
            </div>

            <div className="card" style={{ padding: '2rem', background: 'rgba(7, 9, 14, 0.4)' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-purple)' }}>
                <Cpu size={20} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Gemini Extraction</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Structured response schema parsing matches candidates to active departments, products, and culture.
              </p>
            </div>

            <div className="card" style={{ padding: '2rem', background: 'rgba(7, 9, 14, 0.4)' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-green)' }}>
                <Mail size={20} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>GMass Integrator</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Dispatches transactional emails via GMass API with tracking tokens to listen for real-time open and reply events.
              </p>
            </div>

            <div className="card" style={{ padding: '2rem', background: 'rgba(7, 9, 14, 0.4)' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-yellow)' }}>
                <FileText size={20} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>spaCy Parser</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                NLP models extract candidate credentials from resumes to calculate precise relevance scores for target jobs.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* 6. CTA / Footer Section */}
      <section style={{ padding: '6rem 3rem', textAlign: 'center', position: 'relative' }}>
        <div style={{ position: 'absolute', width: '250px', height: '250px', background: 'radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%)', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', pointerEvents: 'none' }} />
        
        <h2 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem', letterSpacing: '-1px' }}>
          Launch Your Autonomous Campaign
        </h2>
        <p style={{ color: 'var(--text-dim)', maxWidth: '580px', margin: '0 auto 2.5rem auto', lineHeight: 1.6, fontSize: '1.05rem' }}>
          Sign up to connect your profile, parser resumes, monitor Naukri matching, and manage transactional Cold Outreach campaigns.
        </p>
        <button className="btn btn-primary" onClick={onSignIn} style={{ padding: '0.95rem 2.25rem', fontSize: '1rem', boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)' }}>
          Launch Console Workspace <ArrowRight size={18} />
        </button>
      </section>

      <footer style={{ borderTop: '1px solid var(--border)', padding: '2rem 3rem', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
        <p>© 2026 AI-Assisted Smart Job Outreach System. All rights reserved.</p>
      </footer>
    </div>
  );
};
