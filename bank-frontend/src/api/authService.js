// Talks to the FastAPI backend (banking-api) on port 8000.
// Use the "localhost" hostname (not the 127.0.0.1 literal): it resolves to both
// IPv4 and IPv6 so the browser can fall back between them, which keeps the whole
// app on one consistent host.
const API_URL = 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'bank_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

async function request(path, options = {}) {
  const token = getToken()
  let res
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new Error("Can't reach the server. Is the backend running on port 8000?")
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    // FastAPI puts the message in "detail" (a string, or a list for validation errors)
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail
    const err = new Error(detail || `Request failed (${res.status})`)
    err.status = res.status // lets callers tell e.g. 409 "already pending" from a real error
    throw err
  }
  return data
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  localStorage.setItem(TOKEN_KEY, data.token)
  return data.user
}

export async function getCurrentUser() {
  if (!getToken()) return null
  try {
    return await request('/auth/me')
  } catch {
    localStorage.removeItem(TOKEN_KEY) // token no longer valid (e.g. server restarted)
    return null
  }
}

export async function logout() {
  try {
    await request('/auth/logout', { method: 'POST' })
  } finally {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export async function getCustomer(customerId) {
  return request(`/customers/${customerId}`)
}

// ---------- Banking (uses the team's existing API) ----------

// All accounts that belong to this customer
export async function getMyAccounts(customerId) {
  return request(`/accounts/?customer_id=${customerId}`)
}

// Update name / phone.  PUT /api/v1/customers/{id}
export async function updateCustomer(customerId, changes) {
  return request(`/customers/${customerId}`, {
    method: 'PUT',
    body: JSON.stringify(changes),
  })
}

// Every account's number + name, WITHOUT balances (used to show "ACC002 · Jane Smith").
// Customers aren't allowed to list other people's full accounts any more.
export async function getAllAccounts() {
  return request('/accounts/directory')
}

// Find an account by its number (e.g. "ACC002") so people can send money
// using the number printed on the account, not the internal id
export async function findAccountByNumber(accountNumber) {
  const accounts = await request('/accounts/directory')
  const wanted = accountNumber.trim().toUpperCase()
  return accounts.find((a) => a.account_number.toUpperCase() === wanted) || null
}

// Move money.  POST /api/v1/transactions/transfer
export async function sendMoney(fromAccountId, toAccountId, amount) {
  return request('/transactions/transfer', {
    method: 'POST',
    body: JSON.stringify({ from_account_id: fromAccountId, to_account_id: toAccountId, amount }),
  })
}

// ---------- Account applications (public: no login needed) ----------

// Active branches for the application form's dropdown
export async function getPublicBranches() {
  return request('/applications/branches')
}

// Submit a request to open an account. The backend holds it as PENDING until an
// admin approves or declines it. Throws Error(message) on 400/409/429 etc.
export async function submitApplication(payload) {
  return request('/applications/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// ---------- Account applications (admin: needs an admin login token) ----------

// All applications, or just one status (e.g. 'PENDING'). Admin only.
export async function getApplications(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request(`/applications/${query}`)
}

// Approve an application -> provisions customer + account + login. Admin only.
export async function approveApplication(id, openingBalance) {
  return request(`/applications/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ opening_balance: openingBalance }),
  })
}

// Decline an application, with an optional reason kept on the record. Admin only.
export async function declineApplication(id, note) {
  return request(`/applications/${id}/decline`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  })
}

// Transactions that touch any of these accounts, newest first
export async function getMyTransactions(accountIds) {
  const all = await request('/transactions/')
  return all
    .filter((t) => accountIds.includes(t.from_account_id) || accountIds.includes(t.to_account_id))
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
}