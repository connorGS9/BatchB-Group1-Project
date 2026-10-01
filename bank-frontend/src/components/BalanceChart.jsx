import { useEffect, useRef, useState } from 'react'
import { money } from './format.js'

// Total balance across the customer's accounts at the end of each of the last
// `days` days, drawn as a line + soft area with a hover crosshair.
//
// The API stores transactions, not balance snapshots, so we rebuild history by
// walking backwards from today's balance: the balance at the end of a past day is
// today's balance minus everything that moved in/out after that day. Transfers
// between the customer's own accounts net to zero, as they should.

const DAY_MS = 24 * 60 * 60 * 1000
const HEIGHT = 200
const PAD = { top: 16, right: 16, bottom: 28, left: 56 }

function startOfDay(ms) {
  const d = new Date(ms)
  d.setHours(0, 0, 0, 0)
  return d.getTime()
}

export function dailyBalances(transactions, myIds, currentBalance, days, now = Date.now()) {
  const today = startOfDay(now)
  const points = []
  // days + 1 points: the first is the balance going into the window, so the
  // first→last change covers the same span as the "30 days" tiles.
  for (let i = days; i >= 0; i--) {
    const dayStart = today - i * DAY_MS
    points.push({ day: dayStart, end: dayStart + DAY_MS, balance: currentBalance })
  }
  for (const t of transactions) {
    const ts = new Date(t.timestamp).getTime()
    let net = 0
    if (myIds.includes(t.to_account_id)) net += t.amount
    if (myIds.includes(t.from_account_id)) net -= t.amount
    if (net === 0) continue
    // Undo this transaction for every day that ended before it happened.
    for (const p of points) if (p.end <= ts) p.balance -= net
  }
  return points
}

// 3–5 round tick values covering [min, max].
function niceTicks(min, max) {
  if (min === max) {
    const pad = Math.max(Math.abs(min) * 0.1, 10)
    min -= pad
    max += pad
  }
  const raw = (max - min) / 4
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw)
  const ticks = []
  for (let v = Math.floor(min / step) * step; v <= max + step * 0.001; v += step) ticks.push(v)
  if (ticks[ticks.length - 1] < max) ticks.push(ticks[ticks.length - 1] + step)
  return ticks
}

function shortMoney(v) {
  const abs = Math.abs(v)
  if (abs >= 1000) return `${v < 0 ? '-' : ''}$${(abs / 1000).toFixed(abs >= 10000 ? 0 : 1)}k`
  return `${v < 0 ? '-' : ''}$${Math.round(abs)}`
}

const dayLabel = (ms) => new Date(ms).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

export default function BalanceChart({ transactions, myIds, currentBalance, days = 30 }) {
  const wrapRef = useRef(null)
  const [width, setWidth] = useState(600)
  const [hover, setHover] = useState(null) // index into points

  // Size the SVG to its container so text never stretches.
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(260, entry.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const points = dailyBalances(transactions, myIds, currentBalance, days)
  const values = points.map((p) => p.balance)
  const ticks = niceTicks(Math.min(...values), Math.max(...values))
  const lo = ticks[0]
  const hi = ticks[ticks.length - 1]

  const plotW = width - PAD.left - PAD.right
  const plotH = HEIGHT - PAD.top - PAD.bottom
  const x = (i) => PAD.left + (i / (points.length - 1)) * plotW
  const y = (v) => PAD.top + (1 - (v - lo) / (hi - lo)) * plotH

  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.balance).toFixed(1)}`).join('')
  const area = `${line}L${x(points.length - 1)},${y(lo)}L${x(0)},${y(lo)}Z`

  const first = values[0]
  const last = values[values.length - 1]
  const change = last - first

  function handleMove(e) {
    const rect = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - rect.left) / rect.width) * width
    const i = Math.round(((px - PAD.left) / plotW) * (points.length - 1))
    setHover(Math.min(points.length - 1, Math.max(0, i)))
  }

  const h = hover != null ? points[hover] : null
  const prev = hover > 0 ? points[hover - 1].balance : null

  return (
    <section className="panel balance-chart">
      <div className="chart-head">
        <h2>Balance · last {days} days</h2>
        <span className={change >= 0 ? 'chart-change up' : 'chart-change down'}>
          {change >= 0 ? '▲' : '▼'} {money(Math.abs(change))}
        </span>
      </div>

      <div className="chart-wrap" ref={wrapRef}>
        <svg
          width={width}
          height={HEIGHT}
          role="img"
          aria-label={`Total balance went from ${money(first)} to ${money(last)} over the last ${days} days`}
          onPointerMove={handleMove}
          onPointerLeave={() => setHover(null)}
        >
          {ticks.map((t) => (
            <g key={t}>
              <line className="chart-grid" x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)} />
              <text className="chart-axis" x={PAD.left - 8} y={y(t)} dy="0.32em" textAnchor="end">{shortMoney(t)}</text>
            </g>
          ))}
          {[0, Math.floor((points.length - 1) / 2), points.length - 1].map((i) => (
            <text key={i} className="chart-axis" x={x(i)} y={HEIGHT - 8}
              textAnchor={i === 0 ? 'start' : i === points.length - 1 ? 'end' : 'middle'}>
              {dayLabel(points[i].day)}
            </text>
          ))}

          <path className="chart-area" d={area} />
          <path className="chart-line" d={line} />

          {h ? (
            <g>
              <line className="chart-cross" x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + plotH} />
              <circle className="chart-dot" cx={x(hover)} cy={y(h.balance)} r="5" />
            </g>
          ) : (
            <circle className="chart-dot" cx={x(points.length - 1)} cy={y(last)} r="5" />
          )}
        </svg>

        {h && (
          <div
            className="chart-tip"
            style={{ left: x(hover), top: y(h.balance) }}
            data-flip={x(hover) > width * 0.65 ? 'left' : 'right'}
          >
            <span className="chart-tip-date">{dayLabel(h.day)}</span>
            <strong>{money(h.balance)}</strong>
            {prev != null && h.balance !== prev && (
              <span className="chart-tip-delta">
                {h.balance > prev ? '+' : '−'}{money(Math.abs(h.balance - prev))} that day
              </span>
            )}
          </div>
        )}
      </div>

      <table className="visually-hidden">
        <caption>End-of-day total balance</caption>
        <thead><tr><th>Date</th><th>Balance</th></tr></thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.day}><td>{dayLabel(p.day)}</td><td>{money(p.balance)}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
