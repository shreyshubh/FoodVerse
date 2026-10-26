import React from 'react';

const NAV_ITEMS = [
  {
    id: 'overview',
    label: 'Overview',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
        <polyline points="9 22 9 12 15 12 15 22"></polyline>
      </svg>
    ),
  },
  {
    id: 'food_recognition',
    label: 'Food Recognition',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 7V4h3M20 7V4h-3M4 17v3h3M20 17v3h-3"></path>
        <circle cx="12" cy="12" r="3.5"></circle>
      </svg>
    ),
  },
  {
    id: 'freshness',
    label: 'Freshness Detector',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"></path>
      </svg>
    ),
  },
  {
    id: 'hygiene',
    label: 'Hygiene Monitor',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        <path d="m9 12 2 2 4-4"></path>
      </svg>
    ),
  },
  {
    id: 'smart_kitchen',
    label: 'Smart Kitchen',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z"></path>
        <line x1="6" y1="17" x2="18" y2="17"></line>
      </svg>
    ),
  },
  {
    id: 'meal_planner',
    label: 'Meal Planner',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
        <line x1="16" y1="2" x2="16" y2="6"></line>
        <line x1="8" y1="2" x2="8" y2="6"></line>
        <line x1="3" y1="10" x2="21" y2="10"></line>
      </svg>
    ),
  },
  {
    id: 'history',
    label: 'History & Reports',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
      </svg>
    ),
  },
];

export default function Sidebar({
  activeTab,
  onSelectTab,
  mobileOpen,
  onCloseMobile,
  user,
  onOpenAuth,
  onOpenProfile,
}) {
  return (
    <>
      {/* Backdrop for mobile drawer */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${mobileOpen ? 'mobile-open' : ''}`} aria-label="Main Navigation">
        {/* Brand Header */}
        <div className="sidebar-brand">
          <div
            className="brand-logo-wrap"
            onClick={() => {
              if (onCloseMobile) onCloseMobile();
              onSelectTab('landing');
            }}
            style={{ cursor: 'pointer' }}
            title="Go to FoodVerse Homepage"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                if (onCloseMobile) onCloseMobile();
                onSelectTab('landing');
              }
            }}
          >
            <div className="brand-leaf-icon" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
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
            <span className="brand-name">FoodVerse</span>
          </div>

          {/* Close button on mobile */}
          {mobileOpen && (
            <button
              type="button"
              className="mobile-close-btn"
              onClick={onCloseMobile}
              aria-label="Close menu"
            >
              ✕
            </button>
          )}
        </div>

        {/* Navigation Destination List */}
        <nav className="sidebar-nav">
          <ul className="nav-list">
            {NAV_ITEMS.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <li key={item.id} className="nav-item">
                  <button
                    type="button"
                    id={`nav-btn-${item.id}`}
                    className={`nav-button ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      onSelectTab(item.id);
                      if (onCloseMobile) onCloseMobile();
                    }}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Profile Section Anchored at Bottom */}
        <div className="sidebar-profile-section">
          <div className="profile-separator" />
          {user ? (
            <div
              className="user-profile-row"
              onClick={onOpenProfile}
              role="button"
              tabIndex={0}
              title="Click to view your personal account and activity details"
              style={{ cursor: 'pointer' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onOpenProfile();
                }
              }}
            >
              <div className="user-avatar-circle" aria-label="User Avatar">
                <span>{user.name ? user.name.charAt(0).toUpperCase() : 'U'}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, flex: 1 }}>
                <span className="user-profile-name" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user.name}
                </span>
                <span style={{ fontSize: '0.68rem', color: '#9E9E9E', marginTop: 1 }}>View Profile</span>
              </div>
            </div>
          ) : (
            <div
              className="user-profile-row"
              onClick={onOpenAuth}
              role="button"
              tabIndex={0}
              title="Click to Log In or Create an Account"
              style={{ cursor: 'pointer' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onOpenAuth();
                }
              }}
            >
              <div
                className="user-avatar-circle"
                style={{ background: 'rgba(255, 255, 255, 0.15)', color: '#FFF' }}
                aria-label="Guest Avatar"
              >
                <span>👤</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, flex: 1 }}>
                <span className="user-profile-name" style={{ fontSize: '0.82rem' }}>
                  Sign In / Register
                </span>
                <span style={{ fontSize: '0.68rem', color: '#81C784', marginTop: 1 }}>Sync your data</span>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
