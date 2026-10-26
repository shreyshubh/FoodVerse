import React, { useState } from 'react';
import { postFormData } from '../../shared/api/client';
import RecentChecksSection from '../../shared/components/RecentChecksSection';

import promoPastaImg from '../../assets/illustrations/pasta_desk.png';
import recentPaneer from '../../assets/illustrations/recent_paneer_masala.png';
import recentPulao from '../../assets/illustrations/recent_pulao.png';
import recentStirfry from '../../assets/illustrations/recent_stirfry.png';

const SAMPLE_IDEAS = [
  'Paneer curry with tomatoes and peas',
  'Vegetable pulao with aromatic spices',
  'Chicken stir fry with crunchy bell peppers',
  'Creamy tomato garlic pasta with basil',
  'Healthy roasted chickpea & avocado salad',
];

export default function SmartKitchenPage() {
  const [ingredientsText, setIngredientsText] = useState('');
  const [activeInputTab, setActiveInputTab] = useState('describe'); // 'describe', 'image', 'example'
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const [cuisine, setCuisine] = useState('Any');
  const [dietType, setDietType] = useState('Any');
  const [spiceLevel, setSpiceLevel] = useState('Medium');
  const [servings, setServings] = useState(2);

  const [isGenerating, setIsGenerating] = useState(false);
  const [recipe, setRecipe] = useState(null);
  const [error, setError] = useState(null);
  const [voiceNotice, setVoiceNotice] = useState(false);
  const [recentKey, setRecentKey] = useState(0);

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setRecipe(null);
      setError(null);
    }
  };

  const handleClearImage = () => {
    setSelectedImage(null);
    setPreviewUrl(null);
  };

  const handleSelectChip = (ideaText) => {
    setIngredientsText(ideaText);
    setActiveInputTab('describe');
  };

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    if (!ingredientsText.trim() && !selectedImage) {
      alert('Please describe your ingredients or upload a photo to generate a recipe.');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setRecipe(null);

    try {
      const formData = new FormData();
      formData.append('ingredients_text', ingredientsText.trim() || 'Assorted pantry ingredients');
      formData.append('servings', String(servings || 2));
      if (cuisine !== 'Any') {
        formData.append('cuisine', cuisine);
      }
      if (dietType !== 'Any') {
        formData.append('dietary_restrictions', dietType);
      }
      if (selectedImage) {
        formData.append('image', selectedImage);
      }

      const data = await postFormData('/api/v1/recipes/generate', formData);
      setRecipe(data);
      setRecentKey((k) => k + 1);
    } catch (err) {
      console.error('Recipe generation error:', err);
      setError(err.message || 'Unable to generate recipe. Please ensure backend LLM service is available.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="module-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div className="header-icon-badge" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z"></path>
            <line x1="6" y1="17" x2="18" y2="17"></line>
          </svg>
        </div>
        <div>
          <h1 className="page-title">Smart Recipe Generator</h1>
          <p className="page-subtitle">
            Describe your ingredients or upload a photo to get a full recipe.
          </p>
        </div>
      </div>

      <div className="workspace-grid">
        {/* Left Column: Form & Inputs */}
        <div className="workspace-main-col">
          <div className="workspace-card">
            {/* Input Selection Tabs */}
            <div className="inspection-mode-tabs">
              <button
                type="button"
                className={`mode-tab-btn ${activeInputTab === 'describe' ? 'active' : ''}`}
                onClick={() => setActiveInputTab('describe')}
              >
                <span>Describe Ingredients</span>
              </button>
              <button
                type="button"
                className={`mode-tab-btn ${activeInputTab === 'image' ? 'active' : ''}`}
                onClick={() => setActiveInputTab('image')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                <span>Upload Image</span>
              </button>
              <button
                type="button"
                className={`mode-tab-btn ${activeInputTab === 'example' ? 'active' : ''}`}
                onClick={() => {
                  setActiveInputTab('describe');
                  setIngredientsText('Chicken breast, basmati rice, ripe tomatoes, onion, garlic');
                }}
              >
                <span>Use Example</span>
              </button>
            </div>

            {/* Optional Image Upload if tab active */}
            {activeInputTab === 'image' && (
              <div className={`upload-drop-card full-width ${previewUrl ? 'has-preview' : ''}`} style={{ marginBottom: '1rem' }}>
                {previewUrl ? (
                  <div className="preview-container">
                    <img src={previewUrl} alt="Pantry ingredients" className="upload-preview-img" />
                    <button type="button" className="preview-remove-btn" onClick={handleClearImage}>
                      ✕
                    </button>
                  </div>
                ) : (
                  <label className="upload-drop-label">
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleImageChange}
                      className="visually-hidden-file-input"
                    />
                    <div className="upload-circle-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D43828" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                      </svg>
                    </div>
                    <span className="upload-title">Upload Ingredients Image</span>
                    <span className="upload-prompt">Click to snap or browse pantry photo</span>
                  </label>
                )}
              </div>
            )}

            {/* Ingredients Textarea */}
            <div className="form-field-group">
              <div className="textarea-with-controls-wrap">
                <textarea
                  id="ingredients-textarea-input"
                  className="warm-textarea"
                  placeholder="e.g. I have chicken, rice, tomatoes. What can I make?"
                  rows={4}
                  maxLength={300}
                  value={ingredientsText}
                  onChange={(e) => setIngredientsText(e.target.value)}
                />
                <div className="textarea-footer-row">
                  <span className="char-counter">{ingredientsText.length}/300</span>
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
              </div>
              {voiceNotice && (
                <span className="form-inline-note">
                  🎙️ Voice capture available in supported browser environments.
                </span>
              )}
            </div>

            {/* Dietary Preferences Three Dropdowns Row */}
            <div className="preferences-section">
              <label className="form-sublabel">Dietary preferences (optional)</label>
              <div className="three-dropdowns-row">
                <div className="form-field-group">
                  <label htmlFor="recipe-cuisine-select" className="dropdown-label">Cuisine</label>
                  <select
                    id="recipe-cuisine-select"
                    className="warm-select-input"
                    value={cuisine}
                    onChange={(e) => setCuisine(e.target.value)}
                  >
                    <option value="Any">Any</option>
                    <option value="Indian">Indian</option>
                    <option value="Italian">Italian</option>
                    <option value="Mexican">Mexican</option>
                    <option value="Asian">Asian</option>
                    <option value="Mediterranean">Mediterranean</option>
                  </select>
                </div>

                <div className="form-field-group">
                  <label htmlFor="recipe-diet-select" className="dropdown-label">Diet type</label>
                  <select
                    id="recipe-diet-select"
                    className="warm-select-input"
                    value={dietType}
                    onChange={(e) => setDietType(e.target.value)}
                  >
                    <option value="Any">Any</option>
                    <option value="Vegetarian">Vegetarian</option>
                    <option value="Vegan">Vegan</option>
                    <option value="Keto">Keto</option>
                    <option value="High-Protein">High-Protein</option>
                    <option value="Low-Carb">Low-Carb</option>
                  </select>
                </div>

                <div className="form-field-group">
                  <label htmlFor="recipe-spice-select" className="dropdown-label">Spice level</label>
                  <select
                    id="recipe-spice-select"
                    className="warm-select-input"
                    value={spiceLevel}
                    onChange={(e) => setSpiceLevel(e.target.value)}
                  >
                    <option value="Mild">Mild</option>
                    <option value="Medium">Medium</option>
                    <option value="Spicy">Spicy</option>
                    <option value="Extra Spicy">Extra Spicy</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Primary Action Button */}
            <button
              type="button"
              className="btn-burgundy-primary"
              onClick={handleGenerate}
              disabled={isGenerating || (!ingredientsText.trim() && !selectedImage)}
              id="generate-recipe-btn"
            >
              {isGenerating ? (
                <span>Generating Recipe with LangGraph...</span>
              ) : (
                <>
                  <span>Generate Recipe</span>
                  <span className="btn-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          {/* Sample Ideas Chips */}
          <div className="sample-ideas-section">
            <span className="sample-ideas-label">Sample ideas</span>
            <div className="sample-chips-wrap">
              {SAMPLE_IDEAS.map((idea, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="idea-chip-btn"
                  onClick={() => handleSelectChip(idea)}
                >
                  {idea.split(' ')[0]} {idea.split(' ')[1] || ''}
                </button>
              ))}
            </div>
          </div>

          {/* Live Recent Recipes */}
          <RecentChecksSection
            feature="recipe_generation"
            heading="Recent recipes"
            defaultFallbackImage={recentPaneer}
            refreshKey={recentKey}
          />
        </div>

        {/* Right Column: Promotional Card OR Live Recipe Results */}
        <div className="workspace-side-col">
          {error && (
            <div className="result-alert-box error" role="alert">
              <span className="alert-icon">⚠️</span>
              <div className="alert-body">
                <strong>Recipe Generation Failed:</strong> {error}
              </div>
              <button type="button" className="alert-retry-btn" onClick={handleGenerate}>
                Retry
              </button>
            </div>
          )}

          {isGenerating && (
            <div className="loading-card">
              <div className="warm-spinner" />
              <h3>Crafting your personalized recipe...</h3>
              <p>LangGraph multi-step agent: validation, dietary verification & USDA nutrition grounding</p>
            </div>
          )}

          {!isGenerating && recipe && (
            <div className="analysis-result-card" id="recipe-result-panel">
              <div className="result-card-header">
                <div>
                  <span className="result-tag">CHEF CREATION</span>
                  <h2 className="result-dish-title">{recipe.title || 'Custom Recipe'}</h2>
                </div>
                {recipe.difficulty && (
                  <div className="confidence-pill high">
                    <span>{recipe.difficulty}</span>
                  </div>
                )}
              </div>

              {recipe.summary && (
                <p className="recipe-summary-text">{recipe.summary}</p>
              )}

              {/* Prep & Cook Time Row */}
              <div className="recipe-timing-row">
                <div className="timing-box">
                  <span className="timing-label">Prep Time</span>
                  <span className="timing-val">{recipe.prep_time_minutes || 15} mins</span>
                </div>
                <div className="timing-box">
                  <span className="timing-label">Cook Time</span>
                  <span className="timing-val">{recipe.cook_time_minutes || 20} mins</span>
                </div>
                <div className="timing-box">
                  <span className="timing-label">Servings</span>
                  <span className="timing-val">{recipe.servings || 2}</span>
                </div>
              </div>

              {/* Nutrition estimate */}
              {recipe.nutrition && (
                <div className="recipe-nutrition-box">
                  <span className="assumptions-heading">Nutritional Breakdown (per serving):</span>
                  <div className="macros-stat-grid mini">
                    <div className="macro-stat-box">
                      <span className="macro-value calories">{Math.round(recipe.nutrition.calories_kcal || 0)}</span>
                      <span className="macro-label">kcal</span>
                    </div>
                    <div className="macro-stat-box">
                      <span className="macro-value">{Math.round(recipe.nutrition.protein_g || 0)}g</span>
                      <span className="macro-label">Protein</span>
                    </div>
                    <div className="macro-stat-box">
                      <span className="macro-value">{Math.round(recipe.nutrition.carbohydrates_g || 0)}g</span>
                      <span className="macro-label">Carbs</span>
                    </div>
                    <div className="macro-stat-box">
                      <span className="macro-value">{Math.round(recipe.nutrition.fat_g || 0)}g</span>
                      <span className="macro-label">Fat</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Ingredients List */}
              {recipe.ingredients && recipe.ingredients.length > 0 && (
                <div className="recipe-ingredients-box">
                  <span className="assumptions-heading">Ingredients:</span>
                  <ul className="checklist-items">
                    {recipe.ingredients.map((ing, i) => (
                      <li key={i} className="ingredient-item">
                        <span className="check-bullet">✓</span>
                        <span>{ing}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Ordered Cooking Steps */}
              {recipe.steps && recipe.steps.length > 0 && (
                <div className="recipe-steps-box">
                  <span className="assumptions-heading">Cooking Instructions:</span>
                  <ol className="ordered-steps-list">
                    {recipe.steps.map((step, i) => (
                      <li key={i} className="step-item">
                        <span className="step-number">{i + 1}</span>
                        <span className="step-desc">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Warnings or Allergen notices */}
              {recipe.warnings && recipe.warnings.length > 0 && (
                <div className="assumptions-box">
                  <span className="assumptions-heading">Dietary Notes:</span>
                  <ul className="assumptions-list">
                    {recipe.warnings.map((w, i) => (
                      <li key={i}>• {w}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="result-actions-row">
                <button
                  type="button"
                  className="btn-secondary-action"
                  onClick={() => {
                    setRecipe(null);
                    setIngredientsText('');
                    setSelectedImage(null);
                    setPreviewUrl(null);
                  }}
                >
                  Create Another Recipe
                </button>
                {recipe.report_id && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-status-success)', fontWeight: 600 }}>
                    ✓ Saved to MongoDB (ID: {recipe.report_id.slice(-6)})
                  </span>
                )}
                <span className="request-id-text">ID: {recipe.request_id?.slice(0, 8)}</span>
              </div>
            </div>
          )}

          {!isGenerating && !recipe && !error && (
            <div className="yellow-promo-card">
              <div className="promo-illustration-wrap">
                <img src={promoPastaImg} alt="Plate of fresh pasta with basil" className="promo-hero-img" />
              </div>
              <div className="promo-text-group">
                <h2 className="promo-headline">
                  <span className="headline-green">Turn ingredients</span>
                  <br />
                  <span className="headline-burgundy">into something</span>
                  <br />
                  <span className="headline-burgundy">special.</span>
                </h2>
                <ul className="promo-features-list">
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Get step-by-step recipes</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Use what you already have</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Try different cuisines</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Cooking tips and substitutions</span>
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
