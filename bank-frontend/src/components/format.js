// Shared helper: 1234.5 -> "$1,234.50"
export function money(amount) {
  return amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}