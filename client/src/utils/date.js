// Date formatting utilities
// Centralizes the date-rendering logic that was previously duplicated across
// views and detail modals. Callers pass a locale and/or Intl options to preserve
// their specific display format; all functions guard against invalid dates.

const DEFAULT_OPTIONS = { month: 'short', day: 'numeric', year: 'numeric' }

// Map the app's locale code ('en' | 'ja') to an Intl locale string.
export function intlLocale(localeCode) {
  return localeCode === 'ja' ? 'ja-JP' : 'en-US'
}

// Format a date string via toLocaleDateString.
// options: Intl.DateTimeFormat options (defaults to short month, day, numeric year)
// fallback: returned for empty or unparseable dates
export function formatDate(dateString, { locale = 'en-US', options, fallback = '-' } = {}) {
  if (!dateString) return fallback
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return fallback
  return date.toLocaleDateString(locale, options ?? DEFAULT_OPTIONS)
}

// Format a date string as MM/DD/YY (numeric, locale-independent).
export function formatDateShort(dateString, { fallback = '-' } = {}) {
  if (!dateString) return fallback
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return fallback
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const year = date.getFullYear().toString().slice(-2)
  return `${month}/${day}/${year}`
}
