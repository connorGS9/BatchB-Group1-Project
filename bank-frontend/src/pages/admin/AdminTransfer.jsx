import { useState } from 'react'
import { sendMoney } from '../../api/authService.js'
import { money } from '../../components/format.js'

// Admin money movement, by account id (mirrors the old dashboard's Transfer).
export default function AdminTransfer() {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function submit(e) {
    e.preventDefault()
    setError('')
    setMsg('')
    const value = Math.round(Number(amount) * 100) / 100
    if (!from || !to) return setError('Enter both account IDs.')
    if (Number(from) === Number(to)) return setError('From and To must be different accounts.')
    if (!value || value <= 0) return setError('Enter an amount greater than $0.')
    setBusy(true)
    try {
      const t = await sendMoney(Number(from), Number(to), value)
      setMsg(`Transfer #${t.id}: ${money(t.amount)} from account #${t.from_account_id} → #${t.to_account_id}`)
      setFrom('')
      setTo('')
      setAmount('')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1>Transfer money</h1>

      <section className="panel">
        <p className="muted">Move funds between accounts by their ID.</p>
        <form className="admin-form" onSubmit={submit}>
          <div className="fld"><label htmlFor="x-from">From account ID</label><input id="x-from" type="number" min="1" value={from} onChange={(e) => setFrom(e.target.value)} required /></div>
          <div className="fld"><label htmlFor="x-to">To account ID</label><input id="x-to" type="number" min="1" value={to} onChange={(e) => setTo(e.target.value)} required /></div>
          <div className="fld"><label htmlFor="x-amt">Amount</label><input id="x-amt" type="number" min="0.01" step="0.01" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} required /></div>
          <div className="button-row">
            <button type="submit" className="primary" disabled={busy}>{busy ? 'Sending…' : 'Send transfer'}</button>
          </div>
        </form>
        {msg && <p className="success" role="status">{msg}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>
    </>
  )
}
