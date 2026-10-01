import { useCallback, useEffect, useState } from 'react'
import {
  createAccount, deactivateAccount, getAccounts, getBranches, updateAccount,
} from '../../api/authService.js'
import { money } from '../../components/format.js'

const EMPTY = { customer_id: '', first_name: '', last_name: '', balance: '0', branch_id: '' }

export default function AdminAccounts() {
  const [accounts, setAccounts] = useState([])
  const [branches, setBranches] = useState([])
  const [filters, setFilters] = useState({ customer_id: '', branch_id: '', min_balance: '' })
  const [form, setForm] = useState(EMPTY)
  const [editingId, setEditingId] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [confirmingId, setConfirmingId] = useState(null) // row awaiting deactivate confirm

  const load = useCallback(async (f = filters) => {
    try {
      setAccounts(await getAccounts(f))
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [filters])

  useEffect(() => {
    getBranches()
      .then((bs) => {
        setBranches(bs)
        setForm((prev) => ({ ...prev, branch_id: bs[0]?.id ?? '' }))
      })
      .catch((e) => setError(e.message))
    load({ customer_id: '', branch_id: '', min_balance: '' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }
  function setFilter(field) {
    return (e) => setFilters((f) => ({ ...f, [field]: e.target.value }))
  }

  function resetForm() {
    setEditingId(null)
    setForm({ ...EMPTY, branch_id: branches[0]?.id ?? '' })
  }

  function startEdit(a) {
    setEditingId(a.id)
    setForm({
      customer_id: String(a.customer_id), first_name: a.first_name, last_name: a.last_name,
      balance: String(a.balance), branch_id: a.branch_id,
    })
    setMsg('')
    setError('')
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMsg('')
    try {
      if (editingId) {
        const a = await updateAccount(editingId, {
          first_name: form.first_name.trim(), last_name: form.last_name.trim(),
          branch_id: Number(form.branch_id),
        })
        setMsg(`Updated account #${a.id}`)
      } else {
        const a = await createAccount({
          customer_id: Number(form.customer_id), first_name: form.first_name.trim(),
          last_name: form.last_name.trim(), balance: Number(form.balance) || 0,
          branch_id: Number(form.branch_id),
        })
        setMsg(`Opened account ${a.account_number} for customer #${a.customer_id}`)
      }
      resetForm()
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function deactivate(a) {
    setError('')
    setConfirmingId(null)
    try {
      await deactivateAccount(a.id)
      setMsg(`Deactivated account ${a.account_number}`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const editing = editingId != null

  return (
    <>
      <h1>Accounts</h1>

      <section className="panel">
        <h2>{editing ? `Edit account #${editingId}` : 'Open a new account'}</h2>
        <form className="admin-form" onSubmit={submit}>
          <div className="fld">
            <label htmlFor="a-cust">Customer ID</label>
            <input id="a-cust" type="number" min="1" value={form.customer_id} onChange={set('customer_id')} disabled={editing} required />
          </div>
          <div className="fld">
            <label htmlFor="a-first">First name</label>
            <input id="a-first" value={form.first_name} onChange={set('first_name')} required />
          </div>
          <div className="fld">
            <label htmlFor="a-last">Last name</label>
            <input id="a-last" value={form.last_name} onChange={set('last_name')} required />
          </div>
          <div className="fld">
            <label htmlFor="a-bal">Opening balance</label>
            <input id="a-bal" type="number" min="0" step="0.01" value={form.balance} onChange={set('balance')} disabled={editing} title={editing ? 'Balance changes via transfers' : undefined} />
          </div>
          <div className="fld">
            <label htmlFor="a-branch">Branch</label>
            <select id="a-branch" value={form.branch_id} onChange={set('branch_id')}>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div className="button-row">
            <button type="submit" className="primary" disabled={busy}>
              {busy ? 'Saving…' : editing ? 'Save changes' : 'Open account'}
            </button>
            {editing && <button type="button" className="secondary" onClick={resetForm} disabled={busy}>Cancel</button>}
          </div>
        </form>
        {msg && <p className="success" role="status">{msg}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>

      <section className="panel">
        <div className="admin-toolbar">
          <div className="fld"><label htmlFor="f-cust">Customer ID</label><input id="f-cust" type="number" placeholder="any" value={filters.customer_id} onChange={setFilter('customer_id')} /></div>
          <div className="fld"><label htmlFor="f-branch">Branch</label>
            <select id="f-branch" value={filters.branch_id} onChange={setFilter('branch_id')}>
              <option value="">any</option>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div className="fld"><label htmlFor="f-bal">Min balance</label><input id="f-bal" type="number" placeholder="any" value={filters.min_balance} onChange={setFilter('min_balance')} /></div>
          <div className="button-row">
            <button type="button" className="primary" onClick={() => load()}>Filter</button>
            <button type="button" className="secondary" onClick={() => { const cleared = { customer_id: '', branch_id: '', min_balance: '' }; setFilters(cleared); load(cleared) }}>Clear</button>
          </div>
        </div>

        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>Account #</th><th>Customer</th><th>Name</th><th className="num">Balance</th><th>Branch</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {accounts.length === 0 ? (
              <tr><td colSpan={8} className="admin-empty">No accounts match.</td></tr>
            ) : accounts.map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td>
                <td>{a.account_number}</td>
                <td>#{a.customer_id}</td>
                <td>{a.first_name} {a.last_name}</td>
                <td className="num">{money(a.balance)}</td>
                <td>#{a.branch_id}</td>
                <td><span className={a.is_active ? 'tag tag-ok' : 'tag tag-no'}>{a.is_active ? 'active' : 'inactive'}</span></td>
                <td>
                  <div className="row-actions">
                    {confirmingId === a.id ? (
                      <>
                        <button type="button" className="btn-sm btn-danger" onClick={() => deactivate(a)}>Confirm</button>
                        <button type="button" className="btn-sm btn-edit" onClick={() => setConfirmingId(null)}>Cancel</button>
                      </>
                    ) : (
                      <>
                        <button type="button" className="btn-sm btn-edit" onClick={() => startEdit(a)}>Edit</button>
                        {a.is_active && <button type="button" className="btn-sm btn-danger" onClick={() => setConfirmingId(a.id)}>Deactivate</button>}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}
