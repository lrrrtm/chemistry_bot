function hasExplicitTimezone(value: string) {
  return /(?:Z|[+-]\d{2}:\d{2})$/i.test(value)
}

export function parseServerDate(value: string | null | undefined) {
  if (!value) return null

  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const withTimezone = hasExplicitTimezone(normalized) ? normalized : `${normalized}Z`
  const date = new Date(withTimezone)

  return Number.isNaN(date.getTime()) ? null : date
}

export function formatLocalDate(value: string | null | undefined, options?: Intl.DateTimeFormatOptions) {
  const date = parseServerDate(value)
  if (!date) return '-'

  return date.toLocaleString('ru-RU', options)
}
