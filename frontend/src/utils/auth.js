export const AUTH_STORAGE_KEY = 'careerbloom_auth';

export const getStoredAuth = () => {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
};

export const saveAuth = (authPayload) => {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authPayload));
};

export const clearAuth = () => {
  localStorage.removeItem(AUTH_STORAGE_KEY);
};

export const buildAuthHeaders = (token, extraHeaders = {}) => {
  const headers = { ...extraHeaders };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
};
