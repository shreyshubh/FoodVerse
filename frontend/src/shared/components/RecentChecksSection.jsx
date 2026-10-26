import React, { useState, useEffect, useCallback } from 'react';
import { fetchJson, BASE_URL } from '../api/client';
import ReportDetailModal from './ReportDetailModal';

export default function RecentChecksSection({
  feature,
  heading = 'Recent activity',
  defaultFallbackImage,
  isFourCol = false,
  refreshKey = 0,
  onSelectTab,
}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);

  const loadRecent = useCallback(async () => {
    try {
      setLoading(true);
      const url = feature
        ? `/api/v1/history?feature=${encodeURIComponent(feature)}&limit=${isFourCol ? 4 : 3}`
        : `/api/v1/history?limit=${isFourCol ? 4 : 3}`;
      const res = await fetchJson(url);
      setItems(res?.items || []);
    } catch (err) {
      console.warn('Could not load recent checks:', err);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [feature, isFourCol]);

  useEffect(() => {
    loadRecent();
  }, [loadRecent, refreshKey]);

  const formatItemMeta = (item) => {
    const parts = [];
    if (item.created_at) {
      try {
        const d = new Date(item.created_at);
        const now = new Date();
        const diffMinutes = Math.floor((now - d) / 60000);
        if (diffMinutes < 2) {
          parts.push('Just now');
        } else if (diffMinutes < 60) {
          parts.push(`${diffMinutes}m ago`);
        } else if (diffMinutes < 1440) {
          parts.push(`${Math.floor(diffMinutes / 60)}h ago`);
        } else {
          parts.push(d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }));
        }
      } catch {
        // Ignore date parse
      }
    }

    if (item.metrics) {
      if (item.metrics.target_calories) {
        parts.push(`${Math.round(item.metrics.target_calories)} kcal`);
      } else if (item.metrics.calories_kcal) {
        parts.push(`${Math.round(item.metrics.calories_kcal)} kcal`);
      } else if (item.metrics.overall_score !== undefined && item.metrics.overall_score !== null) {
        parts.push(`Score: ${item.metrics.overall_score}`);
      } else if (item.metrics.freshness_state) {
        parts.push(item.metrics.freshness_state);
      }
    } else if (item.badge) {
      parts.push(item.badge.replace('_', ' '));
    }

    return parts.join(' • ') || 'Completed';
  };

  const handleViewAll = () => {
    if (onSelectTab) {
      onSelectTab('history');
    } else {
      window.location.hash = 'history';
    }
  };

  return (
    <>
      <div className="recent-section">
        <div className="recent-header-row">
          <h3 className="recent-heading">{heading}</h3>
          <button
            type="button"
            className="recent-view-all"
            onClick={handleViewAll}
            title="View complete history archive"
          >
            View all
          </button>
        </div>

        {loading ? (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: '0.82rem',
              background: 'var(--color-card)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-card-border)',
            }}
          >
            Loading recent checks...
          </div>
        ) : items.length === 0 ? (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: '0.82rem',
              background: 'var(--color-card)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-card-border)',
            }}
          >
            No recent activity recorded yet. Run a check above to see live history here.
          </div>
        ) : (
          <div className={`recent-items-grid ${isFourCol ? 'four-col' : ''}`}>
            {items.map((item) => {
              const fileId = item.media && item.media[0]?.file_id;
              const thumbUrl = fileId ? `${BASE_URL}/api/v1/media/${fileId}` : defaultFallbackImage;

              return (
                <div
                  key={item.id || item._id}
                  className="recent-item-card"
                  onClick={() => setSelectedReport(item)}
                  style={{ cursor: 'pointer' }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setSelectedReport(item);
                    }
                  }}
                  title="Click to inspect report details"
                >
                  <img
                    src={thumbUrl}
                    alt={item.title || 'Recent check'}
                    className="recent-thumb"
                    onError={(e) => {
                      if (defaultFallbackImage && e.currentTarget.src !== defaultFallbackImage) {
                        e.currentTarget.src = defaultFallbackImage;
                      }
                    }}
                  />
                  <div className="recent-info">
                    <span className="recent-name">{item.title || 'Analysis Report'}</span>
                    <span className="recent-meta">{formatItemMeta(item)}</span>
                  </div>
                  <span className="recent-chevron" aria-hidden="true">
                    ›
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Interactive Report Inspection Modal */}
      {selectedReport && (
        <ReportDetailModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </>
  );
}
