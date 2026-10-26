/**
 * FoodVerse AI — History API Client.
 *
 * Scoped to the verified backend session owner.
 */
import { getJson, deleteJson } from '../../shared/api/client';

export async function fetchHistorySummary() {
  const res = await getJson('/api/v1/history/summary');
  return res.data;
}

export async function fetchHistoryReports({ feature, status, limit = 10, cursor = null } = {}) {
  const query = new URLSearchParams();
  if (feature) query.append('feature', feature);
  if (status) query.append('status', status);
  if (limit) query.append('limit', String(limit));
  if (cursor) query.append('cursor', cursor);

  const endpoint = `/api/v1/history?${query.toString()}`;
  return await getJson(endpoint);
}

export async function fetchHistoryReport(reportId) {
  const res = await getJson(`/api/v1/history/${reportId}`);
  return res.report;
}

export async function deleteHistoryReport(reportId) {
  return await deleteJson(`/api/v1/history/${reportId}`);
}
