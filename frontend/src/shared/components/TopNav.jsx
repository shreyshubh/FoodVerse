import React from 'react';

export default function TopNav({ onToggleMobile, activeTabName }) {
  return (
    <header className="mobile-header-bar" aria-label="Mobile Navigation Bar">
      <div className="mobile-header-brand">
        <div className="brand-leaf-icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path
              d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"
              fill="#7CB342"
            />
            <path
              d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.5 12 16.3 12 19c0 1.5-.7 2-2 2H2Z"
              fill="#9CCC65"
            />
          </svg>
        </div>
        <span className="mobile-brand-name">FoodVerse</span>
      </div>

      <button
        type="button"
        className="mobile-menu-btn"
        onClick={onToggleMobile}
        aria-label="Toggle navigation menu"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
    </header>
  );
}
