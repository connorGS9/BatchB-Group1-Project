import { useState } from 'react'
import { findAccountByNumber, sendMoney } from '../api/authService.js'
import { money } from './format.js'

// Two steps: fill in the form -> review -> confirm. Money only moves on "Confirm".
export default function SendMoney({ accounts, onSent }) {
  const active = accounts.filter((a) => a.is_active)
  const [fromId, setFromId] = useState(active[0]?.id ?? '')
  const [toNumber, setToNumber] = useState('')
  const [amount, setAmount] = useState('')
  const [review, setReview] = useState(null) // { to, amount } while confirming
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [busy, setBusy] = useState(false)

  const from = accounts.find((a) => a.id === Number(fromId))

  async function handleReview(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    const value = Math.round(Number(amount) * 100) / 100
    if (!from) return setError('Choose the account to send from.')
    if (!toNumber.trim()) return setError('Enter the account number to send to, e.g. ACC002.')
    if (!value || value <= 0) return setError('Enter an amount greater than $0.')
    if (value > from.balance) return setError(`You only have ${money(from.balance)} in ${from.account_number}.`)

    setBusy(true)
    try {
      const to = await findAccountByNumber(toNumber)
      if (!to) return setError(`No account found with number ${toNumber.trim().toUpperCase()}.`)
      if (to.id === from.id) return setError("You can't send money to the same account.")
      if (!to.is_active) return setError(`Account ${to.account_number} is closed and can't receive money.`)
      setReview({ to, amount: value })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleConfirm() {
    setBusy(true)
    setError('')
    try {
      await sendMoney(from.id, review.to.id, review.amount)
      setSuccess(`Sent ${money(review.amount)} to ${review.to.account_number}.`)
      setReview(null)
      setToNumber('')
      setAmount('')
      onSent() // reload balances + activity
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (active.length === 0) {
    return (
      <section className="panel">
        <h2>Send money</h2>
        <p className="muted">You need an active account to send money.</p>
      </section>
    )
  }

  return (
    <section className="panel">
      <h2>Send money</h2>

      {review ? (
        <div className="review">
          <p>
            Send <strong>{money(review.amount)}</strong> from <strong>{from.account_number}</strong> to{' '}
            <strong>{review.to.account_number}</strong> ({review.to.first_name} {review.to.last_name})?
          </p>
          <p className="muted">
            {from.account_number} balance after: {money(from.balance - review.amount)}
          </p>
          {error && <p className="error" role="alert">{error}</p>}
          <div className="button-row">
            <button type="button" className="primary" onClick={handleConfirm} disabled={busy}>
              {busy ? 'Sending…' : 'Confirm and send'}
            </button>
            <button type="button" className="secondary" onClick={() => setReview(null)} disabled={busy}>
              Back
            </button>
          </div>
        </div>
      ) : (
        <form className="stack" onSubmit={handleReview} noValidate>
          <label htmlFor="from">From</label>
          <select id="from" value={fromId} onChange={(e) => setFromId(e.target.value)}>
            {active.map((a) => (
              <option key={a.id} value={a.id}>
                {a.account_number} · {money(a.balance)}
              </option>
            ))}
          </select>

          <label htmlFor="to">To account number</label>
          <input id="to" placeholder="ACC002" value={toNumber} onChange={(e) => setToNumber(e.target.value)} />

          <label htmlFor="amount">Amount (USD)</label>
          <input
            id="amount"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />

          {error && <p className="error" role="alert">{error}</p>}
          {success && <p className="success" role="status">{success}</p>}

          <button type="submit" className="primary" disabled={busy}>
            {busy ? 'Checking…' : 'Review transfer'}
          </button>
        </form>
      )}
    </section>
  )
}