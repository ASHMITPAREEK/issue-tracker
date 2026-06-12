const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('token')
}

export async function apiRequest(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }

  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { error: text }
    }
  }

  if (!res.ok) {
    const message = data?.error || data?.detail || `Request failed (${res.status})`
    const error = new Error(typeof message === 'string' ? message : JSON.stringify(message))
    error.status = res.status
    throw error
  }

  return data
}

export const api = {
  register: (payload) => apiRequest('/auth/register', { method: 'POST', body: payload, auth: false }),
  login: (payload) => apiRequest('/auth/login', { method: 'POST', body: payload, auth: false }),
  logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  me: () => apiRequest('/auth/me'),
  users: () => apiRequest('/auth/users'),

  getDashboardStats: () => apiRequest('/dashboard/stats'),

  listProjects: (includeArchived = false) =>
    apiRequest(`/projects?include_archived=${includeArchived}`),
  getProject: (id) => apiRequest(`/projects/${id}`),
  createProject: (payload) => apiRequest('/projects', { method: 'POST', body: payload }),
  updateProject: (id, payload) => apiRequest(`/projects/${id}`, { method: 'PATCH', body: payload }),
  archiveProject: (id) => apiRequest(`/projects/${id}/archive`, { method: 'POST' }),
  unarchiveProject: (id) => apiRequest(`/projects/${id}/unarchive`, { method: 'POST' }),

  listIssues: (params = {}) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') query.set(key, value)
    })
    const qs = query.toString()
    return apiRequest(`/issues${qs ? `?${qs}` : ''}`)
  },
  createIssue: (payload) => apiRequest('/issues', { method: 'POST', body: payload }),
  updateIssue: (id, payload) => apiRequest(`/issues/${id}`, { method: 'PATCH', body: payload }),
  deleteIssue: (id) => apiRequest(`/issues/${id}`, { method: 'DELETE' }),
}
