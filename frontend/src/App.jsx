import React, { useState, useEffect } from 'react';
import Sidebar from './shared/components/Sidebar';
import TopNav from './shared/components/TopNav';
import OverviewPage from './features/overview/OverviewPage';
import FoodAnalysisPage from './features/food-analysis/FoodAnalysisPage';
import FreshnessDetectorPage from './features/freshness/FreshnessDetectorPage';
import HygieneMonitorPage from './features/hygiene/HygieneMonitorPage';
import SmartKitchenPage from './features/smart-kitchen/SmartKitchenPage';
import MealPlannerPage from './features/meal-planner/MealPlannerPage';
import HistoryPage from './features/history/HistoryPage';
import AuthModal from './shared/components/AuthModal';
import ProfileModal from './shared/components/ProfileModal';
import { checkBackendHealth } from './features/food-analysis/foodAnalysisApi';
import { getStoredUser, getAuthToken } from './shared/api/client';
import { getCurrentUser, logoutUser } from './shared/api/authApi';

const VALID_TABS = [
  'overview',
  'food_recognition',
  'freshness',
  'hygiene',
  'smart_kitchen',
  'meal_planner',
  'history',
];

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);

  // User authentication state
  const [user, setUser] = useState(() => getStoredUser());
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    checkBackendHealth()
      .then((data) => setHealthStatus(data))
      .catch(() => setHealthStatus({ status: 'offline' }));

    // If an auth token exists, fetch latest user profile & stats from backend
    if (getAuthToken()) {
      getCurrentUser()
        .then((userData) => setUser(userData))
        .catch(() => {
          // Token may be invalid or expired; leave guest state
        });
    }

    // Sync with URL hash
    const hash = window.location.hash.replace('#', '');
    if (VALID_TABS.includes(hash)) {
      setActiveTab(hash);
    }

    const handleHashChange = () => {
      const newHash = window.location.hash.replace('#', '');
      if (VALID_TABS.includes(newHash)) {
        setActiveTab(newHash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleSelectTab = (tabId) => {
    setActiveTab(tabId);
    window.location.hash = tabId;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAuthSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
    setIsProfileOpen(false);
  };

  return (
    <div className="app-shell">
      {/* Persistent Left Sidebar on Desktop / Drawer on Mobile */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
      />

      {/* Main App Work Area */}
      <div className="app-main-wrapper">
        {/* Mobile Header Bar */}
        <TopNav
          onToggleMobile={() => setMobileOpen((prev) => !prev)}
          activeTabName={activeTab}
        />

        {/* Content Viewport Canvas */}
        <main className="app-content-canvas" id="main-content">
          {activeTab === 'overview' && (
            <OverviewPage onSelectTab={handleSelectTab} />
          )}
          {activeTab === 'food_recognition' && (
            <FoodAnalysisPage onSelectTab={handleSelectTab} />
          )}
          {activeTab === 'freshness' && (
            <FreshnessDetectorPage onSelectTab={handleSelectTab} />
          )}
          {activeTab === 'hygiene' && (
            <HygieneMonitorPage onSelectTab={handleSelectTab} />
          )}
          {activeTab === 'smart_kitchen' && (
            <SmartKitchenPage onSelectTab={handleSelectTab} />
          )}
          {activeTab === 'meal_planner' && (
            <MealPlannerPage onSelectTab={handleSelectTab} />
          )}
          {activeTab === 'history' && (
            <HistoryPage onSelectTab={handleSelectTab} />
          )}
        </main>
      </div>

      {/* Auth Modal (Login / Sign Up) */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Profile Details Modal */}
      <ProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        user={user}
        onLogout={handleLogout}
      />
    </div>
  );
}
