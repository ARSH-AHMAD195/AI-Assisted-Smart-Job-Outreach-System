import React, { useState, useContext } from 'react';
import { AppContext } from '../context/AppContext';

export const Auth = ({ onClose }) => {
  const { BASE_URL, setUser, setAccessToken, setRefreshToken, addLog } = useContext(AppContext);
  const [activeTab, setActiveTab] = useState('login'); // 'login' or 'signup'
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Login inputs
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Signup inputs
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');

  const triggerGoogleLogin = () => {
    window.location.href = `${BASE_URL}/auth/login/google`;
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const params = new URLSearchParams();
      params.append('username', loginEmail);
      params.append('password', loginPassword);

      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');

      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(data.user);
      addLog(`User logged in: ${data.user.full_name}`, "success");
      
      setLoginEmail('');
      setLoginPassword('');
    } catch (err) {
      addLog(`Login failed: ${err.message}`, "error");
      setErrorMsg('Login failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: signupName, email: signupEmail, password: signupPassword })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed');

      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(data.user);
      addLog(`User registered & logged in: ${data.user.full_name}`, "success");

      setSignupName('');
      setSignupEmail('');
      setSignupPassword('');
    } catch (err) {
      addLog(`Registration failed: ${err.message}`, "error");
      setErrorMsg('Registration failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-overlay" style={{ display: 'flex' }} onClick={(e) => {
      if (e.target.classList.contains('auth-overlay') && onClose) {
        onClose();
      }
    }}>
      <div className="auth-card" style={{ position: 'relative' }}>
        {onClose && (
          <button 
            type="button" 
            onClick={onClose} 
            style={{
              position: 'absolute',
              top: '1.25rem',
              right: '1.25rem',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              fontSize: '1.5rem',
              lineHeight: 1,
              padding: '0.25rem',
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => e.target.style.color = 'white'}
            onMouseLeave={(e) => e.target.style.color = 'var(--text-dim)'}
          >
            &times;
          </button>
        )}
        <div className="auth-logo">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          Outreach AI
        </div>

        <h2 style={{ marginBottom: '0.5rem', fontSize: '1.4rem' }}>
          {activeTab === 'login' ? 'Sign In' : 'Create Account'}
        </h2>
        <p style={{ color: 'var(--text-dim)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
          {activeTab === 'login' ? 'Access adaptive job discovery & outreach' : 'Set up your credentials to get started'}
        </p>

        {errorMsg && (
          <div style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', marginBottom: '1rem' }}>
            {errorMsg}
          </div>
        )}

        <div className="auth-tabs">
          <button 
            className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('login'); setErrorMsg(''); }}
          >
            Sign In
          </button>
          <button 
            className={`auth-tab ${activeTab === 'signup' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('signup'); setErrorMsg(''); }}
          >
            Create Account
          </button>
        </div>

        {activeTab === 'login' ? (
          <form onSubmit={handleLoginSubmit}>
            <div className="input-group">
              <label className="input-label" htmlFor="loginEmail">Email Address</label>
              <input 
                className="form-input" 
                type="email" 
                id="loginEmail" 
                required 
                placeholder="name@domain.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label className="input-label" htmlFor="loginPassword">Password</label>
              <input 
                className="form-input" 
                type="password" 
                id="loginPassword" 
                required 
                placeholder="••••••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
            </div>
            <button className="btn btn-primary" type="submit" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
              {!loading ? <span>Sign In</span> : <div className="loader" style={{ display: 'block' }}></div>}
            </button>
          </form>
        ) : (
          <form onSubmit={handleSignupSubmit}>
            <div className="input-group">
              <label className="input-label" htmlFor="signupName">Full Name</label>
              <input 
                className="form-input" 
                type="text" 
                id="signupName" 
                required 
                placeholder="John Doe"
                value={signupName}
                onChange={(e) => setSignupName(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label className="input-label" htmlFor="signupEmail">Email Address</label>
              <input 
                className="form-input" 
                type="email" 
                id="signupEmail" 
                required 
                placeholder="name@domain.com"
                value={signupEmail}
                onChange={(e) => setSignupEmail(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label className="input-label" htmlFor="signupPassword">Password</label>
              <input 
                className="form-input" 
                type="password" 
                id="signupPassword" 
                required 
                minLength={6} 
                placeholder="At least 6 characters"
                value={signupPassword}
                onChange={(e) => setSignupPassword(e.target.value)}
              />
            </div>
            <button className="btn btn-primary" type="submit" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
              {!loading ? <span>Create Account</span> : <div className="loader" style={{ display: 'block' }}></div>}
            </button>
          </form>
        )}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '1.25rem 0', gap: '0.5rem' }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border)' }}></div>
          <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem', transform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
            or continue with
          </span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border)' }}></div>
        </div>

        <button 
          type="button" 
          className="btn btn-secondary" 
          onClick={triggerGoogleLogin}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', transition: 'all 0.2s', padding: '0.75rem 1rem', borderRadius: '12px', cursor: 'pointer' }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v3.92h6.69a5.74 5.74 0 0 1-2.49 3.77v3.12h4.03c2.36-2.17 3.71-5.38 3.71-8.74z"/>
            <path fill="#34A853" d="M12 24c3.24 0 5.97-1.08 7.96-2.91l-3.12-3.12c-.87.58-1.97.93-3.08.93-2.33 0-4.31-1.57-5.02-3.69H4.57v3.22C6.55 22.18 9.07 24 12 24z"/>
            <path fill="#FBBC05" d="M6.98 15.21a7.18 7.18 0 0 1 0-4.42V7.57H4.57a12 12 0 0 0 0 8.86l2.41-3.22z"/>
            <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.43-3.43C17.96 1.19 15.24 0 12 0 9.07 0 6.55 1.82 4.57 4.75l2.41 3.22c.71-2.12 2.69-3.69 5.02-3.69z"/>
          </svg>
          <span style={{ fontWeight: 600, color: 'white' }}>Sign in with Google</span>
        </button>
      </div>
    </div>
  );
};
