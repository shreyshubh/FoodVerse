import React from 'react';

export default function FoodAnalysisResult({
  result,
  onRecalculatePortion,
  currentServingGrams,
  onReset,
}) {
  if (!result) return null;

  const {
    prediction,
    nutrition,
    health_score,
    assumptions = [],
    warnings = [],
    status,
    request_id,
  } = result;

  const confidencePct = prediction?.confidence !== null && prediction?.confidence !== undefined
    ? Math.round(prediction.confidence * 100)
    : null;

  const isLowConfidence = status === 'needs_confirmation' || status === 'inconclusive';

  const calories = nutrition?.calories_kcal !== null ? Math.round(nutrition.calories_kcal) : '—';
  const protein = nutrition?.protein_g !== null ? nutrition.protein_g.toFixed(1) : '—';
  const carbs = nutrition?.carbohydrates_g !== null ? nutrition.carbohydrates_g.toFixed(1) : '—';
  const fat = nutrition?.fat_g !== null ? nutrition.fat_g.toFixed(1) : '—';

  return (
    <div className="analysis-result-card" id="food-analysis-result-panel">
      {/* Top Header */}
      <div className="result-card-header">
        <div>
          <span className="result-tag">REAL-TIME PREDICTION</span>
          <h2 className="result-dish-title" id="food-predicted-label">
            {prediction?.label || 'Unidentified Food Item'}
          </h2>
        </div>
        {confidencePct !== null && (
          <div className={`confidence-pill ${confidencePct >= 70 ? 'high' : 'medium'}`} id="food-confidence-badge">
            <span>{confidencePct}% Match</span>
          </div>
        )}
      </div>

      {/* Uncertainty Notice if Low Confidence */}
      {isLowConfidence && (
        <div className="result-alert-box warning" id="needs-confirmation-alert">
          <span className="alert-icon">⚠️</span>
          <div>
            <strong>Model Uncertainty Notice:</strong> This prediction has lower confidence.
            Please verify before tracking dietary intake.
          </div>
        </div>
      )}

      {/* Macro Grid */}
      <div className="macros-stat-grid">
        <div className="macro-stat-box">
          <span className="macro-value calories">{calories}</span>
          <span className="macro-label">Calories (kcal)</span>
        </div>
        <div className="macro-stat-box">
          <span className="macro-value">{protein}g</span>
          <span className="macro-label">Protein</span>
        </div>
        <div className="macro-stat-box">
          <span className="macro-value">{carbs}g</span>
          <span className="macro-label">Carbs</span>
        </div>
        <div className="macro-stat-box">
          <span className="macro-value">{fat}g</span>
          <span className="macro-label">Fat</span>
        </div>
      </div>

      {/* Serving Basis & Recalculate */}
      <div className="serving-basis-box">
        <div className="serving-info-row">
          <span className="serving-basis-label">
            Basis: <strong>{nutrition?.basis === 'user_portion' ? `Portion (${nutrition?.serving_grams || currentServingGrams}g)` : 'Standard (100g)'}</strong>
          </span>
          <span className="reference-source">
            Source: {nutrition?.source || 'USDA FoodData Central'}
          </span>
        </div>

        <div className="recalculate-row">
          <label htmlFor="recalc-grams" className="recalc-label">Adjust serving:</label>
          <input
            id="recalc-grams"
            type="number"
            min="10"
            max="2000"
            step="10"
            defaultValue={currentServingGrams}
            className="recalc-input"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const val = Number(e.target.value);
                if (val > 0) onRecalculatePortion(val);
              }
            }}
          />
          <span className="serving-unit">g</span>
          <button
            type="button"
            className="btn-recalc"
            onClick={(e) => {
              const input = document.getElementById('recalc-grams');
              const val = Number(input?.value || currentServingGrams);
              if (val > 0) onRecalculatePortion(val);
            }}
          >
            Update
          </button>
        </div>
      </div>

      {/* Warnings & Assumptions */}
      {(warnings.length > 0 || assumptions.length > 0) && (
        <div className="assumptions-box">
          <span className="assumptions-heading">Notes & Assumptions:</span>
          <ul className="assumptions-list">
            {warnings.map((w, i) => (
              <li key={`warn-${i}`} className="warning-item">• {w}</li>
            ))}
            {assumptions.map((a, i) => (
              <li key={`assump-${i}`}>• {a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Footer */}
      <div className="result-actions-row">
        <button type="button" className="btn-secondary-action" onClick={onReset}>
          Analyze Another Dish
        </button>
        {result.report_id && (
          <span style={{ fontSize: '0.8rem', color: 'var(--color-status-success)', fontWeight: 600 }}>
            ✓ Saved to MongoDB (ID: {result.report_id.slice(-6)})
          </span>
        )}
        {request_id && (
          <span className="request-id-text">ID: {request_id.slice(0, 8)}</span>
        )}
      </div>
    </div>
  );
}
