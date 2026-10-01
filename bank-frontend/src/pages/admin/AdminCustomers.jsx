import { useCallback, useEffect, useState } from 'react'
import {
  createCustomer, deactivateCustomer, getCustomers, updateCustomer,
} from '../../api/authService.js'

const EMPTY = { first_name: '', last_name: '', email: '', phone: '' }

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [editingId, setEditingId] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  const load = useCallback(async () => {
    try {
      setCustomers(await getCustomers())
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  }
  function resetForm() {
    setEditingId(null)
    setForm(EMPTY)
  }
  function startEdit(c) {
    setEditingId(c.id)
    setForm({ first_name: c.first_name, last_name: c.last_name, email: c.email, phone: c.phone })
    setMsg('')
    setError('')
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMsg('')
    const payload = {
      first_name: form.first_name.trim(), last_name: form.last_name.trim(),
      email: form.email.trim(), phone: form.phone.trim(),
    }
    try {
      if (editingId) {
        const c = await updateCustomer(editingId, payload)
        setMsg(`Updated customer #${c.id}`)
      } else {
        const c = await createCustomer(payload)
        setMsg(`Added customer #${c.id} (${c.first_name} ${c.last_name})`)
      }
      resetForm()
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function deactivate(c) {
    setError('')
    try {
      await deactivateCustomer(c.id)
      setMsg(`Deactivated customer #${c.id}`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const editing = editingId != null

  return (
    <>
      <h1>Customers</h1>

      <section className="panel">
        <h2>{editing ? `Edit customer #${editingId}` : 'Add a new customer'}</h2>
        <form className="admin-form" onSubmit={submit}>
          <div className="fld"><label htmlFor="c-first">First name</label><input id="c-first" value={form.first_name} onChange={set('first_name')} required /></div>
          <div className="fld"><label htmlFor="c-last">Last name</label><input id="c-last" value={form.last_name} onChange={set('last_name')} required /></div>
          <div className="fld"><label htmlFor="c-email">Email</label><input id="c-email" type="email" value={form.email} onChange={set('email')} required /></div>
          <div className="fld"><label htmlFor="c-phone">Phone</label><input id="c-phone" value={form.phone} onChange={set('phone')} placeholder="555-0100" required /></div>
          <div className="button-row">
            <button type="submit" className="primary" disabled={busy}>
              {busy ? 'Saving…' : editing ? 'Save changes' : 'Add customer'}
            </button>
            {editing && <button type="button" className="secondary" onClick={resetForm} disabled={busy}>Cancel</button>}
          </div>
        </form>
        {msg && <p className="success" role="status">{msg}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>

      <section className="panel">
        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {customers.length === 0 ? (
              <tr><td colSpan={6} className="admin-empty">No customers.</td></tr>
            ) : customers.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.first_name} {c.last_name}</td>
                <td>{c.email}</td>
                <td>{c.phone}</td>
                <td><span className={c.is_active ? 'tag tag-ok' : 'tag tag-no'}>{c.is_active ? 'active' : 'inactive'}</span></td>
                <td>
                  <div className="row-actions">
                    <button type="button" className="btn-sm btn-edit" onClick={() => startEdit(c)}>Edit</button>
                    {c.is_active && <button type="button" className="btn-sm btn-danger" onClick={() => deactivate(c)}>Deactivate</button>}
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
