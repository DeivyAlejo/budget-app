export type DateDisplayFormat = 'short' | 'medium' | 'long'

// Change this value to switch date style app-wide.
export const DEFAULT_DATE_DISPLAY_FORMAT: DateDisplayFormat = 'medium'

const formatOptionsByStyle: Record<DateDisplayFormat, Intl.DateTimeFormatOptions> = {
  short: {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  },
  medium: {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  },
  long: {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  },
}

export function formatDisplayDate(
  value: string,
  style: DateDisplayFormat = DEFAULT_DATE_DISPLAY_FORMAT,
): string {
  if (!value) {
    return value
  }

  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('en-US', formatOptionsByStyle[style]).format(parsed)
}
