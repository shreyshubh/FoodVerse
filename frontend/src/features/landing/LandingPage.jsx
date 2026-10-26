import React, { useState } from 'react';
import './landing.css';

// Existing illustration and icon assets
import heroBowl from '../../assets/illustrations/hero_bowl.png';
import pastaImg from '../../assets/illustrations/pasta_desk.png';
import iconFood from '../../assets/illustrations/icon_mod_food.png';
import iconFreshness from '../../assets/illustrations/icon_mod_freshness.png';
import iconHygiene from '../../assets/illustrations/icon_mod_hygiene.png';
import iconKitchen from '../../assets/illustrations/icon_mod_kitchen.png';
import iconPlanner from '../../assets/illustrations/icon_mod_planner.png';

export default function LandingPage({ onSelectTab, onOpenAuth, user }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollToSection = (sectionId) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLogoClick = () => {
    setMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLoginClick = () => {
    setMobileMenuOpen(false);
    if (onOpenAuth) {
      onOpenAuth('login');
    }
  };

  const handleSignupClick = () => {
    setMobileMenuOpen(false);
    if (user) {
      // If already logged in, go straight to the main overview workspace
      onSelectTab('overview');
    } else if (onOpenAuth) {
      onOpenAuth('signup');
    }
  };

  return (
    <div className="landing-root">
      {/* ====================================================================
          1. NAVIGATION BAR
          ==================================================================== */}
      <header className="landing-nav-wrapper">
        <div className="landing-nav-container">
          {/* Left: Brand Logo / Wordmark */}
          <button
            type="button"
            className="landing-brand"
            onClick={handleLogoClick}
            aria-label="FoodVerse AI Home"
          >
            <div className="landing-brand-leaf" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"
                  fill="#2E7D32"
                />
                <path
                  d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.5 12 16.3 12 19c0 1.5-.7 2-2 2H2Z"
                  fill="#7CB342"
                />
              </svg>
            </div>
            <span className="landing-brand-title">FoodVerse</span>
            <span className="landing-brand-badge">AI</span>
          </button>

          {/* Center: Section Links */}
          <nav className="landing-nav-center" aria-label="Landing Page Navigation">
            <button
              type="button"
              className="landing-nav-link"
              onClick={() => scrollToSection('features')}
            >
              Features
            </button>
            <button
              type="button"
              className="landing-nav-link"
              onClick={() => scrollToSection('how-it-works')}
            >
              How It Works
            </button>
            <button
              type="button"
              className="landing-nav-link"
              onClick={() => scrollToSection('about')}
            >
              About
            </button>
          </nav>

          {/* Right: Authentication Actions */}
          <div className="landing-nav-actions">
            {user ? (
              <>
                <button
                  type="button"
                  className="landing-user-badge"
                  onClick={() => onSelectTab('overview')}
                  title="Go to Personal Workspace"
                >
                  <span className="landing-user-avatar">
                    {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                  </span>
                  <span className="landing-user-name">{user.name || 'My Kitchen'}</span>
                </button>
                <button
                  type="button"
                  className="landing-btn-primary"
                  onClick={() => onSelectTab('overview')}
                >
                  Open Dashboard →
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="landing-btn-login"
                  onClick={handleLoginClick}
                >
                  Login
                </button>
                <button
                  type="button"
                  className="landing-btn-primary"
                  onClick={handleSignupClick}
                >
                  Get Started
                </button>
              </>
            )}

            {/* Mobile Hamburger Toggle */}
            <button
              type="button"
              className="landing-mobile-toggle"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-label={mobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
              aria-expanded={mobileMenuOpen}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                {mobileMenuOpen ? (
                  <>
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </>
                ) : (
                  <>
                    <line x1="4" y1="8" x2="20" y2="8" />
                    <line x1="4" y1="16" x2="20" y2="16" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        <div className={`landing-mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
          <button
            type="button"
            className="landing-mobile-nav-link"
            onClick={() => scrollToSection('features')}
          >
            Features
          </button>
          <button
            type="button"
            className="landing-mobile-nav-link"
            onClick={() => scrollToSection('how-it-works')}
          >
            How It Works
          </button>
          <button
            type="button"
            className="landing-mobile-nav-link"
            onClick={() => scrollToSection('about')}
          >
            About
          </button>

          <div className="landing-mobile-actions">
            {user ? (
              <button
                type="button"
                className="landing-btn-primary"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onSelectTab('overview');
                }}
              >
                Open Dashboard →
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="landing-btn-secondary"
                  onClick={handleLoginClick}
                >
                  Login to Account
                </button>
                <button
                  type="button"
                  className="landing-btn-primary"
                  onClick={handleSignupClick}
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ====================================================================
          2. HERO SECTION
          ==================================================================== */}
      <section className="landing-hero" aria-labelledby="hero-heading">
        {/* Left Column: Editorial Value Proposition */}
        <div className="landing-hero-content">
          <div className="landing-eyebrow">
            <span className="landing-eyebrow-dot" aria-hidden="true" />
            <span>YOUR INTELLIGENT FOOD COMPANION</span>
          </div>

          <h1 id="hero-heading" className="landing-hero-title">
            Your Food.<br />
            <span className="landing-hero-title-accent">Smarter</span> Decisions.
          </h1>

          <p className="landing-hero-subtitle">
            From recognizing what's on your plate to exploring freshness, discovering recipes, monitoring kitchen hygiene and planning better meals — bring your entire food journey into one place.
          </p>

          <div className="landing-hero-cta-group">
            <button
              type="button"
              className="landing-btn-primary"
              onClick={handleSignupClick}
            >
              Get Started
            </button>
            <button
              type="button"
              className="landing-btn-secondary"
              onClick={() => scrollToSection('features')}
            >
              Explore Features →
            </button>
          </div>

          <p className="landing-hero-subline">
            <span className="landing-hero-subline-leaf" aria-hidden="true">✦</span>
            <span>One kitchen. More possibilities.</span>
          </p>
        </div>

        {/* Right Column: Editorial Food Composition & Floating Cards */}
        <div className="landing-hero-visual" aria-hidden="true">
          {/* Main Dish Plate */}
          <div className="landing-hero-dish-wrap">
            <img
              src={heroBowl}
              alt="Mediterranean Fresh Culinary Bowl"
              className="landing-hero-dish-img"
              loading="eager"
            />
          </div>

          {/* Floating Card 1: Food Recognition */}
          <div className="landing-card-float landing-card-float-top">
            <span className="landing-card-badge-top">Food Recognition</span>
            <div className="landing-card-title-sm">Harvest Grain Bowl</div>
            <div className="landing-card-stats">380 kcal · 24g Protein</div>
          </div>

          {/* Floating Card 2: Freshness Indicator */}
          <div className="landing-card-float landing-card-float-bottom">
            <div className="landing-card-fresh-row">
              <span className="landing-card-fresh-dot" />
              <span className="landing-card-fresh-label">Freshness Analysis</span>
            </div>
            <div className="landing-card-fresh-score">Optimal Condition</div>
            <div className="landing-card-fresh-sub">Day 2 in Crisper · Safe</div>
          </div>

          {/* Floating Card 3: Recipe Inspiration */}
          <div className="landing-card-float landing-card-float-left">
            <div className="landing-card-recipe-title">Smart Kitchen</div>
            <div className="landing-card-recipe-meta">
              <span>Garlic Herb Bowl</span>
              <span>· 20 min</span>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          3. FEATURE SHOWCASE GRID (#features)
          ==================================================================== */}
      <section id="features" className="landing-section" aria-labelledby="features-heading">
        <div className="landing-section-header">
          <span className="landing-section-eyebrow">INTEGRATED MODULES</span>
          <h2 id="features-heading" className="landing-section-heading">
            Everything Your Food Journey Needs
          </h2>
          <p className="landing-section-sub">
            From the first scan to the final bite, make more informed decisions in your kitchen.
          </p>
        </div>

        <div className="landing-features-grid">
          {/* 1. Food Recognition */}
          <article
            className="landing-feature-card"
            onClick={() => onSelectTab('food_recognition')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onSelectTab('food_recognition')}
          >
            <div>
              <div className="landing-feature-top">
                <div className="landing-feature-icon-wrap">
                  <img src={iconFood} alt="" className="landing-feature-icon-img" />
                </div>
                <span className="landing-feature-num">01</span>
              </div>
              <h3 className="landing-feature-title">Food Recognition</h3>
              <p className="landing-feature-desc">
                Discover what’s on your plate with AI-powered food identification.
              </p>
              <div className="landing-feature-tags">
                <span className="landing-feature-tag">101 Dishes</span>
                <span className="landing-feature-tag">USDA Macros</span>
                <span className="landing-feature-tag">Portion Scaling</span>
              </div>
            </div>
            <span className="landing-feature-action-link">
              Try Food Recognition →
            </span>
          </article>

          {/* 2. Freshness Analysis */}
          <article
            className="landing-feature-card"
            onClick={() => onSelectTab('freshness')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onSelectTab('freshness')}
          >
            <div>
              <div className="landing-feature-top">
                <div className="landing-feature-icon-wrap">
                  <img src={iconFreshness} alt="" className="landing-feature-icon-img" />
                </div>
                <span className="landing-feature-num">02</span>
              </div>
              <h3 className="landing-feature-title">Freshness Analysis</h3>
              <p className="landing-feature-desc">
                Explore visible signs of freshness and potential spoilage from food images.
              </p>
              <div className="landing-feature-tags">
                <span className="landing-feature-tag">Visual Degradation</span>
                <span className="landing-feature-tag">Storage Days</span>
                <span className="landing-feature-tag">Safety Alerts</span>
              </div>
            </div>
            <span className="landing-feature-action-link">
              Inspect Freshness →
            </span>
          </article>

          {/* 3. Hygiene Inspector */}
          <article
            className="landing-feature-card"
            onClick={() => onSelectTab('hygiene')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onSelectTab('hygiene')}
          >
            <div>
              <div className="landing-feature-top">
                <div className="landing-feature-icon-wrap">
                  <img src={iconHygiene} alt="" className="landing-feature-icon-img" />
                </div>
                <span className="landing-feature-num">03</span>
              </div>
              <h3 className="landing-feature-title">Hygiene Inspector</h3>
              <p className="landing-feature-desc">
                Review supported kitchen inspections and identify visible hygiene concerns.
              </p>
              <div className="landing-feature-tags">
                <span className="landing-feature-tag">PPE Auditing</span>
                <span className="landing-feature-tag">Gloves & Masks</span>
                <span className="landing-feature-tag">Compliance Rate</span>
              </div>
            </div>
            <span className="landing-feature-action-link">
              Launch Hygiene Monitor →
            </span>
          </article>

          {/* 4. Smart Kitchen */}
          <article
            className="landing-feature-card"
            onClick={() => onSelectTab('smart_kitchen')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onSelectTab('smart_kitchen')}
          >
            <div>
              <div className="landing-feature-top">
                <div className="landing-feature-icon-wrap">
                  <img src={iconKitchen} alt="" className="landing-feature-icon-img" />
                </div>
                <span className="landing-feature-num">04</span>
              </div>
              <h3 className="landing-feature-title">Smart Kitchen</h3>
              <p className="landing-feature-desc">
                Turn available ingredients into recipes tailored to your preferences.
              </p>
              <div className="landing-feature-tags">
                <span className="landing-feature-tag">Pantry Match</span>
                <span className="landing-feature-tag">Chef Instructions</span>
                <span className="landing-feature-tag">Cooking Times</span>
              </div>
            </div>
            <span className="landing-feature-action-link">
              Generate Recipes →
            </span>
          </article>

          {/* 5. Meal Planner */}
          <article
            className="landing-feature-card"
            onClick={() => onSelectTab('meal_planner')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && onSelectTab('meal_planner')}
          >
            <div>
              <div className="landing-feature-top">
                <div className="landing-feature-icon-wrap">
                  <img src={iconPlanner} alt="" className="landing-feature-icon-img" />
                </div>
                <span className="landing-feature-num">05</span>
              </div>
              <h3 className="landing-feature-title">Meal Planner</h3>
              <p className="landing-feature-desc">
                Plan meals around your preferences, nutritional goals and dietary constraints.
              </p>
              <div className="landing-feature-tags">
                <span className="landing-feature-tag">Daily Schedules</span>
                <span className="landing-feature-tag">Balanced Macros</span>
                <span className="landing-feature-tag">Coach Reports</span>
              </div>
            </div>
            <span className="landing-feature-action-link">
              Create Meal Plan →
            </span>
          </article>
        </div>
      </section>

      {/* ====================================================================
          4. HOW IT WORKS SECTION (#how-it-works)
          ==================================================================== */}
      <section id="how-it-works" className="landing-how-bg" aria-labelledby="how-heading">
        <div className="landing-section">
          <div className="landing-section-header">
            <span className="landing-section-eyebrow">A CLEAR PROCESS</span>
            <h2 id="how-heading" className="landing-section-heading">
              Good Food Decisions, Made Simpler
            </h2>
            <p className="landing-section-sub">
              Three seamless steps to bring clarity, safety, and inspiration to everyday meals.
            </p>
          </div>

          <div className="landing-steps-row">
            {/* Step 01 */}
            <div className="landing-step-card">
              <div className="landing-step-num">01</div>
              <h3 className="landing-step-title">Explore</h3>
              <p className="landing-step-desc">
                Upload a food image, inspect available ingredients or share your preferences.
              </p>
            </div>

            {/* Step 02 */}
            <div className="landing-step-card">
              <div className="landing-step-num">02</div>
              <h3 className="landing-step-title">Discover</h3>
              <p className="landing-step-desc">
                Use the relevant FoodVerse AI tools to explore food recognition, visible freshness indicators, recipes or meal plans.
              </p>
            </div>

            {/* Step 03 */}
            <div className="landing-step-card">
              <div className="landing-step-num">03</div>
              <h3 className="landing-step-title">Save & Revisit</h3>
              <p className="landing-step-desc">
                Keep your analyses and generated plans organized in your existing FoodVerse AI workspace.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          5. VISUAL STORY / BRAND SECTION (#about)
          ==================================================================== */}
      <section id="about" className="landing-section" aria-labelledby="about-heading">
        <div className="landing-brand-story">
          <div className="landing-brand-story-left">
            <span className="landing-story-eyebrow">OUR PHILOSOPHY</span>
            <h2 id="about-heading" className="landing-story-title">
              A Little More Thought Behind Every Bite.
            </h2>
            <p className="landing-story-desc">
              Food is more than what's on your plate. It's the ingredients you choose, the meals you create, the care you take in your kitchen, and the decisions that shape your everyday routine.
            </p>

            <div className="landing-story-pillars">
              <div className="landing-story-pillar-item">
                <div className="landing-story-pillar-title">Nutritional Awareness</div>
                <div className="landing-story-pillar-sub">Insight into your everyday fuel</div>
              </div>
              <div className="landing-story-pillar-item">
                <div className="landing-story-pillar-title">Kitchen Creativity</div>
                <div className="landing-story-pillar-sub">Turning leftovers into meals</div>
              </div>
              <div className="landing-story-pillar-item">
                <div className="landing-story-pillar-title">Conscious Freshness</div>
                <div className="landing-story-pillar-sub">Less spoilage, better taste</div>
              </div>
              <div className="landing-story-pillar-item">
                <div className="landing-story-pillar-title">Safety & Cleanliness</div>
                <div className="landing-story-pillar-sub">Peace of mind while prepping</div>
              </div>
            </div>
          </div>

          <div className="landing-brand-story-right">
            <div className="landing-story-img-wrap">
              <img
                src={pastaImg}
                alt="Culinary Preparation & Ingredients"
                className="landing-story-img"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          6. FINAL CALL TO ACTION
          ==================================================================== */}
      <section className="landing-cta-section" aria-labelledby="cta-heading">
        <div className="landing-cta-panel">
          <h2 id="cta-heading" className="landing-cta-heading">
            Make Room for a Smarter Food Journey.
          </h2>
          <p className="landing-cta-sub">
            Bring food discovery, kitchen creativity and meal planning together with FoodVerse AI.
          </p>

          <div className="landing-cta-actions">
            <button
              type="button"
              className="landing-cta-btn-primary"
              onClick={handleSignupClick}
            >
              Get Started
            </button>
            {!user && (
              <button
                type="button"
                className="landing-cta-secondary-link"
                onClick={handleLoginClick}
              >
                Already have an account? Log in
              </button>
            )}
          </div>
        </div>
      </section>

      {/* ====================================================================
          7. MINIMAL POLISHED FOOTER
          ==================================================================== */}
      <footer className="landing-footer">
        <div className="landing-footer-container">
          <div className="landing-footer-top">
            <div className="landing-footer-about">
              <div className="landing-brand" onClick={handleLogoClick}>
                <div className="landing-brand-leaf" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"
                      fill="#2E7D32"
                    />
                    <path
                      d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.5 12 16.3 12 19c0 1.5-.7 2-2 2H2Z"
                      fill="#7CB342"
                    />
                  </svg>
                </div>
                <span className="landing-brand-title">FoodVerse AI</span>
              </div>
              <p className="landing-footer-desc">
                An integrated culinary intelligence platform combining food recognition, freshness analysis, hygiene monitoring, recipe generation, and meal planning.
              </p>
            </div>

            <div className="landing-footer-links-group">
              <div className="landing-footer-col">
                <span className="landing-footer-col-title">Navigation</span>
                <button
                  type="button"
                  className="landing-footer-link"
                  onClick={() => scrollToSection('features')}
                >
                  Features
                </button>
                <button
                  type="button"
                  className="landing-footer-link"
                  onClick={() => scrollToSection('how-it-works')}
                >
                  How It Works
                </button>
                <button
                  type="button"
                  className="landing-footer-link"
                  onClick={() => scrollToSection('about')}
                >
                  About
                </button>
              </div>

              <div className="landing-footer-col">
                <span className="landing-footer-col-title">Account</span>
                <button
                  type="button"
                  className="landing-footer-link"
                  onClick={handleLoginClick}
                >
                  Login
                </button>
                <button
                  type="button"
                  className="landing-footer-link"
                  onClick={handleSignupClick}
                >
                  Get Started
                </button>
                <button
                  type="button"
                  className="landing-footer-link"
                  onClick={() => onSelectTab('overview')}
                >
                  Dashboard Workspace
                </button>
              </div>
            </div>
          </div>

          <div className="landing-footer-bottom">
            <span>© {new Date().getFullYear()} FoodVerse AI. All rights reserved.</span>
            <span>Mindful Nourishment · Kitchen Safety · Culinary Creativity</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
