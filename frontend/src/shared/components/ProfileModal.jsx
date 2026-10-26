import React from 'react';

const FEATURE_LABELS = {
  food_recognition: 'Food Recognition',
  freshness_analysis: 'Freshness Detector',
  hygiene_analysis: 'Hygiene Monitor',
  recipe_generation: 'Smart Kitchen',
  meal_plan: 'Meal Planner',
};

export default function ProfileModal({ isOpen, onClose, user, onLogout }) {
  if (!isOpen || !user) return null;

  const formatBirthday = (dateStr) => {
    if (!dateStr) return 'Not set';
    try {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        return d.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' });
      }
      return dateStr;
    } catch {
      return dateStr;
    }
  };

  const formatJoined = (isoStr) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return '';
    }
  };

  const initial = user.name ? user.name.charAt(0).toUpperCase() : 'U';
  const stats = user.stats || {};
  const totalReports = stats.total_reports || 0;
  const featureCounts = stats.counts_by_feature || {};

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
          maxWidth: 520,
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
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

        {/* Profile Header Card */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, paddingBottom: 20, borderBottom: '1px solid var(--color-card-border)' }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 'var(--radius-full)',
              background: 'var(--color-primary-burgundy)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'var(--font-headings)',
              fontSize: '1.7rem',
              fontWeight: 700,
              boxShadow: 'var(--shadow-warm-xs)',
              flexShrink: 0,
            }}
          >
            {initial}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2
                style={{
                  fontFamily: 'var(--font-headings)',
                  fontSize: '1.4rem',
                  color: 'var(--color-text-primary)',
                  margin: 0,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {user.name}
              </h2>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  color: 'var(--color-promo-green)',
                  background: 'var(--color-promo-bg)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid var(--color-promo-border)',
                }}
              >
                Verified Member
              </span>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--color-text-muted)', margin: '4px 0 0 0' }}>
              {user.email}
            </p>
          </div>
        </div>

        {/* User Details Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 24 }}>
          <div
            style={{
              padding: '12px 14px',
              background: 'var(--color-canvas)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-card-border)',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Birthday
            </span>
            <p style={{ margin: '4px 0 0 0', fontWeight: 700, color: 'var(--color-text-primary)', fontSize: '0.92rem' }}>
              🎂 {formatBirthday(user.birthday)}
            </p>
          </div>

          <div
            style={{
              padding: '12px 14px',
              background: 'var(--color-canvas)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-card-border)',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Member Since
            </span>
            <p style={{ margin: '4px 0 0 0', fontWeight: 700, color: 'var(--color-text-primary)', fontSize: '0.92rem' }}>
              🗓️ {formatJoined(user.created_at) || 'Today'}
            </p>
          </div>

          <div
            style={{
              gridColumn: '1 / -1',
              padding: '12px 14px',
              background: 'var(--color-canvas)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-card-border)',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Account ID (MongoDB)
            </span>
            <p style={{ margin: '4px 0 0 0', fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
              {user.id || user._id}
            </p>
          </div>
        </div>

        {/* Personal Activity Statistics */}
        <div style={{ marginBottom: 24 }}>
          <h3
            style={{
              fontFamily: 'var(--font-headings)',
              fontSize: '1rem',
              color: 'var(--color-text-primary)',
              marginBottom: 12,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>Personal Activity Statistics</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--color-primary-burgundy)', fontWeight: 700 }}>
              {totalReports} Total Reports
            </span>
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 10 }}>
            {Object.entries(FEATURE_LABELS).map(([featKey, featName]) => {
              const count = featureCounts[featKey] || 0;
              return (
                <div
                  key={featKey}
                  style={{
                    padding: '10px 12px',
                    background: 'var(--color-canvas)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--color-card-border)',
                  }}
                >
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'block' }}>
                    {featName}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-headings)',
                      fontSize: '1.2rem',
                      fontWeight: 700,
                      color: count > 0 ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                    }}
                  >
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 16, borderTop: '1px solid var(--color-card-border)' }}>
          <button
            type="button"
            onClick={onLogout}
            style={{
              background: 'transparent',
              border: '1px solid var(--color-status-error)',
              color: 'var(--color-status-error)',
              padding: '8px 16px',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            Sign Out
          </button>

          <button
            type="button"
            className="btn-burgundy-action"
            onClick={onClose}
            style={{ padding: '8px 22px', fontSize: '0.85rem' }}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
