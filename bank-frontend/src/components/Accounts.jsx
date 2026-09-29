import { money } from './format.js'

// Balance card(s) + recent activity for the signed-in customer
export default function Accounts({ accounts, allAccounts, transactions }) {
  const myIds = accounts.map((a) => a.id)
  const numberOf = (id) => allAccounts.find((a) => a.id === id)?.account_number || `#${id}`
  const nameOf = (id) => {
    const a = allAccounts.find((x) => x.id === id)
    return a ? `${a.account_number} · ${a.first_name} ${a.last_name}` : `account #${id}`
  }
  const total = accounts.reduce((sum, a) => sum + a.balance, 0)

  return (
    <>
      <section className="balance-card">
        <p className="label">Total balance</p>
        <p className="balance">{money(total)}</p>
        <ul className="account-list">
          {accounts.map((a) => (
            <li key={a.id}>
              <span>
                Account <strong>{a.account_number}</strong>
                {!a.is_active && <span className="badge">Inactive</span>}
              </span>
              <span className="amount">{money(a.balance)}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Recent activity</h2>
        {transactions.length === 0 ? (
          <p className="muted">No transactions yet.</p>
        ) : (
          <ul className="activity">
            {transactions.slice(0, 8).map((t) => {
              const sent = myIds.includes(t.from_account_id)
              return (
                <li key={t.id}>
                  <div>
                    <p className="what">
                      {sent ? `Sent to ${nameOf(t.to_account_id)}` : `Received from ${nameOf(t.from_account_id)}`}
                    </p>
                    <p className="when">
                      {new Date(t.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                      {' · '}
                      {sent ? `from ${numberOf(t.from_account_id)}` : `to ${numberOf(t.to_account_id)}`}
                    </p>
                  </div>
                  <span className={sent ? 'amount out' : 'amount in'}>
                    {sent ? '−' : '+'}
                    {money(t.amount)}
                  </span>
                </li>
              )
            })}
          </ul>
        )}
      </section>
    </>
  )
}