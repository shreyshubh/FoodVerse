import React, { useState } from 'react';
import { postJson } from '../../shared/api/client';
import RecentChecksSection from '../../shared/components/RecentChecksSection';

import promoSaladImg from '../../assets/illustrations/salad_desk.png';
import mealOatsThumb from '../../assets/illustrations/recent_meal_oats.png';
import mealPaneerThumb from '../../assets/illustrations/recent_meal_paneer.png';
import mealSmoothieThumb from '../../assets/illustrations/recent_meal_smoothie.png';
import mealKhichdiThumb from '../../assets/illustrations/recent_meal_khichdi.png';

export default function MealPlannerPage() {
  const [age, setAge] = useState('22');
  const [gender, setGender] = useState('Female');
  const [heightCm, setHeightCm] = useState('175');
  const [weightKg, setWeightKg] = useState('70');
  const [activity, setActivity] = useState('Moderate');
  const [goal, setGoal] = useState('Maintenance');
  const [dietType, setDietType] = useState('Standard');
  const [cuisine, setCuisine] = useState('Global');
  const [allergies, setAllergies] = useState('');

  const [activePlanTab, setActivePlanTab] = useState('today'); // 'today' or 'weekly'
  const [isGenerating, setIsGenerating] = useState(false);
  const [planData, setPlanData] = useState(null);
  const [error, setError] = useState(null);
  const [voiceNotice, setVoiceNotice] = useState(false);
  const [recentKey, setRecentKey] = useState(0);

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    setIsGenerating(true);
    setError(null);
    setPlanData(null);

    try {
      const payload = {
        age: parseInt(age, 10) || 22,
        gender: gender || 'Female',
        height_cm: parseFloat(heightCm) || 175.0,
        weight_kg: parseFloat(weightKg) || 70.0,
        activity_level: activity || 'Moderate',
        goal: goal || 'Maintenance',
        diet_type: dietType || 'Standard',
        cuisine_preference: cuisine || 'Global',
        allergies: allergies.trim(),
        medical_conditions: '',
      };

      const data = await postJson('/api/v1/meal-plans/generate', payload);
      setPlanData(data);
      setRecentKey((k) => k + 1);
    } catch (err) {
      console.error('Meal planning error:', err);
      setError(err.message || 'Unable to generate personalized meal plan.');
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
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div>
          <h1 className="page-title">Personalized Meal Planner</h1>
          <p className="page-subtitle">
            Plan your week around your health goals and preferences.
          </p>
        </div>
      </div>

      <div className="workspace-grid">
        {/* Left Column: Profile Form */}
        <div className="workspace-main-col">
          <div className="workspace-card">
            {/* Form Header */}
            <div className="profile-section-header">
              <div className="profile-user-icon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2E4D1D" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <h2 className="profile-section-title">Your Profile</h2>
            </div>

            {/* Row 1: Age, Gender, Height, Weight */}
            <div className="profile-four-col-row">
              <div className="form-field-group">
                <label htmlFor="user-age-input" className="form-sublabel">Age</label>
                <input
                  id="user-age-input"
                  type="number"
                  min="12"
                  max="120"
                  className="warm-text-input mini"
                  placeholder="e.g. 22"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
              </div>

              <div className="form-field-group">
                <label htmlFor="user-gender-select" className="form-sublabel">Gender</label>
                <select
                  id="user-gender-select"
                  className="warm-select-input mini"
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="form-field-group">
                <label htmlFor="user-height-input" className="form-sublabel">Height (cm)</label>
                <input
                  id="user-height-input"
                  type="number"
                  min="100"
                  max="250"
                  className="warm-text-input mini"
                  placeholder="e.g. 175"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                />
              </div>

              <div className="form-field-group">
                <label htmlFor="user-weight-input" className="form-sublabel">Weight (kg)</label>
                <input
                  id="user-weight-input"
                  type="number"
                  min="30"
                  max="300"
                  className="warm-text-input mini"
                  placeholder="e.g. 70"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                />
              </div>
            </div>

            {/* Row 2: Activity level, Goal */}
            <div className="form-two-col-row">
              <div className="form-field-group">
                <label htmlFor="user-activity-select" className="form-sublabel">Activity level</label>
                <select
                  id="user-activity-select"
                  className="warm-select-input"
                  value={activity}
                  onChange={(e) => setActivity(e.target.value)}
                >
                  <option value="Sedentary">Sedentary (Desk work)</option>
                  <option value="Light">Light (1-2 days exercise)</option>
                  <option value="Moderate">Moderate (3-5 days exercise)</option>
                  <option value="Active">Active (6-7 days sports)</option>
                  <option value="Very Active">Very Active (Physical job/athlete)</option>
                </select>
              </div>

              <div className="form-field-group">
                <label htmlFor="user-goal-select" className="form-sublabel">Goal</label>
                <select
                  id="user-goal-select"
                  className="warm-select-input"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                >
                  <option value="Maintenance">Maintain weight</option>
                  <option value="Weight Loss">Weight loss</option>
                  <option value="Muscle Gain">Muscle gain</option>
                </select>
              </div>
            </div>

            {/* Row 3: Diet type, Cuisine preferences */}
            <div className="form-two-col-row">
              <div className="form-field-group">
                <label htmlFor="user-diet-select" className="form-sublabel">Diet type</label>
                <select
                  id="user-diet-select"
                  className="warm-select-input"
                  value={dietType}
                  onChange={(e) => setDietType(e.target.value)}
                >
                  <option value="Standard">Standard</option>
                  <option value="Vegetarian">Vegetarian</option>
                  <option value="Vegan">Vegan</option>
                  <option value="High Protein">High Protein</option>
                  <option value="Mediterranean">Mediterranean</option>
                  <option value="Keto">Keto</option>
                </select>
              </div>

              <div className="form-field-group">
                <label htmlFor="user-cuisine-input" className="form-sublabel">Cuisine preferences</label>
                <input
                  id="user-cuisine-input"
                  type="text"
                  className="warm-text-input"
                  placeholder="e.g. Indian, Italian, etc."
                  value={cuisine}
                  onChange={(e) => setCuisine(e.target.value)}
                />
              </div>
            </div>

            {/* Row 4: Allergies / Restrictions */}
            <div className="form-field-group">
              <label htmlFor="user-allergies-input" className="form-sublabel">
                Allergies / Restrictions (optional)
              </label>
              <div className="input-with-button-wrap">
                <input
                  id="user-allergies-input"
                  type="text"
                  className="warm-text-input"
                  placeholder="e.g. nuts, gluten, lactose, etc."
                  value={allergies}
                  onChange={(e) => setAllergies(e.target.value)}
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
                  🎙️ Voice input available in supported browser environments.
                </span>
              )}
            </div>

            {/* Generate Action Button */}
            <button
              type="button"
              className="btn-burgundy-primary"
              onClick={handleGenerate}
              disabled={isGenerating}
              id="generate-plan-btn"
            >
              {isGenerating ? (
                <span>Calculating Targets & Crafting Plan...</span>
              ) : (
                <>
                  <span>Generate Meal Plan</span>
                  <span className="btn-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          {/* Live Recent Meal Plans */}
          <RecentChecksSection
            feature="meal_plan"
            heading="Recent meal plans"
            defaultFallbackImage={mealOatsThumb}
            refreshKey={recentKey}
          />
        </div>

        {/* Right Column: Promotional Card OR Live Meal Plan Result */}
        <div className="workspace-side-col">
          {error && (
            <div className="result-alert-box error" role="alert">
              <span className="alert-icon">⚠️</span>
              <div className="alert-body">
                <strong>Planning Error:</strong> {error}
              </div>
              <button type="button" className="alert-retry-btn" onClick={handleGenerate}>
                Retry
              </button>
            </div>
          )}

          {isGenerating && (
            <div className="loading-card">
              <div className="warm-spinner" />
              <h3>Calculating clinical metabolic targets...</h3>
              <p>Mifflin-St Jeor formula + LangGraph deterministic zero-trust allergy verification</p>
            </div>
          )}

          {!isGenerating && planData && (
            <div className="analysis-result-card" id="meal-plan-result-panel">
              <div className="result-card-header">
                <div>
                  <span className="result-tag">TARGETED NUTRITION PLAN</span>
                  <h2 className="result-dish-title">Personalized Daily Plan</h2>
                </div>
                <div className="confidence-pill high">
                  <span>{planData.adherence_score_pct || 90}% Optimal</span>
                </div>
              </div>

              {/* Targets Summary Box */}
              {planData.calculated_targets && (
                <div className="metabolic-targets-box">
                  <span className="assumptions-heading">Daily Caloric & Macro Targets:</span>
                  <div className="macros-stat-grid">
                    <div className="macro-stat-box">
                      <span className="macro-value calories">
                        {Math.round(planData.calculated_targets.target_calories)}
                      </span>
                      <span className="macro-label">Target kcal</span>
                    </div>
                    <div className="macro-stat-box">
                      <span className="macro-value">
                        {Math.round(planData.calculated_targets.target_protein_g)}g
                      </span>
                      <span className="macro-label">Protein</span>
                    </div>
                    <div className="macro-stat-box">
                      <span className="macro-value">
                        {Math.round(planData.calculated_targets.target_carbs_g)}g
                      </span>
                      <span className="macro-label">Carbs</span>
                    </div>
                    <div className="macro-stat-box">
                      <span className="macro-value">
                        {Math.round(planData.calculated_targets.target_fat_g)}g
                      </span>
                      <span className="macro-label">Fat</span>
                    </div>
                  </div>
                  <div className="bmr-subtext-row">
                    <span>BMR: {Math.round(planData.calculated_targets.bmr_kcal)} kcal</span>
                    <span>TDEE: {Math.round(planData.calculated_targets.tdee_kcal)} kcal</span>
                    <span>Hydration: {planData.calculated_targets.hydration_liters} L</span>
                  </div>
                </div>
              )}

              {/* Allergy clearance badge */}
              {planData.allergy_safety_cleared && (
                <div className="allergy-cleared-banner">
                  <span className="check-mark">🛡️</span>
                  <span>Zero-Trust Allergy Safety Cleared: No declared allergen conflicts detected.</span>
                </div>
              )}

              {/* Today's Generated Meals */}
              {planData.today_plan?.meals && (
                <div className="today-meals-container">
                  <span className="assumptions-heading">Today's Meal Schedule:</span>
                  <div className="generated-meals-list">
                    {planData.today_plan.meals.map((meal, idx) => (
                      <div key={idx} className="plan-meal-item-card">
                        <div className="plan-meal-header">
                          <span className="meal-type-badge">{meal.meal_type}</span>
                          <span className="meal-cals-text">{Math.round(meal.calories_kcal)} kcal</span>
                        </div>
                        <h4 className="meal-dish-name">{meal.dish_name}</h4>
                        <p className="meal-description">{meal.description}</p>
                        <div className="meal-macro-tags">
                          <span>P: {Math.round(meal.protein_g)}g</span>
                          <span>C: {Math.round(meal.carbohydrates_g)}g</span>
                          <span>F: {Math.round(meal.fat_g)}g</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Coach Notes */}
              {planData.coach_notes && (
                <div className="reasoning-box">
                  <span className="assumptions-heading">Clinical Nutrition Coach Guidance:</span>
                  <p className="reasoning-text">{planData.coach_notes}</p>
                </div>
              )}

              <div className="result-actions-row">
                <button
                  type="button"
                  className="btn-secondary-action"
                  onClick={() => setPlanData(null)}
                >
                  Adjust Profile & Re-plan
                </button>
                {planData.report_id && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-status-success)', fontWeight: 600 }}>
                    ✓ Saved to MongoDB (ID: {planData.report_id.slice(-6)})
                  </span>
                )}
                <span className="request-id-text">ID: {planData.request_id?.slice(0, 8)}</span>
              </div>
            </div>
          )}

          {!isGenerating && !planData && !error && (
            <div className="yellow-promo-card">
              <div className="promo-illustration-wrap">
                <img src={promoSaladImg} alt="Vibrant fresh salad bowl" className="promo-hero-img" />
              </div>
              <div className="promo-text-group">
                <h2 className="promo-headline">
                  <span className="headline-green">A healthier</span>
                  <br />
                  <span className="headline-burgundy">you, one meal</span>
                  <br />
                  <span className="headline-burgundy">at a time.</span>
                </h2>
                <ul className="promo-features-list">
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Personalized meal plans</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Balanced nutrition</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Weekly meal schedule</span>
                  </li>
                  <li>
                    <span className="bullet-circle">●</span>
                    <span>Smart food recommendations</span>
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
