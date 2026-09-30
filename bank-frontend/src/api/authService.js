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
    throw new Error(detail || `Request failed (${res.status})`)
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

// Transactions that touch any of these accounts, newest first
export async function getMyTransactions(accountIds) {
  const all = await request('/transactions/')
  return all
    .filter((t) => accountIds.includes(t.from_account_id) || accountIds.includes(t.to_account_id))
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
}