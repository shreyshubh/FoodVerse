/**
 * FoodVerse AI — Authentication API client.
 */
import { postJson, fetchJson, setAuthSession, clearAuthSession } from './client';

export async function signupUser({ name, email, birthday, password }) {
  const data = await postJson('/api/v1/auth/signup', {
    name,
    email,
    birthday,
    password,
  });
  if (data?.token && data?.user) {
    setAuthSession(data.token, data.user);
  }
  return data;
}

export async function loginUser({ email, password }) {
  const data = await postJson('/api/v1/auth/login', {
    email,
    password,
  });
  if (data?.token && data?.user) {
    setAuthSession(data.token, data.user);
  }
  return data;
}

export async function getCurrentUser() {
  const user = await fetchJson('/api/v1/auth/me');
  return user;
}

export async function logoutUser() {
  try {
    await postJson('/api/v1/auth/logout', {});
  } finally {
    clearAuthSession();
  }
}
