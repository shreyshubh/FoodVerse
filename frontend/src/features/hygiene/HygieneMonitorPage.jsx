import React, { useState } from 'react';
import { postFormData } from '../../shared/api/client';
import RecentChecksSection from '../../shared/components/RecentChecksSection';

import promoChefImg from '../../assets/illustrations/chef_clean.png';
import recentCam1 from '../../assets/illustrations/recent_cam1.png';
import recentCam2 from '../../assets/illustrations/recent_cam2.png';
import recentCam3 from '../../assets/illustrations/recent_cam3.png';

const COMPLIANCE_RULES = [
  { id: 'gloves', label: 'Gloves', checked: true },
  { id: 'hairnet', label: 'Hairnet', checked: true },
  { id: 'apron', label: 'Apron', checked: true },
  { id: 'clean_surfaces', label: 'Clean Surfaces', checked: true },
  { id: 'mask', label: 'Mask', checked: false },
  { id: 'proper_storage', label: 'Proper Storage', checked: false },
];

export default function HygieneMonitorPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isVideo, setIsVideo] = useState(false);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'camera'
  const [selectedRules, setSelectedRules] = useState(
    COMPLIANCE_RULES.reduce((acc, r) => ({ ...acc, [r.id]: r.checked }), {})
  );
  const [isInspecting, setIsInspecting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [recentKey, setRecentKey] = useState(0);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setIsVideo(file.type.includes('video') || /\.(mp4|avi|mov|webm)$/i.test(file.name));
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
      setIsVideo(file.type.includes('video') || /\.(mp4|avi|mov|webm)$/i.test(file.name));
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

  const handleToggleRule = (ruleId) => {
    setSelectedRules((prev) => ({ ...prev, [ruleId]: !prev[ruleId] }));
  };

  const handleInspect = async () => {
    if (!selectedFile) {
      alert('Please upload CCTV footage or a kitchen photo first.');
      return;
    }

    setIsInspecting(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('media', selectedFile);
      formData.append('station_id', 'Prep Station 01');

      const data = await postFormData('/api/v1/hygiene-analysis', formData);
      setResult(data);
      setRecentKey((k) => k + 1);
    } catch (err) {
      console.error('Hygiene inspection error:', err);
      setError(err.message || 'Inspection failed. Please ensure the backend detector is active.');
    } finally {
      setIsInspecting(false);
    }
  };

  const handleDownloadReport = () => {
    if (!result) return;
    const reportText =
      result.audit_report_text ||
      `FOODVERSE AI — HYGIENE & SAFETY AUDIT REPORT\nStation: Prep Station 01\nScore: ${result.overall_score ?? 'N/A'}/100\nRisk: ${result.risk_level}\nSummary: ${result.ai_summary}`;
    const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Hygiene_Safety_Report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="module-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div className="header-icon-badge" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            <path d="m9 12 2 2 4-4"></path>
          </svg>
        </div>
        <div>
          <h1 className="page-title">Hygiene & Safety Monitor</h1>
          <p className="page-subtitle">
            AI-powered surveillance for kitchen compliance and safety risks.
          </p>
        </div>
      </div>

      <div className="workspace-grid">
        {/* Left Column: Form & Inputs */}
        <div className="workspace-main-col">
          <div className="workspace-card">
            {/* Mode Tabs */}
            <div className="inspection-mode-tabs">
              <button
                type="button"
                className={`mode-tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
                onClick={() => setActiveTab('upload')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7"></polygon>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
                <span>Upload Video</span>
              </button>
              <button
                type="button"
                className={`mode-tab-btn ${activeTab === 'camera' ? 'active' : ''}`}
                onClick={() => setActiveTab('camera')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
                <span>Live Camera (Coming Soon)</span>
              </button>
            </div>

            {activeTab === 'camera' ? (
              <div className="coming-soon-box">
                <p>
                  📹 Real-time RTSP stream surveillance integration is in progress.
                  Please switch to <strong>Upload Video</strong> to run local YOLOv8 PPE detection.
                </p>
              </div>
            ) : (
              <>
                {/* Upload Zone */}
                <div
                  className={`upload-drop-card full-width ${previewUrl ? 'has-preview' : ''}`}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                >
                  {previewUrl ? (
                    <div className="preview-container">
                      {isVideo ? (
                        <video src={previewUrl} controls className="upload-preview-media" />
                      ) : (
                        <img src={previewUrl} alt="Kitchen preview" className="upload-preview-img" />
                      )}
                      <button
                        type="button"
                        className="preview-remove-btn"
                        onClick={handleClear}
                        aria-label="Remove media"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <label className="upload-drop-label">
                      <input
                        type="file"
                        accept="video/mp4,video/avi,video/quicktime,video/webm,image/jpeg,image/png"
                        onChange={handleFileChange}
                        className="visually-hidden-file-input"
                      />
                      <div className="upload-circle-icon">
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                          <polygon points="23 7 16 12 23 17 23 7"></polygon>
                          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                        </svg>
                      </div>
                      <span className="upload-title">Upload Kitchen Video</span>
                      <span className="upload-prompt">Drag & drop or click to browse</span>
                      <span className="upload-subtext">Supports MP4, MOV, AVI, JPG (max 100MB)</span>
                    </label>
                  )}
                </div>

                {/* Compliance Rules Pills */}
                <div className="compliance-rules-section">
                  <label className="form-label">Compliance rules</label>
                  <div className="rules-pills-wrap">
                    {COMPLIANCE_RULES.map((rule) => {
                      const isChecked = !!selectedRules[rule.id];
                      return (
                        <button
                          key={rule.id}
                          type="button"
                          className={`rule-pill-btn ${isChecked ? 'active' : ''}`}
                          onClick={() => handleToggleRule(rule.id)}
                        >
                          <span className="rule-checkbox-dot">{isChecked ? '✓' : ''}</span>
                          <span>{rule.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Inspect Action */}
                <button
                  type="button"
                  className="btn-burgundy-primary"
                  onClick={handleInspect}
                  disabled={isInspecting || !selectedFile}
                  id="inspect-hygiene-btn"
                >
                  {isInspecting ? (
                    <span>Running Dual YOLO Inspection...</span>
                  ) : (
                    <>
                      <span>Inspect Video</span>
                      <span className="btn-arrow" aria-hidden="true">→</span>
                    </>
                  )}
                </button>
              </>
            )}
          </div>

          {/* Live Recent Inspections */}
          <RecentChecksSection
            feature="hygiene_analysis"
            heading="Recent safety checks"
            defaultFallbackImage={recentCam1}
            refreshKey={recentKey}
          />
        </div>

        {/* Right Column: Promotional Card OR Inspection Findings */}
        <div className="workspace-side-col">
          {error && (
            <div className="result-alert-box error" role="alert">
              <span className="alert-icon">⚠️</span>
              <div className="alert-body">
                <strong>Inspection Issue:</strong> {error}
              </div>
              <button type="button" className="alert-retry-btn" onClick={handleInspect}>
                Retry
              </button>
            </div>
          )}

          {isInspecting && (
            <div className="loading-card">
              <div className="warm-spinner" />
              <h3>Scanning frames for PPE & safety risks...</h3>
              <p>Dual YOLOv8 (Personnel + PPE) inference via OpenCV frame stream</p>
            </div>
          )}

          {!isInspecting && result && (
            <div className="analysis-result-card" id="hygiene-result-panel">
              <div className="result-card-header">
                <div>
                  <span className="result-tag">SAFETY AUDIT REPORT</span>
                  <h2 className="result-dish-title">Station 01 Inspection</h2>
                </div>
                <div className={`risk-badge ${result.risk_level?.toLowerCase().replace(/\s+/g, '-')}`}>
                  {result.risk_level || 'ASSESSED'}
                </div>
              </div>

              {/* Compliance Score */}
              <div className="hygiene-score-container">
                <div className="score-circle-display">
                  <span className="score-num">{result.overall_score !== null ? result.overall_score : '—'}</span>
                  <span className="score-denom">/ 100</span>
                </div>
                <div className="score-details-meta">
                  <span className="score-title">
                    {result.overall_score !== null ? 'Overall Compliance Score' : 'Personnel Not Assessable'}
                  </span>
                  <span className="score-stats">
                    {result.persons_observed} persons detected • {result.frames_analyzed} frames analyzed
                  </span>
                </div>
              </div>

              {/* Alerts List */}
              {result.alerts && result.alerts.length > 0 ? (
                <div className="violations-container">
                  <span className="assumptions-heading">Detected Violations:</span>
                  <div className="violations-list">
                    {result.alerts.map((alert, idx) => (
                      <div key={idx} className={`violation-item-row ${alert.severity?.toLowerCase()}`}>
                        <div className="violation-main-info">
                          <span className="violation-badge">{alert.severity}</span>
                          <span className="violation-label">{alert.label}</span>
                        </div>
                        <p className="violation-desc">{alert.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="no-violations-box">
                  <span>✓ No active safety violations detected in sampled footage.</span>
                </div>
              )}

              {/* AI Summary */}
              {result.ai_summary && (
                <div className="reasoning-box">
                  <span className="assumptions-heading">Audit Summary:</span>
                  <p className="reasoning-text">{result.ai_summary}</p>
                </div>
              )}

              {/* Actions Row */}
              <div className="result-actions-row">
                <button type="button" className="btn-burgundy-action" onClick={handleDownloadReport}>
                  Download Report
                </button>
                <button type="button" className="btn-secondary-action" onClick={handleClear}>
                  Inspect Another Media
                </button>
                {result.report_id && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-status-success)', fontWeight: 600 }}>
                    ✓ Saved to MongoDB (ID: {result.report_id.slice(-6)})
                  </span>
                )}
              </div>
            </div>
          )}

          {!isInspecting && !result && !error && (
            <div className="yellow-promo-card">
              <div className="promo-illustration-wrap">
                <img src={promoChefImg} alt="Chef in kitchen illustration" className="promo-hero-img" />
              </div>
              <div className="promo-text-group">
                <h2 className="promo-headline">
                  <span className="headline-green">Cleaner</span>
                  <br />
                  <span className="headline-green">kitchens,</span>
                  <br />
                  <span className="headline-burgundy">safer food.</span>
                </h2>
                <ul className="promo-features-list">
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Detect safety violations</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Check compliance rules</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Get real-time alerts</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Download inspection report</span>
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
