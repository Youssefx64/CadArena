import axios from 'axios';

const client = axios.create({
  baseURL: '',
  timeout: 15000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

function extractError(err) {
  const detail = err.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || String(d)).join(', ');
  if (detail) return String(detail);
  if (err.message?.includes('Network Error')) return 'Cannot connect to server. Check the backend is running.';
  return err.message || 'An unexpected error occurred.';
}

async function call(fn) {
  try {
    return (await fn()).data;
  } catch (err) {
    throw new Error(extractError(err));
  }
}

const authApi = {
  register: (name, email, password) =>
    call(() => client.post('/api/v1/auth/register', { name, email, password })),

  login: (email, password) =>
    call(() => client.post('/api/v1/auth/login', { email, password })),

  logout: () => call(() => client.post('/api/v1/auth/logout')),

  getCurrentUser: () => call(() => client.get('/api/v1/auth/me')),

  getProfile: () => call(() => client.get('/api/v1/profile/me')),

  updateProfile: (data) => call(() => client.patch('/api/v1/profile/me', data)),

  uploadAvatar: (file) => {
    const form = new FormData();
    form.append('file', file);
    return call(() =>
      client.post('/api/v1/profile/me/avatar', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000,
      })
    );
  },

  deleteAvatar: () => call(() => client.delete('/api/v1/profile/me/avatar')),
};

export default authApi;
