/**
 * FoodVerse AI — History & Report Archive View.
 *
 * Implements owner-scoped report browsing, feature filtering,
 * full detail inspection, and deletion confirmation while preserving
 * the approved warm illustrated design system.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { fetchHistoryReports, deleteHistoryReport } from './historyApi';
import { BASE_URL } from '../../shared/api/client';

const FILTER_TABS = [
  { id: '', label: 'All Reports' },
  { id: 'food_recognition', label: 'Food Recognition' },
  { id: 'freshness_analysis', label: 'Freshness' },
  { id: 'hygiene_analysis', label: 'Hygiene' },
  { id: 'recipe_generation', label: 'Recipes' },
  { id: 'meal_plan', label: 'Meal Plans' },
];

const FEATURE_NAMES = {
  food_recognition: 'Food Recognition',
  freshness_analysis: 'Freshness Detector',
  hygiene_analysis: 'Hygiene Monitor',
  recipe_generation: 'Smart Kitchen',
  meal_plan: 'Meal Planner',
};

export default function HistoryPage({ onSelectTab }) {
  const [activeFilter, setActiveFilter] = useState('');
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedReport, setSelectedReport] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const loadReports = useCallback(async (filter, cursor = null, append = false) => {
    try {
      if (!append) setLoading(true);
      setError(null);
      const res = await fetchHistoryReports({
        feature: filter || null,
        cursor,
        limit: 8,
      });

      if (append) {
        setReports((prev) => [...prev, ...(res.items || [])]);
      } else {
        setReports(res.items || []);
      }
      setNextCursor(res.next_cursor);
      setHasMore(Boolean(res.has_more));
      setTotalCount(res.total || 0);
    } catch (err) {
      setError(err.message || 'Failed to load report history.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports(activeFilter);
  }, [activeFilter, loadReports]);

  const handleFilterChange = (filterId) => {
    setActiveFilter(filterId);
    setReports([]);
    setNextCursor(null);
  };

  const handleLoadMore = () => {
    if (nextCursor && !loading) {
      loadReports(activeFilter, nextCursor, true);
    }
  };

  const handleDelete = async (reportId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this report and any associated media?')) {
      return;
    }
    try {
      setDeletingId(reportId);
      await deleteHistoryReport(reportId);
      setReports((prev) => prev.filter((r) => r.id !== reportId && r._id !== reportId));
      setTotalCount((prev) => Math.max(0, prev - 1));
      if (selectedReport && (selectedReport.id === reportId || selectedReport._id === reportId)) {
        setSelectedReport(null);
      }
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="history-page-container" style={{ padding: '24px 32px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ marginBottom: 28 }}>
        <span className="banner-eyebrow" style={{ fontSize: '0.8rem', letterSpacing: '0.08em', color: 'var(--color-primary-burgundy)', fontWeight: 700 }}>
          SESSION ARCHIVE
        </span>
        <h1 style={{ fontFamily: 'var(--font-headings)', fontSize: '2rem', color: 'var(--color-text-primary)', marginTop: 4 }}>
          Analysis & Report History
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.95rem', marginTop: 4 }}>
          Review and inspect all past analyses, recipes, and audits stored in MongoDB. ({totalCount} {totalCount === 1 ? 'record' : 'records'})
        </p>
      </div>

      {/* Feature Filter Tabs */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
        {FILTER_TABS.map((tab) => {
          const isActive = activeFilter === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleFilterChange(tab.id)}
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.88rem',
                fontWeight: 600,
                border: '1px solid',
                borderColor: isActive ? 'var(--color-primary-burgundy)' : 'var(--color-card-border)',
                background: isActive ? 'var(--color-primary-burgundy)' : 'var(--color-card)',
                color: isActive ? '#FFFFFF' : 'var(--color-text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Loading state */}
      {loading && reports.length === 0 && (
        <div style={{ padding: '60px 20px', textAlign: 'center', background: 'var(--color-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-card-border)' }}>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>Loading report history from MongoDB...</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div style={{ padding: '30px', textAlign: 'center', background: 'var(--color-status-error-bg)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-status-error)', marginBottom: 20 }}>
          <p style={{ color: 'var(--color-status-error)', fontWeight: 600, marginBottom: 12 }}>{error}</p>
          <button
            type="button"
            className="btn-burgundy-action"
            onClick={() => loadReports(activeFilter)}
            style={{ padding: '8px 20px', fontSize: '0.88rem' }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && reports.length === 0 && (
        <div style={{ padding: '60px 24px', textAlign: 'center', background: 'var(--color-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-card-border)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>📋</div>
          <h3 style={{ fontFamily: 'var(--font-headings)', fontSize: '1.25rem', color: 'var(--color-text-primary)', marginBottom: 6 }}>
            No reports recorded yet
          </h3>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.92rem', maxWidth: 440, margin: '0 auto 20px auto' }}>
            Run a Food Recognition scan, Freshness check, Kitchen Hygiene audit, or generate a Recipe to see it saved here.
          </p>
          <button
            type="button"
            className="btn-burgundy-action"
            onClick={() => onSelectTab && onSelectTab('food_recognition')}
            style={{ padding: '10px 24px', fontSize: '0.9rem' }}
          >
            Start an Analysis →
          </button>
        </div>
      )}

      {/* Reports Grid */}
      {reports.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {reports.map((report) => {
            const feature = report.feature;
            const result = report.result || {};
            const mediaList = report.media || [];
            const hasMedia = mediaList.length > 0 && mediaList[0].file_id;
            const mediaUrl = hasMedia ? `${BASE_URL}/api/v1/media/${mediaList[0].file_id}` : null;

            let title = 'Report';
            let subtitle = '';
            if (feature === 'food_recognition') {
              title = result.predicted_food || result.prediction?.label || 'Food Recognition';
              subtitle = result.confidence ? `${(result.confidence * 100).toFixed(0)}% confidence` : '';
            } else if (feature === 'freshness_analysis') {
              title = result.food_name || 'Freshness Inspection';
              subtitle = `${result.freshness_state || ''} • ${result.safety_status || ''}`;
            } else if (feature === 'hygiene_analysis') {
              title = 'Hygiene Inspection';
              subtitle = `Compliance: ${result.risk_level || result.compliance_status || 'Audited'}`;
            } else if (feature === 'recipe_generation') {
              title = result.title || 'Smart Recipe';
              subtitle = `${result.prep_time_minutes ? result.prep_time_minutes + result.cook_time_minutes : ''} mins • ${result.difficulty || ''}`;
            } else if (feature === 'meal_plan') {
              title = 'Personalized Meal Plan';
              subtitle = `${result.today_plan?.calories_total || result.calculated_targets?.target_calories || ''} kcal`;
            }

            return (
              <div
                key={report.id || report._id}
                onClick={() => setSelectedReport(report)}
                style={{
                  background: 'var(--color-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-card-border)',
                  padding: 18,
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  boxShadow: 'var(--shadow-warm-xs)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-warm-md)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = 'var(--shadow-warm-xs)';
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-full)',
                      background: 'var(--color-promo-bg)',
                      color: 'var(--color-promo-burgundy)',
                    }}>
                      {FEATURE_NAMES[feature] || feature}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      {formatDate(report.created_at)}
                    </span>
                  </div>

                  {hasMedia && (
                    <div style={{ width: '100%', height: 130, borderRadius: 'var(--radius-sm)', overflow: 'hidden', marginBottom: 12, background: '#eee' }}>
                      <img
                        src={mediaUrl}
                        alt=""
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                      />
                    </div>
                  )}

                  <h3 style={{ fontFamily: 'var(--font-headings)', fontSize: '1.1rem', color: 'var(--color-text-primary)', marginBottom: 4 }}>
                    {title}
                  </h3>
                  {subtitle && (
                    <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.85rem', marginBottom: 12 }}>
                      {subtitle}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--color-card-border)' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-primary-burgundy)', fontWeight: 600 }}>
                    Inspect Details →
                  </span>
                  <button
                    type="button"
                    onClick={(e) => handleDelete(report.id || report._id, e)}
                    disabled={deletingId === (report.id || report._id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--color-status-error)',
                      fontSize: '0.8rem',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      opacity: deletingId === (report.id || report._id) ? 0.5 : 1,
                    }}
                    aria-label="Delete report"
                  >
                    {deletingId === (report.id || report._id) ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination Load More */}
      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 32 }}>
          <button
            type="button"
            className="btn-burgundy-action"
            onClick={handleLoadMore}
            disabled={loading}
            style={{ padding: '10px 28px', fontSize: '0.9rem' }}
          >
            {loading ? 'Loading...' : 'Load Older Reports'}
          </button>
        </div>
      )}

      {/* Report Detail Modal */}
      {selectedReport && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(26, 22, 18, 0.65)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20,
          }}
          onClick={() => setSelectedReport(null)}
        >
          <div
            style={{
              background: 'var(--color-card)',
              borderRadius: 'var(--radius-xl)',
              maxWidth: 680,
              width: '100%',
              maxHeight: '85vh',
              overflowY: 'auto',
              padding: 28,
              boxShadow: 'var(--shadow-warm-lg)',
              border: '1px solid var(--color-card-border)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--color-promo-bg)',
                  color: 'var(--color-promo-burgundy)',
                }}>
                  {FEATURE_NAMES[selectedReport.feature] || selectedReport.feature}
                </span>
                <h2 style={{ fontFamily: 'var(--font-headings)', fontSize: '1.4rem', color: 'var(--color-text-primary)', marginTop: 8 }}>
                  Report Details
                </h2>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                  ID: {selectedReport.id || selectedReport._id} • {formatDate(selectedReport.created_at)}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                style={{
                  fontSize: '1.25rem',
                  color: 'var(--color-text-muted)',
                  cursor: 'pointer',
                  padding: '4px 8px',
                }}
              >
                ✕
              </button>
            </div>

            {/* Media thumbnail if present */}
            {selectedReport.media && selectedReport.media.length > 0 && selectedReport.media[0].file_id && (
              <div style={{ width: '100%', maxHeight: 240, overflow: 'hidden', borderRadius: 'var(--radius-md)', marginBottom: 20, background: '#eee' }}>
                <img
                  src={`${BASE_URL}/api/v1/media/${selectedReport.media[0].file_id}`}
                  alt="Saved Upload"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            )}

            {/* Feature specific structured view */}
            <div style={{ fontSize: '0.92rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              {selectedReport.feature === 'food_recognition' && (
                <div>
                  <h4 style={{ color: 'var(--color-text-primary)', marginBottom: 6 }}>
                    Predicted Dish: <span style={{ color: 'var(--color-primary-burgundy)' }}>{selectedReport.result?.predicted_food || selectedReport.result?.prediction?.label}</span>
                  </h4>
                  <p>Confidence: {((selectedReport.result?.confidence || 0) * 100).toFixed(1)}%</p>
                  {selectedReport.result?.nutrition && (
                    <div style={{ marginTop: 14, padding: 12, background: 'var(--color-canvas)', borderRadius: 'var(--radius-sm)' }}>
                      <strong>Nutrition Breakdown:</strong>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 8, textAlign: 'center' }}>
                        <div><small>Calories</small><br /><strong>{selectedReport.result.nutrition.calories_kcal || 0} kcal</strong></div>
                        <div><small>Protein</small><br /><strong>{selectedReport.result.nutrition.protein_g || 0}g</strong></div>
                        <div><small>Carbs</small><br /><strong>{selectedReport.result.nutrition.carbohydrates_g || 0}g</strong></div>
                        <div><small>Fat</small><br /><strong>{selectedReport.result.nutrition.fat_g || 0}g</strong></div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {selectedReport.feature === 'freshness_analysis' && (
                <div>
                  <h4 style={{ color: 'var(--color-text-primary)' }}>{selectedReport.result?.food_name}</h4>
                  <p><strong>State:</strong> {selectedReport.result?.freshness_state} • <strong>Safety Status:</strong> {selectedReport.result?.safety_status}</p>
                  <p style={{ marginTop: 8 }}><strong>Visual Reasoning:</strong> {selectedReport.result?.reasoning}</p>
                  <p style={{ marginTop: 8 }}><strong>Consumer Advice:</strong> {selectedReport.result?.advice}</p>
                  <div style={{ marginTop: 14, padding: 10, background: 'var(--color-promo-bg)', borderRadius: 'var(--radius-sm)', fontSize: '0.82rem', color: 'var(--color-promo-burgundy)' }}>
                    ⚠️ {selectedReport.result?.limitations_disclaimer || 'Visual inspection cannot rule out microbiological toxins.'}
                  </div>
                </div>
              )}

              {selectedReport.feature === 'hygiene_analysis' && (
                <div>
                  <p><strong>Compliance Status:</strong> {selectedReport.result?.risk_level || selectedReport.result?.compliance_status}</p>
                  <p><strong>Score:</strong> {selectedReport.result?.overall_score ?? 'Not assessable'} / 100</p>
                  <p><strong>Persons Observed:</strong> {selectedReport.result?.persons_observed || 0}</p>
                  <p style={{ marginTop: 10 }}><strong>Audit Summary:</strong></p>
                  <p>{selectedReport.result?.ai_summary || selectedReport.result?.audit_report_text}</p>
                </div>
              )}

              {selectedReport.feature === 'recipe_generation' && (
                <div>
                  <h4 style={{ color: 'var(--color-primary-burgundy)', fontSize: '1.2rem', marginBottom: 6 }}>
                    {selectedReport.result?.title}
                  </h4>
                  <p style={{ marginBottom: 12 }}>{selectedReport.result?.summary}</p>
                  <strong>Ingredients:</strong>
                  <ul style={{ paddingLeft: 20, margin: '8px 0 16px 0' }}>
                    {(selectedReport.result?.ingredients || []).map((ing, i) => (
                      <li key={i}>{ing}</li>
                    ))}
                  </ul>
                  <strong>Preparation Steps:</strong>
                  <ol style={{ paddingLeft: 20, marginTop: 8 }}>
                    {(selectedReport.result?.steps || []).map((step, i) => (
                      <li key={i} style={{ marginBottom: 6 }}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {selectedReport.feature === 'meal_plan' && (
                <div>
                  <p><strong>Calorie Target:</strong> {selectedReport.result?.calculated_targets?.target_calories || 0} kcal</p>
                  <p><strong>Coach Notes:</strong> {selectedReport.result?.coach_notes}</p>
                  <div style={{ marginTop: 14 }}>
                    <strong>Today's Menu:</strong>
                    <div style={{ marginTop: 8 }}>
                      {(selectedReport.result?.today_plan?.meals || []).map((m, i) => (
                        <div key={i} style={{ padding: '8px 12px', background: 'var(--color-canvas)', borderRadius: 'var(--radius-sm)', marginBottom: 6 }}>
                          <span style={{ fontWeight: 700, color: 'var(--color-primary-burgundy)', fontSize: '0.8rem' }}>[{m.meal_type}]</span> {m.dish_name} — {m.calories_kcal} kcal
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Close Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--color-card-border)' }}>
              <button
                type="button"
                className="btn-burgundy-action"
                onClick={() => setSelectedReport(null)}
                style={{ padding: '8px 22px', fontSize: '0.88rem' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
