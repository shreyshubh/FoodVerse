import React, { useState, useEffect } from 'react';
import heroBowlImg from '../../assets/illustrations/hero_bowl.png';
import iconFood from '../../assets/illustrations/icon_mod_food.png';
import iconFreshness from '../../assets/illustrations/icon_mod_freshness.png';
import iconHygiene from '../../assets/illustrations/icon_mod_hygiene.png';
import iconKitchen from '../../assets/illustrations/icon_mod_kitchen.png';
import iconPlanner from '../../assets/illustrations/icon_mod_planner.png';
import { fetchHistorySummary } from '../history/historyApi';
import { BASE_URL } from '../../shared/api/client';
import ReportDetailModal from '../../shared/components/ReportDetailModal';

const MODULES = [
  {
    id: 'food_recognition',
    title: 'Food Recognition',
    subtitle: 'Name any dish and see its nutrition.',
    icon: iconFood,
    highlight: true,
  },
  {
    id: 'freshness',
    title: 'Freshness Detector',
    subtitle: 'Check if your food is safe to eat.',
    icon: iconFreshness,
    highlight: false,
  },
  {
    id: 'hygiene',
    title: 'Hygiene Monitor',
    subtitle: 'Ensure kitchen safety and hygiene.',
    icon: iconHygiene,
    highlight: false,
  },
  {
    id: 'smart_kitchen',
    title: 'Smart Kitchen',
    subtitle: 'Get recipes from your ingredients or photos.',
    icon: iconKitchen,
    highlight: false,
  },
  {
    id: 'meal_planner',
    title: 'Meal Planner',
    subtitle: 'Plan your week around your health goals.',
    icon: iconPlanner,
    highlight: false,
  },
];

export default function OverviewPage({ onSelectTab }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchHistorySummary();
      setSummary(data);
    } catch (err) {
      setError(err.message || 'Unable to load activity summary.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const formatDate = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="overview-container">
      {/* Pale-yellow Hero Welcome Banner */}
      <section className="overview-welcome-banner" aria-label="Welcome Banner">
        <div className="banner-left-content">
          <span className="banner-eyebrow">WELCOME TO FOODVERSE</span>
          <h1 className="banner-headline">
            <span className="headline-green">Good food,</span>
            <br />
            <span className="headline-burgundy">brighter days.</span>
          </h1>
          <p className="banner-description">
            AI tools that help you choose better, cook safer and keep your kitchen clean.
          </p>
          <button
            type="button"
            className="btn-burgundy-action"
            onClick={() => onSelectTab('food_recognition')}
            id="overview-explore-btn"
          >
            <span>Explore all modules</span>
            <span className="btn-arrow" aria-hidden="true">→</span>
          </button>
        </div>

        <div className="banner-right-art">
          <div className="script-slogan" aria-hidden="true">
            Better food,
            <br />
            brighter days.
          </div>
          <div className="hero-bowl-wrap">
            <img
              src={heroBowlImg}
              alt="Delicious warm rice and culinary dish with herbs"
              className="hero-bowl-img"
            />
          </div>
        </div>
      </section>

      {/* Explore the Modules Section */}
      <section className="overview-modules-section" aria-label="Explore Modules">
        <div className="section-title-row">
          <h2 className="modules-heading">Explore the modules</h2>
          <span className="modules-subhead">Five AI tools for your food journey.</span>
        </div>

        <div className="modules-cards-grid">
          {MODULES.map((mod) => (
            <div
              key={mod.id}
              className={`module-overview-card ${mod.highlight ? 'card-highlighted' : ''}`}
              onClick={() => onSelectTab(mod.id)}
              role="button"
              tabIndex={0}
              id={`overview-card-${mod.id}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectTab(mod.id);
                }
              }}
            >
              <div className="card-illustration-box">
                <img src={mod.icon} alt="" className="mod-card-icon" />
              </div>
              <div className="card-content-wrap">
                <h3 className="mod-card-title">{mod.title}</h3>
                <p className="mod-card-desc">{mod.subtitle}</p>
              </div>
              <div className="card-arrow-circle" aria-label={`Open ${mod.title}`}>
                <span>→</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Real Dashboard Activity & History Section */}
      <section className="overview-activity-section" style={{ marginTop: 40 }} aria-label="Recent Session Activity">
        <div className="section-title-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 16 }}>
          <div>
            <h2 className="modules-heading" style={{ fontSize: '1.4rem' }}>Recent Activity</h2>
            <span className="modules-subhead">Real reports saved to your session</span>
          </div>
          <button
            type="button"
            onClick={() => onSelectTab('history')}
            style={{
              color: 'var(--color-primary-burgundy)',
              fontWeight: 700,
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <span>View All History</span>
            <span>→</span>
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div style={{ padding: '28px', background: 'var(--color-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-card-border)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Loading recent analyses...
          </div>
        )}

        {/* Error & Retry State */}
        {error && !loading && (
          <div style={{ padding: '20px', background: 'var(--color-status-error-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-status-error)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--color-status-error)', fontSize: '0.9rem' }}>{error}</span>
            <button
              type="button"
              className="btn-burgundy-action"
              onClick={loadSummary}
              style={{ padding: '6px 14px', fontSize: '0.82rem' }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && (!summary || summary.total_reports === 0) && (
          <div style={{ padding: '32px 24px', background: 'var(--color-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-card-border)', textAlign: 'center' }}>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.92rem', marginBottom: 14 }}>
              No analyses recorded in this session yet. Run any of the five AI modules above to save reports and track history.
            </p>
            <button
              type="button"
              className="btn-burgundy-action"
              onClick={() => onSelectTab('food_recognition')}
              style={{ padding: '8px 20px', fontSize: '0.85rem' }}
            >
              Try Food Recognition →
            </button>
          </div>
        )}

        {/* Real Summary Content */}
        {!loading && !error && summary && summary.total_reports > 0 && (
          <div>
            {/* Real Counts Bar */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
              <div style={{ padding: '10px 16px', background: 'var(--color-promo-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-promo-border)' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-promo-burgundy)', fontWeight: 700, textTransform: 'uppercase' }}>Total Reports</span>
                <p style={{ fontFamily: 'var(--font-headings)', fontSize: '1.4rem', fontWeight: 700, color: 'var(--color-promo-green)', margin: 0 }}>
                  {summary.total_reports}
                </p>
              </div>

              {Object.entries(summary.counts_by_feature || {}).map(([feat, cnt]) => {
                if (cnt === 0) return null;
                const label = feat.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                return (
                  <div key={feat} style={{ padding: '10px 16px', background: 'var(--color-card)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-card-border)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>{label}</span>
                    <p style={{ fontFamily: 'var(--font-headings)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                      {cnt}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Recent 5 Real Reports List */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
              {(summary.recent_reports || []).map((rep) => (
                <div
                  key={rep.id}
                  onClick={() => setSelectedReport(rep)}
                  title="Click to view complete report details"
                  style={{
                    background: 'var(--color-card)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--color-card-border)',
                    padding: '14px 16px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    boxShadow: 'var(--shadow-warm-xs)',
                    transition: 'transform var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
                  onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-primary-burgundy)', textTransform: 'uppercase' }}>
                        {rep.badge?.replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                        {formatDate(rep.created_at)}
                      </span>
                    </div>

                    <h4 style={{ fontFamily: 'var(--font-headings)', fontSize: '1rem', color: 'var(--color-text-primary)', marginBottom: 2 }}>
                      {rep.title}
                    </h4>
                    {rep.subtitle && (
                      <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.82rem' }}>
                        {rep.subtitle}
                      </p>
                    )}
                  </div>

                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 8 }}>
                    Report ID: {rep.id?.slice(-6)} • Open →
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Interactive Report Details Modal */}
      {selectedReport && (
        <ReportDetailModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
}
