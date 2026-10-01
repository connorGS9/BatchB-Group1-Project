import { useState } from 'react'
import { sendMoney } from '../api/authService.js'
import { money } from './format.js'

// A small "glance + act" dashboard shown above the detailed tabs on the
// customer home: quick stats, a 30-day money-flow bar, and one-tap pay for
// recent recipients. Everything here is backed by the real API (same calls the
// tabs use).

const DAY_MS = 24 * 60 * 60 * 1000
const QUICK_AMOUNTS = [10, 25, 50]

// Total moved in / out of the customer's accounts over the last `days` days.
function flowSince(transactions, myIds, days) {
  const cutoff = Date.now() - days * DAY_MS
  let incoming = 0
  let outgoing = 0
  for (const t of transactions) {
    if (new Date(t.timestamp).getTime() < cutoff) continue
    if (myIds.includes(t.to_account_id)) incoming += t.amount
    if (myIds.includes(t.from_account_id)) outgoing += t.amount
  }
  return { incoming, outgoing }
}

function initials(first, last) {
  return `${first?.[0] ?? ''}${last?.[0] ?? ''}`.toUpperCase() || '?'
}

// Accounts the customer has actually paid or been paid by, newest first, resolved
// to their public directory record. Inactive accounts (can't receive) are dropped.
function recentRecipients(transactions, myIds, directory) {
  const seen = new Set()
  const out = []
  for (const t of transactions) { // transactions arrive newest-first
    const otherId = myIds.includes(t.from_account_id)
      ? t.to_account_id
      : myIds.includes(t.to_account_id)
        ? t.from_account_id
        : null
    if (otherId == null || myIds.includes(otherId) || seen.has(otherId)) continue
    seen.add(otherId)
    const account = directory.find((a) => a.id === otherId)
    if (account && account.is_active) out.push(account)
  }
  return out
}

export default function Dashboard({ accounts, directory, transactions, onDone }) {
  const myIds = accounts.map((a) => a.id)
  const active = accounts.filter((a) => a.is_active)
  const total = accounts.reduce((sum, a) => sum + a.balance, 0)
  const { incoming, outgoing } = flowSince(transactions, myIds, 30)
  const flowMax = Math.max(incoming, outgoing, 1)

  // Recent recipients: only accounts this customer has actually transacted with
  // (most recent first), resolved to a name via the directory. We never surface
  // the full directory here — just people already in the customer's own history.
  const recipients = recentRecipients(transactions, myIds, directory).slice(0, 6)

  const [fromId, setFromId] = useState(active[0]?.id ?? '')
  const [recipientId, setRecipientId] = useState(null)
  const [amount, setAmount] = useState('')
  const [pending, setPending] = useState(false) // waiting for the confirm click
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const from = accounts.find((a) => a.id === Number(fromId))
  const recipient = recipients.find((a) => a.id === recipientId)
  const value = Math.round(Number(amount) * 100) / 100

  function reset() {
    setPending(false)
    setRecipientId(null)
    setAmount('')
  }

  function validate() {
    if (!from) return 'Choose the account to send from.'
    if (!recipient) return 'Pick someone to pay.'
    if (!value || value <= 0) return 'Enter an amount greater than $0.'
    if (value > from.balance) return `You only have ${money(from.balance)} in ${from.account_number}.`
    return ''
  }

  function handleSend() {
    setSuccess('')
    const problem = validate()
    if (problem) {
      setError(problem)
      setPending(false)
      return
    }
    setError('')
    setPending(true) // show the confirm button
  }

  async function handleConfirm() {
    setBusy(true)
    setError('')
    try {
      await sendMoney(from.id, recipient.id, value)
      setSuccess(`Sent ${money(value)} to ${recipient.first_name}.`)
      reset()
      onDone() // refresh balances + activity everywhere
    } catch (err) {
      setError(err.message)
      setPending(false)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="dashboard">
      <ul className="stat-tiles">
        <li className="stat">
          <span className="stat-label">Accounts</span>
          <span className="stat-value">{accounts.length}</span>
        </li>
        <li className="stat">
          <span className="stat-label">Total balance</span>
          <span className="stat-value">{money(total)}</span>
        </li>
        <li className="stat">
          <span className="stat-label">In · 30 days</span>
          <span className="stat-value in">{money(incoming)}</span>
        </li>
        <li className="stat">
          <span className="stat-label">Out · 30 days</span>
          <span className="stat-value">{money(outgoing)}</span>
        </li>
      </ul>

      <section className="panel flow-card">
        <h2>Money flow · last 30 days</h2>
        {incoming === 0 && outgoing === 0 ? (
          <p className="muted">No money has moved in the last 30 days.</p>
        ) : (
          <div className="flow">
            <div className="flow-row">
              <span className="flow-tag">In</span>
              <span className="flow-track">
                <span className="flow-bar in" style={{ width: `${(incoming / flowMax) * 100}%` }} />
              </span>
              <span className="flow-amt">{money(incoming)}</span>
            </div>
            <div className="flow-row">
              <span className="flow-tag">Out</span>
              <span className="flow-track">
                <span className="flow-bar out" style={{ width: `${(outgoing / flowMax) * 100}%` }} />
              </span>
              <span className="flow-amt">{money(outgoing)}</span>
            </div>
          </div>
        )}
      </section>

      <section className="panel pay-card">
        <h2>Recent recipients</h2>
        {active.length === 0 ? (
          <p className="muted">You need an active account to send money.</p>
        ) : recipients.length === 0 ? (
          <p className="muted">
            No recent recipients yet. Pay a new account from the <strong>Send money</strong> tab, and they'll show up here.
          </p>
        ) : (
          <>
            <p className="pay-hint">Tap someone you've paid before, pick an amount, send.</p>
            <ul className="friend-chips">
              {recipients.map((r) => (
                <li key={r.id}>
                  <button
                    type="button"
                    className={r.id === recipientId ? 'chip sel' : 'chip'}
                    onClick={() => {
                      setRecipientId(r.id)
                      setPending(false)
                      setError('')
                    }}
                    aria-pressed={r.id === recipientId}
                  >
                    <span className="chip-avatar" aria-hidden="true">{initials(r.first_name, r.last_name)}</span>
                    <span className="chip-name">{r.first_name}</span>
                  </button>
                </li>
              ))}
            </ul>

            <div className="pay-controls">
              <select
                aria-label="Pay from account"
                value={fromId}
                onChange={(e) => { setFromId(e.target.value); setPending(false) }}
              >
                {active.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.account_number} · {money(a.balance)}
                  </option>
                ))}
              </select>

              <div className="amount-picks">
                {QUICK_AMOUNTS.map((q) => (
                  <button
                    type="button"
                    key={q}
                    className={value === q ? 'pick on' : 'pick'}
                    onClick={() => { setAmount(String(q)); setPending(false) }}
                  >
                    ${q}
                  </button>
                ))}
                <input
                  type="number"
                  inputMode="decimal"
                  min="0.01"
                  step="0.01"
                  placeholder="Other"
                  value={amount}
                  onChange={(e) => { setAmount(e.target.value); setPending(false) }}
                  aria-label="Custom amount"
                />
              </div>
            </div>

            {error && <p className="error" role="alert">{error}</p>}
            {success && <p className="success" role="status">{success}</p>}

            {pending ? (
              <div className="button-row">
                <button type="button" className="primary" onClick={handleConfirm} disabled={busy}>
                  {busy ? 'Sending…' : `Confirm: ${money(value)} → ${recipient?.first_name}`}
                </button>
                <button type="button" className="secondary" onClick={() => setPending(false)} disabled={busy}>
                  Cancel
                </button>
              </div>
            ) : (
              <button type="button" className="primary pay-send" onClick={handleSend}>
                {recipient && value > 0 ? `Send ${money(value)} to ${recipient.first_name}` : 'Send money'}
              </button>
            )}
          </>
        )}
      </section>
    </div>
  )
}
