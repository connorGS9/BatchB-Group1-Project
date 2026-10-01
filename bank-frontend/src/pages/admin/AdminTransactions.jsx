import { useCallback, useEffect, useState } from 'react'
import { getTransactions } from '../../api/authService.js'
import { money } from '../../components/format.js'

const TYPES = ['TRANSFER', 'DEPOSIT', 'WITHDRAWAL']

export default function AdminTransactions() {
  const [txns, setTxns] = useState([])
  const [filters, setFilters] = useState({ start_date: '', type: '' })
  const [error, setError] = useState('')

  const load = useCallback(async (f = filters) => {
    try {
      setTxns(await getTransactions(f))
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [filters])

  useEffect(() => {
    load({ start_date: '', type: '' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function setFilter(field) {
    return (e) => setFilters((f) => ({ ...f, [field]: e.target.value }))
  }

  return (
    <>
      <h1>Transaction ledger</h1>

      <section className="panel">
        <div className="admin-toolbar">
          <div className="fld"><label htmlFor="t-start">Start date</label><input id="t-start" type="date" value={filters.start_date} onChange={setFilter('start_date')} /></div>
          <div className="fld"><label htmlFor="t-type">Type</label>
            <select id="t-type" value={filters.type} onChange={setFilter('type')}>
              <option value="">any</option>
              {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="button-row">
            <button type="button" className="primary" onClick={() => load()}>Filter</button>
            <button type="button" className="secondary" onClick={() => { const c = { start_date: '', type: '' }; setFilters(c); load(c) }}>Clear</button>
          </div>
        </div>

        {error && <p className="error" role="alert">{error}</p>}

        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>From</th><th>To</th><th className="num">Amount</th><th>Type</th><th>When</th></tr>
          </thead>
          <tbody>
            {txns.length === 0 ? (
              <tr><td colSpan={6} className="admin-empty">No transactions match.</td></tr>
            ) : txns.map((t) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>#{t.from_account_id}</td>
                <td>#{t.to_account_id}</td>
                <td className="num">{money(t.amount)}</td>
                <td><span className="tag tag-ok">{t.type}</span></td>
                <td>{new Date(t.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}
