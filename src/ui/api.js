const BASE_URL = 'http://127.0.0.1:8000/api'

async function request(path, options = {}) {
  let response
  try { response = await fetch(`${BASE_URL}${path}`, options) }
  catch { throw new Error('The local backend is unavailable. Start the FastAPI server and try again.') }
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new Error(payload?.detail || 'The backend returned an unexpected response.')
  return payload
}

export const api = {
  getEmails: (filter) => request(filter === 'Inbox' ? '/emails' : filter === 'Attachments' ? '/emails/attachments' : filter === 'Important' ? '/emails/important' : filter === 'Starred' ? '/emails/starred' : `/categories/${encodeURIComponent(filter)}`),
  getEmail: (id) => request(`/emails/${encodeURIComponent(id)}`),
  sync: () => request('/sync', { method: 'POST' }),
  ask: (query) => request('/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) }),
}
