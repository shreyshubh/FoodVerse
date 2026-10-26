/**
 * FoodVerse AI — Food Analysis Feature API.
 *
 * Encapsulates the communication contract with the /api/v1/food-analysis endpoint.
 */

import { postFormData, getJson } from '../../shared/api/client';

/**
 * Upload an image and optional serving size for AI recognition and nutrition estimation.
 *
 * @param {File|Blob} imageFile - The food image file.
 * @param {number|null} [servingGrams] - Optional user-specified serving size in grams.
 * @param {object} [options] - Optional settings (e.g., abort signal).
 * @returns {Promise<import('../../types').FoodAnalysisResponse>}
 */
export async function analyzeFoodImage(imageFile, servingGrams = null, options = {}) {
  const formData = new FormData();
  formData.append('image', imageFile);

  if (servingGrams !== null && servingGrams !== undefined && servingGrams > 0) {
    formData.append('serving_grams', String(servingGrams));
  }

  return await postFormData('/api/v1/food-analysis', formData, options);
}

/**
 * Health check to verify backend and service readiness.
 */
export async function checkBackendHealth() {
  return await getJson('/health');
}
