import React, { useState, useRef } from 'react';

const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp'];
const PORTION_PRESETS = [50, 100, 150, 200, 300, 500];

export default function FoodImageUploader({
  onAnalyze,
  isLoading,
  selectedFile,
  setSelectedFile,
  servingGrams,
  setServingGrams,
  onReset,
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  // Validate and stage file
  const handleFile = (file) => {
    setValidationError(null);

    if (!file) return;

    // Check extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError(
        `Unsupported file type (${ext}). Please upload a JPEG, PNG, WebP, or BMP image.`
      );
      return;
    }

    // Check size
    if (file.size > MAX_SIZE_BYTES) {
      setValidationError(
        `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the 10 MB limit.`
      );
      return;
    }

    if (file.size === 0) {
      setValidationError('Uploaded file is empty.');
      return;
    }

    setSelectedFile(file);

    // Create object URL for preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (isLoading) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!isLoading) setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setSelectedFile(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (onReset) onReset();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedFile || isLoading) return;
    onAnalyze(selectedFile, servingGrams);
  };

  return (
    <div className="glass-panel" id="food-uploader-card">
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--text-white)' }}>
        Upload Food Dish
      </h2>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Capture or upload a clear photo of your food to identify ingredients and retrieve verified nutrition metrics.
      </p>

      {/* Dropzone or Preview */}
      {!previewUrl ? (
        <div
          id="upload-dropzone"
          className={`dropzone ${isDragOver ? 'drag-active' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <input
            id="food-image-input"
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp,.bmp,image/jpeg,image/png,image/webp,image/bmp"
            onChange={handleInputChange}
            style={{ display: 'none' }}
          />
          <div className="dropzone-icon">🥗</div>
          <p className="dropzone-heading">Drop food photo here, or browse</p>
          <p className="dropzone-subtext">Supported formats: JPEG, PNG, WebP, BMP (max 10 MB)</p>
          <div className="badge-formats">
            <span>High Resolution</span>
            <span>•</span>
            <span>Single Dish</span>
            <span>•</span>
            <span>Natural Lighting</span>
          </div>
        </div>
      ) : (
        <div className="preview-container" id="food-image-preview">
          <img src={previewUrl} alt="Selected food preview" className="preview-img" />
          <div className="preview-overlay">
            <div className="file-info">
              {selectedFile?.name}
              <div className="file-meta">
                {(selectedFile?.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile?.type || 'Image'}
              </div>
            </div>
            <button
              id="btn-remove-image"
              type="button"
              className="btn-secondary"
              onClick={handleClear}
              disabled={isLoading}
              title="Remove image and choose another"
            >
              ✕ Change Photo
            </button>
          </div>
        </div>
      )}

      {/* Validation Error */}
      {validationError && (
        <div className="alert-box error" style={{ marginTop: '1rem' }} id="upload-validation-error">
          <span>⚠️</span>
          <span>{validationError}</span>
        </div>
      )}

      {/* Serving Size Option */}
      <div className="control-group">
        <label className="control-label" htmlFor="serving-grams-input">
          <span>Serving Portion (Optional)</span>
          <span className="control-label-hint">Default: 100g standard reference</span>
        </label>
        <div className="input-wrapper">
          <input
            id="serving-grams-input"
            type="number"
            min="1"
            max="5000"
            step="1"
            placeholder="e.g. 150 (Leave blank for per-100g basis)"
            className="text-input"
            value={servingGrams || ''}
            onChange={(e) => {
              const val = e.target.value ? parseFloat(e.target.value) : null;
              setServingGrams(val);
            }}
            disabled={isLoading}
          />
          <span className="input-unit">grams (g)</span>
        </div>

        {/* Presets */}
        <div className="portion-presets">
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center', marginRight: '0.25rem' }}>
            Quick:
          </span>
          {PORTION_PRESETS.map((p) => (
            <button
              key={p}
              type="button"
              className={`preset-chip ${servingGrams === p ? 'active' : ''}`}
              onClick={() => setServingGrams(p)}
              disabled={isLoading}
            >
              {p}g
            </button>
          ))}
          {servingGrams && (
            <button
              type="button"
              className="preset-chip"
              onClick={() => setServingGrams(null)}
              disabled={isLoading}
              title="Reset to 100g reference"
            >
              Reset (100g)
            </button>
          )}
        </div>
      </div>

      {/* Action Button */}
      <button
        id="btn-analyze-food"
        type="button"
        className="btn-primary"
        onClick={handleSubmit}
        disabled={!selectedFile || isLoading}
      >
        {isLoading ? (
          <>
            <div className="spinner" />
            <span>Analyzing Image & Calculating Nutrition...</span>
          </>
        ) : (
          <>
            <span>⚡</span>
            <span>Identify Food & Analyze Nutrition</span>
          </>
        )}
      </button>
    </div>
  );
}
