import React from 'react';
import { BASE_URL } from '../api/client';

const FEATURE_NAMES = {
  food_recognition: 'Food Recognition',
  freshness_analysis: 'Freshness Detector',
  hygiene_analysis: 'Hygiene Monitor',
  recipe_generation: 'Smart Kitchen',
  meal_plan: 'Meal Planner',
};

export default function ReportDetailModal({ report, onClose }) {
  if (!report) return null;

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
      onClick={onClose}
      role="dialog"
      aria-modal="true"
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
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-promo-bg)',
                color: 'var(--color-promo-burgundy)',
              }}
            >
              {FEATURE_NAMES[report.feature] || report.feature}
            </span>
            <h2 style={{ fontFamily: 'var(--font-headings)', fontSize: '1.4rem', color: 'var(--color-text-primary)', marginTop: 8 }}>
              Report Details
            </h2>
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
              ID: {report.id || report._id} • {formatDate(report.created_at)}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            style={{
              fontSize: '1.25rem',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: '4px 8px',
              background: 'transparent',
              border: 'none',
            }}
          >
            ✕
          </button>
        </div>

        {/* Media thumbnail if present */}
        {report.media && report.media.length > 0 && report.media[0].file_id && (
          <div style={{ width: '100%', maxHeight: 240, overflow: 'hidden', borderRadius: 'var(--radius-md)', marginBottom: 20, background: '#eee' }}>
            <img
              src={`${BASE_URL}/api/v1/media/${report.media[0].file_id}`}
              alt="Saved Report Media"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
        )}

        {/* Feature specific structured view */}
        <div style={{ fontSize: '0.92rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          {report.feature === 'food_recognition' && (
            <div>
              <h4 style={{ color: 'var(--color-text-primary)', marginBottom: 6 }}>
                Predicted Dish:{' '}
                <span style={{ color: 'var(--color-primary-burgundy)' }}>
                  {report.result?.predicted_food || report.result?.prediction?.label || 'Analyzed Item'}
                </span>
              </h4>
              <p>Confidence: {((report.result?.confidence || 0) * 100).toFixed(1)}%</p>
              {report.result?.nutrition && (
                <div style={{ marginTop: 14, padding: 12, background: 'var(--color-canvas)', borderRadius: 'var(--radius-sm)' }}>
                  <strong>Nutrition Breakdown:</strong>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 8, textAlign: 'center' }}>
                    <div><small>Calories</small><br /><strong>{report.result.nutrition.calories_kcal || 0} kcal</strong></div>
                    <div><small>Protein</small><br /><strong>{report.result.nutrition.protein_g || 0}g</strong></div>
                    <div><small>Carbs</small><br /><strong>{report.result.nutrition.carbohydrates_g || 0}g</strong></div>
                    <div><small>Fat</small><br /><strong>{report.result.nutrition.fat_g || 0}g</strong></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {report.feature === 'freshness_analysis' && (
            <div>
              <h4 style={{ color: 'var(--color-text-primary)' }}>{report.result?.food_name || 'Inspected Food'}</h4>
              <p><strong>State:</strong> {report.result?.freshness_state} • <strong>Safety Status:</strong> {report.result?.safety_status}</p>
              <p style={{ marginTop: 8 }}><strong>Visual Reasoning:</strong> {report.result?.reasoning}</p>
              <p style={{ marginTop: 8 }}><strong>Consumer Advice:</strong> {report.result?.advice}</p>
              <div style={{ marginTop: 14, padding: 10, background: 'var(--color-promo-bg)', borderRadius: 'var(--radius-sm)', fontSize: '0.82rem', color: 'var(--color-promo-burgundy)' }}>
                ⚠️ {report.result?.limitations_disclaimer || 'Visual inspection cannot rule out microbiological toxins.'}
              </div>
            </div>
          )}

          {report.feature === 'hygiene_analysis' && (
            <div>
              <p><strong>Compliance Status:</strong> {report.result?.risk_level || report.result?.compliance_status}</p>
              <p><strong>Score:</strong> {report.result?.overall_score ?? 'Not assessable'} / 100</p>
              <p><strong>Persons Observed:</strong> {report.result?.persons_observed || 0}</p>
              <p style={{ marginTop: 10 }}><strong>Audit Summary:</strong></p>
              <p>{report.result?.ai_summary || report.result?.audit_report_text}</p>
            </div>
          )}

          {report.feature === 'recipe_generation' && (
            <div>
              <h4 style={{ color: 'var(--color-primary-burgundy)', fontSize: '1.2rem', marginBottom: 6 }}>
                {report.result?.title}
              </h4>
              <p style={{ marginBottom: 12 }}>{report.result?.summary}</p>
              <strong>Ingredients:</strong>
              <ul style={{ paddingLeft: 20, margin: '8px 0 16px 0' }}>
                {(report.result?.ingredients || []).map((ing, i) => (
                  <li key={i}>{ing}</li>
                ))}
              </ul>
              <strong>Preparation Steps:</strong>
              <ol style={{ paddingLeft: 20, marginTop: 8 }}>
                {(report.result?.steps || []).map((step, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {report.feature === 'meal_plan' && (
            <div>
              <p><strong>Calorie Target:</strong> {report.result?.calculated_targets?.target_calories || 0} kcal</p>
              <p><strong>Coach Notes:</strong> {report.result?.coach_notes}</p>
              <div style={{ marginTop: 14 }}>
                <strong>Today's Menu:</strong>
                <div style={{ marginTop: 8 }}>
                  {(report.result?.today_plan?.meals || []).map((m, i) => (
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
            onClick={onClose}
            style={{ padding: '8px 22px', fontSize: '0.88rem' }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
