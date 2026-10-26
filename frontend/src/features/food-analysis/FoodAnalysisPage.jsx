import React, { useState } from 'react';
import { analyzeFoodImage } from './foodAnalysisApi';
import FoodAnalysisResult from './FoodAnalysisResult';
import RecentChecksSection from '../../shared/components/RecentChecksSection';

import promoBowlImg from '../../assets/illustrations/bowl_desk.png';
import biryaniThumb from '../../assets/illustrations/recent_biryani.png';
import pastaThumb from '../../assets/illustrations/pasta_desk.png';
import saladThumb from '../../assets/illustrations/salad_desk.png';
import bananaThumb from '../../assets/illustrations/recent_banana.png';
import dalThumb from '../../assets/illustrations/recent_dal_rice.png';

const EXAMPLES = [
  { id: 'biryani', name: 'Biryani', thumb: biryaniThumb, path: '/sample_pizza.jpg' },
  { id: 'pasta', name: 'Pasta', thumb: pastaThumb, path: '/sample_pizza.jpg' },
  { id: 'salad', name: 'Salad', thumb: saladThumb, path: '/sample_pizza.jpg' },
];

export default function FoodAnalysisPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [contextDescription, setContextDescription] = useState('');
  const [servingGrams, setServingGrams] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
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

  const handleSelectExample = async (example) => {
    try {
      const response = await fetch(example.path);
      const blob = await response.blob();
      const file = new File([blob], `${example.id}.jpg`, { type: 'image/jpeg' });
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    } catch {
      alert(`Could not load ${example.name} example.`);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      alert('Please upload or select a food image first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await analyzeFoodImage(selectedFile, servingGrams);
      setResult(data);
      setRecentKey((k) => k + 1);
    } catch (err) {
      console.error('Food analysis error:', err);
      setError(err.message || 'Unable to analyze food. Ensure the backend is reachable.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecalculate = async (newGrams) => {
    setServingGrams(newGrams);
    if (!selectedFile) return;
    setIsLoading(true);
    try {
      const data = await analyzeFoodImage(selectedFile, newGrams);
      setResult(data);
    } catch (err) {
      console.error('Recalculate error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="module-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div className="header-icon-badge" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="3" ry="3"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
        </div>
        <div>
          <h1 className="page-title">Food Recognition</h1>
          <p className="page-subtitle">
            Upload a food image and get the dish name, calories and detailed nutrition.
          </p>
        </div>
      </div>

      <div className="workspace-grid">
        {/* Left Column: Form & Inputs */}
        <div className="workspace-main-col">
          <div className="workspace-card">
            <div className="upload-and-examples-row">
              {/* Upload Drop Zone */}
              <div
                className={`upload-drop-card ${previewUrl ? 'has-preview' : ''}`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
              >
                {previewUrl ? (
                  <div className="preview-container">
                    <img src={previewUrl} alt="Selected food item" className="upload-preview-img" />
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

              {/* Try an Example */}
              <div className="try-example-box">
                <span className="example-box-heading">Try an example</span>
                <div className="examples-list">
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex.id}
                      type="button"
                      className="example-item-btn"
                      onClick={() => handleSelectExample(ex)}
                    >
                      <div className="example-thumb-wrap">
                        <img src={ex.thumb} alt={ex.name} className="example-thumb-img" />
                      </div>
                      <span className="example-name">{ex.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Context Input */}
            <div className="form-field-group">
              <label htmlFor="food-context-input" className="form-label">
                Add context (optional)
              </label>
              <div className="input-with-button-wrap">
                <input
                  id="food-context-input"
                  type="text"
                  className="warm-text-input"
                  placeholder="e.g. homemade, restaurant, portion size etc."
                  value={contextDescription}
                  onChange={(e) => setContextDescription(e.target.value)}
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

            {/* Serving size control */}
            <div className="serving-size-row">
              <label htmlFor="food-serving-grams" className="form-sublabel">
                Serving basis (grams):
              </label>
              <input
                id="food-serving-grams"
                type="number"
                min="10"
                max="2000"
                step="10"
                value={servingGrams}
                onChange={(e) => setServingGrams(Number(e.target.value))}
                className="serving-input"
              />
              <span className="serving-unit">g</span>
            </div>

            {/* Analyze Action Button */}
            <button
              type="button"
              className="btn-burgundy-primary"
              onClick={handleAnalyze}
              disabled={isLoading || !selectedFile}
              id="analyze-food-btn"
            >
              {isLoading ? (
                <span>Analyzing Food...</span>
              ) : (
                <>
                  <span>Analyse Food</span>
                  <span className="btn-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          {/* Live Recent Analyses Row */}
          <RecentChecksSection
            feature="food_recognition"
            heading="Recent analyses"
            defaultFallbackImage={biryaniThumb}
            refreshKey={recentKey}
          />
        </div>

        {/* Right Column: Promotional Card OR Live Results */}
        <div className="workspace-side-col">
          {error && (
            <div className="result-alert-box error" role="alert">
              <span className="alert-icon">⚠️</span>
              <div className="alert-body">
                <strong>Analysis Failed:</strong> {error}
              </div>
              <button type="button" className="alert-retry-btn" onClick={handleAnalyze}>
                Retry
              </button>
            </div>
          )}

          {isLoading && (
            <div className="loading-card">
              <div className="warm-spinner" />
              <h3>Recognizing dish & estimating nutrition...</h3>
              <p>PyTorch MobileNetV2 inference + USDA FoodData Central lookup</p>
            </div>
          )}

          {!isLoading && result && (
            <FoodAnalysisResult
              result={result}
              onRecalculatePortion={handleRecalculate}
              currentServingGrams={servingGrams}
              onReset={handleClear}
            />
          )}

          {!isLoading && !result && !error && (
            <div className="yellow-promo-card">
              <div className="promo-illustration-wrap">
                <img src={promoBowlImg} alt="Nutritious food bowl illustration" className="promo-hero-img" />
              </div>
              <div className="promo-text-group">
                <h2 className="promo-headline">
                  <span className="headline-green">Snap</span>
                  <br />
                  <span className="headline-green">your meal.</span>
                  <br />
                  <span className="headline-burgundy">Know what's</span>
                  <br />
                  <span className="headline-burgundy">inside.</span>
                </h2>
                <ul className="promo-features-list">
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Get dish name</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>See calories and nutrition</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Receive healthy suggestions</span>
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
