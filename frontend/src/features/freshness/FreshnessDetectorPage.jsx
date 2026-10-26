import React, { useState } from 'react';
import { postFormData } from '../../shared/api/client';
import RecentChecksSection from '../../shared/components/RecentChecksSection';

import promoTomatoesImg from '../../assets/illustrations/tomatoes_desk.png';
import recentStrawberries from '../../assets/illustrations/recent_strawberries.png';
import recentMilk from '../../assets/illustrations/recent_milk.png';
import recentChicken from '../../assets/illustrations/recent_chicken.png';

export default function FreshnessDetectorPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [storageDuration, setStorageDuration] = useState('2');
  const [storageType, setStorageType] = useState('Refrigerator');
  const [sensoryNotes, setSensoryNotes] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [voiceNotice, setVoiceNotice] = useState(false);
  const [recentKey, setRecentKey] = useState(0);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
  };

  const handleCheckFreshness = async () => {
    if (!selectedFile) {
      alert('Please upload a food photo first to inspect freshness.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('storage_days', String(storageDuration || '2'));
      formData.append('storage_type', storageType || 'Refrigerator');
      if (sensoryNotes.trim()) {
        formData.append('sensory_notes', sensoryNotes.trim());
      }

      const data = await postFormData('/api/v1/freshness-analysis', formData);
      setResult(data);
      setRecentKey((k) => k + 1);
    } catch (err) {
      console.error('Freshness analysis error:', err);
      setError(err.message || 'Freshness inspection failed. Please verify backend connection.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="module-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div className="header-icon-badge" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"></path>
          </svg>
        </div>
        <div>
          <h1 className="page-title">Freshness Detector</h1>
          <p className="page-subtitle">
            Spot spoilage early using image analysis and added context.
          </p>
        </div>
      </div>

      <div className="workspace-grid">
        {/* Left Column: Form & Inputs */}
        <div className="workspace-main-col">
          <div className="workspace-card">
            {/* Upload Box */}
            <div
              className={`upload-drop-card full-width ${previewUrl ? 'has-preview' : ''}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              {previewUrl ? (
                <div className="preview-container">
                  <img src={previewUrl} alt="Inspection subject" className="upload-preview-img" />
                  <button
                    type="button"
                    className="preview-remove-btn"
                    onClick={handleClear}
                    aria-label="Remove image"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <label className="upload-drop-label">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                    className="visually-hidden-file-input"
                  />
                  <div className="upload-circle-icon">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <circle cx="8.5" cy="8.5" r="1.5"></circle>
                      <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                  </div>
                  <span className="upload-title">Upload Food Image</span>
                  <span className="upload-prompt">Drag & drop or click to browse</span>
                  <span className="upload-subtext">Supports JPG, PNG, WEBP (max 5MB)</span>
                </label>
              )}
            </div>

            {/* Storage Duration & Type Form Row */}
            <div className="form-two-col-row">
              <div className="form-field-group">
                <label htmlFor="freshness-storage-duration" className="form-label">
                  Storage duration
                </label>
                <select
                  id="freshness-storage-duration"
                  className="warm-select-input"
                  value={storageDuration}
                  onChange={(e) => setStorageDuration(e.target.value)}
                >
                  <option value="1">e.g. 1 day</option>
                  <option value="2">e.g. 2 days</option>
                  <option value="3">e.g. 3 days</option>
                  <option value="5">e.g. 5 days</option>
                  <option value="7">1 week</option>
                  <option value="14">2 weeks</option>
                  <option value="30">1 month+</option>
                </select>
              </div>

              <div className="form-field-group">
                <label htmlFor="freshness-storage-type" className="form-label">
                  Storage type
                </label>
                <select
                  id="freshness-storage-type"
                  className="warm-select-input"
                  value={storageType}
                  onChange={(e) => setStorageType(e.target.value)}
                >
                  <option value="Refrigerator">Refrigerator</option>
                  <option value="Room Temp">Room Temp</option>
                  <option value="Freezer">Freezer</option>
                  <option value="Pantry">Pantry</option>
                </select>
              </div>
            </div>

            {/* Additional Notes */}
            <div className="form-field-group">
              <label htmlFor="freshness-notes-input" className="form-label">
                Additional notes (optional)
              </label>
              <div className="input-with-button-wrap">
                <input
                  id="freshness-notes-input"
                  type="text"
                  className="warm-text-input"
                  placeholder="e.g. smell, texture, appearance etc."
                  value={sensoryNotes}
                  onChange={(e) => setSensoryNotes(e.target.value)}
                />
                <button
                  type="button"
                  className="mic-action-btn"
                  onClick={() => setVoiceNotice((p) => !p)}
                  title="Voice input"
                  aria-label="Voice input"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                  </svg>
                </button>
              </div>
              {voiceNotice && (
                <span className="form-inline-note">
                  🎙️ Voice capture available in supported browser environments.
                </span>
              )}
            </div>

            {/* Check Freshness Primary Action */}
            <button
              type="button"
              className="btn-burgundy-primary"
              onClick={handleCheckFreshness}
              disabled={isAnalyzing || !selectedFile}
              id="check-freshness-btn"
            >
              {isAnalyzing ? (
                <span>Inspecting Produce...</span>
              ) : (
                <>
                  <span>Check Freshness</span>
                  <span className="btn-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          {/* Live Recent Checks Section */}
          <RecentChecksSection
            feature="freshness_analysis"
            heading="Recent freshness checks"
            defaultFallbackImage={recentStrawberries}
            refreshKey={recentKey}
          />
        </div>

        {/* Right Column: Promotional Card OR Inspection Result */}
        <div className="workspace-side-col">
          {error && (
            <div className="result-alert-box error" role="alert">
              <span className="alert-icon">⚠️</span>
              <div className="alert-body">
                <strong>Inspection Issue:</strong> {error}
              </div>
              <button type="button" className="alert-retry-btn" onClick={handleCheckFreshness}>
                Retry
              </button>
            </div>
          )}

          {isAnalyzing && (
            <div className="loading-card">
              <div className="warm-spinner" />
              <h3>Analyzing visual freshness...</h3>
              <p>Multimodal vision analysis & deterministic safety verification</p>
            </div>
          )}

          {!isAnalyzing && result && (
            <div className="analysis-result-card" id="freshness-result-panel">
              <div className="result-card-header">
                <div>
                  <span className="result-tag">INSPECTION REPORT</span>
                  <h2 className="result-dish-title">{result.food_name || 'Food Subject'}</h2>
                </div>
                <div className={`safety-verdict-badge ${result.safety_status?.toLowerCase() || 'caution'}`}>
                  {result.safety_status || 'CAUTION'}
                </div>
              </div>

              <div className="freshness-meta-row">
                <div className="freshness-state-pill">
                  <span>State: <strong>{result.freshness_state || 'Marginal'}</strong></span>
                </div>
                <div className="confidence-pill high">
                  <span>Confidence: {Math.round(result.confidence || 0)}%</span>
                </div>
              </div>

              {result.signs && result.signs.length > 0 && (
                <div className="signs-box">
                  <span className="assumptions-heading">Visual Observations:</span>
                  <ul className="assumptions-list">
                    {result.signs.map((s, i) => (
                      <li key={`sign-${i}`}>• {s}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="reasoning-box">
                <span className="assumptions-heading">Safety Reasoning:</span>
                <p className="reasoning-text">{result.reasoning}</p>
              </div>

              <div className="advice-box">
                <span className="assumptions-heading">Storage Advice:</span>
                <p className="advice-text">{result.advice}</p>
              </div>

              <div className="safety-disclaimer-note">
                <span className="disclaimer-icon">ℹ️</span>
                <span>
                  {result.limitations_disclaimer ||
                    'Visual inspection cannot rule out bacterial toxins. Follow standard safety regulations.'}
                </span>
              </div>

              <div className="result-actions-row">
                <button type="button" className="btn-secondary-action" onClick={handleClear}>
                  Inspect Another Item
                </button>
                {result.report_id && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-status-success)', fontWeight: 600 }}>
                    ✓ Saved to MongoDB (ID: {result.report_id.slice(-6)})
                  </span>
                )}
                <span className="request-id-text">ID: {result.request_id?.slice(0, 8)}</span>
              </div>
            </div>
          )}

          {!isAnalyzing && !result && !error && (
            <div className="yellow-promo-card">
              <div className="promo-illustration-wrap">
                <img src={promoTomatoesImg} alt="Fresh ripe tomatoes on vine" className="promo-hero-img" />
              </div>
              <div className="promo-text-group">
                <h2 className="promo-headline">
                  <span className="headline-green">Is it</span>{' '}
                  <span className="headline-green">still fresh?</span>
                </h2>
                <p className="promo-description">
                  Upload a photo and get an AI-powered freshness analysis with safety guidance.
                </p>
                <ul className="promo-features-list">
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Detect spoilage</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Identify visual signs</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Check safety level</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Get storage recommendations</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
