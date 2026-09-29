import { useState } from 'react'
import { updateCustomer } from '../api/authService.js'

// Edit first name, last name and phone.  Saves with PUT /api/v1/customers/{id}
export default function Settings({ customer, onSaved }) {
  const [form, setForm] = useState({
    first_name: customer.first_name,
    last_name: customer.last_name,
    phone: customer.phone,
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)

  const changed =
    form.first_name !== customer.first_name ||
    form.last_name !== customer.last_name ||
    form.phone !== customer.phone

  function update(field) {
    return (e) => {
      setForm({ ...form, [field]: e.target.value })
      setSuccess('')
    }
  }

  async function handleSave(e) {
    e.preventDefault()
    setError('')
    const clean = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      phone: form.phone.trim(),
    }
    if (!clean.first_name || !clean.last_name) return setError('First and last name are required.')
    if (!/^[0-9+()\-.\s]{7,20}$/.test(clean.phone)) return setError('Enter a phone number, e.g. 555-0100.')

    setSaving(true)
    try {
      const saved = await updateCustomer(customer.id, clean)
      setForm({ first_name: saved.first_name, last_name: saved.last_name, phone: saved.phone })
      setSuccess('Your details were saved.')
      onSaved(saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="panel">
      <h2>Profile settings</h2>
      <form className="stack" onSubmit={handleSave} noValidate>
        <div className="two-col">
          <div>
            <label htmlFor="first_name">First name</label>
            <input id="first_name" value={form.first_name} onChange={update('first_name')} />
          </div>
          <div>
            <label htmlFor="last_name">Last name</label>
            <input id="last_name" value={form.last_name} onChange={update('last_name')} />
          </div>
        </div>

        <label htmlFor="phone">Phone number</label>
        <input id="phone" type="tel" value={form.phone} onChange={update('phone')} />

        <label htmlFor="email">Email</label>
        <input id="email" value={customer.email} disabled />

        {error && <p className="error" role="alert">{error}</p>}
        {success && <p className="success" role="status">{success}</p>}

        <button type="submit" className="primary" disabled={saving || !changed}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </form>
    </section>
  )
}