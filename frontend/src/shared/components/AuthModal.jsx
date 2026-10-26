import React, { useState } from 'react';
import { loginUser, signupUser } from '../api/authApi';

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode); // 'login' or 'signup'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [birthday, setBirthday] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === 'signup') {
        if (!name.trim()) {
          throw new Error('Please enter your full name.');
        }
        if (!email.trim() || !email.includes('@')) {
          throw new Error('Please enter a valid email address.');
        }
        if (!birthday) {
          throw new Error('Please enter your birthday.');
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters long.');
        }

        const res = await signupUser({
          name: name.trim(),
          email: email.trim(),
          birthday,
          password,
        });

        setSuccessMsg('Account created successfully!');
        if (onAuthSuccess) {
          onAuthSuccess(res.user);
        }
        setTimeout(() => {
          onClose();
        }, 600);
      } else {
        if (!email.trim()) {
          throw new Error('Please enter your email address.');
        }
        if (!password) {
          throw new Error('Please enter your password.');
        }

        const res = await loginUser({
          email: email.trim(),
          password,
        });

        setSuccessMsg('Welcome back!');
        if (onAuthSuccess) {
          onAuthSuccess(res.user);
        }
        setTimeout(() => {
          onClose();
        }, 600);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchMode = (newMode) => {
    setMode(newMode);
    setError(null);
    setSuccessMsg(null);
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(26, 22, 18, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: '20px',
      }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        style={{
          background: 'var(--color-card)',
          borderRadius: 'var(--radius-xl)',
          maxWidth: 440,
          width: '100%',
          padding: '32px 28px',
          boxShadow: 'var(--shadow-warm-lg)',
          border: '1px solid var(--color-card-border)',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          style={{
            position: 'absolute',
            top: 20,
            right: 20,
            background: 'transparent',
            border: 'none',
            fontSize: '1.25rem',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: 4,
          }}
        >
          ✕
        </button>

        {/* Brand Tag */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--color-promo-green)',
              background: 'var(--color-canvas)',
              padding: '4px 12px',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--color-card-border)',
            }}
          >
            FoodVerse Account
          </span>
          <h2
            style={{
              fontFamily: 'var(--font-headings)',
              fontSize: '1.5rem',
              color: 'var(--color-text-primary)',
              marginTop: 10,
              marginBottom: 4,
            }}
          >
            {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: 0 }}>
            {mode === 'login'
              ? 'Log in to sync your scans, recipes, and personal reports.'
              : 'Join FoodVerse to save and track your personal nutrition data.'}
          </p>
        </div>

        {/* Toggle Mode Tabs */}
        <div
          style={{
            display: 'flex',
            background: 'var(--color-canvas)',
            padding: 4,
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--color-card-border)',
            marginBottom: 20,
          }}
        >
          <button
            type="button"
            onClick={() => handleSwitchMode('login')}
            style={{
              flex: 1,
              padding: '8px 0',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              background: mode === 'login' ? 'var(--color-card)' : 'transparent',
              color: mode === 'login' ? 'var(--color-primary-burgundy)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.85rem',
              boxShadow: mode === 'login' ? 'var(--shadow-warm-xs)' : 'none',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => handleSwitchMode('signup')}
            style={{
              flex: 1,
              padding: '8px 0',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              background: mode === 'signup' ? 'var(--color-card)' : 'transparent',
              color: mode === 'signup' ? 'var(--color-primary-burgundy)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.85rem',
              boxShadow: mode === 'signup' ? 'var(--shadow-warm-xs)' : 'none',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            Sign Up
          </button>
        </div>

        {/* Error / Success Feedback */}
        {error && (
          <div
            style={{
              padding: '10px 14px',
              background: 'var(--color-status-error-bg)',
              border: '1px solid var(--color-status-error)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-status-error)',
              fontSize: '0.82rem',
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div
            style={{
              padding: '10px 14px',
              background: 'var(--color-promo-bg)',
              border: '1px solid var(--color-promo-border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-promo-burgundy)',
              fontSize: '0.82rem',
              fontWeight: 600,
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>✓</span>
            <span>{successMsg}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {mode === 'signup' && (
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  color: 'var(--color-text-secondary)',
                  marginBottom: 6,
                }}
              >
                Full Name
              </label>
              <input
                type="text"
                placeholder="e.g. Shrey Pandey"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="input-base"
                style={{ width: '100%', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.78rem',
                fontWeight: 700,
                color: 'var(--color-text-secondary)',
                marginBottom: 6,
              }}
            >
              Email Address
            </label>
            <input
              type="email"
              placeholder="e.g. shrey@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="input-base"
              style={{ width: '100%', boxSizing: 'border-box' }}
            />
          </div>

          {mode === 'signup' && (
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  color: 'var(--color-text-secondary)',
                  marginBottom: 6,
                }}
              >
                Birthday
              </label>
              <input
                type="date"
                value={birthday}
                onChange={(e) => setBirthday(e.target.value)}
                required
                className="input-base"
                style={{ width: '100%', boxSizing: 'border-box' }}
              />
            </div>
          )}

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <label
                style={{
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  color: 'var(--color-text-secondary)',
                }}
              >
                Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--color-primary-burgundy)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder={mode === 'signup' ? 'At least 6 characters' : 'Enter your password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="input-base"
              style={{ width: '100%', boxSizing: 'border-box' }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-burgundy-action"
            style={{
              width: '100%',
              marginTop: 10,
              padding: '12px',
              fontSize: '0.92rem',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>{loading ? 'Processing...' : mode === 'login' ? 'Log In to FoodVerse' : 'Create Account'}</span>
            {!loading && <span aria-hidden="true">→</span>}
          </button>
        </form>

        {/* Footer switch prompt */}
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          {mode === 'login' ? (
            <span>
              Don't have an account yet?{' '}
              <button
                type="button"
                onClick={() => handleSwitchMode('signup')}
                style={{
                  color: 'var(--color-primary-burgundy)',
                  fontWeight: 700,
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Create one now
              </button>
            </span>
          ) : (
            <span>
              Already registered?{' '}
              <button
                type="button"
                onClick={() => handleSwitchMode('login')}
                style={{
                  color: 'var(--color-primary-burgundy)',
                  fontWeight: 700,
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Sign In
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
