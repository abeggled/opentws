/**
 * useTz — timezone-aware date/time formatting composable.
 *
 * Uses the configured application timezone (from settings store) with
 * Intl.DateTimeFormat so that all timestamp displays respect the same
 * timezone — independent of the user's browser locale.
 */
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export function useTz() {
  const settings = useSettingsStore()

  /** Configured IANA timezone string, e.g. "Europe/Zurich" */
  const timezone = computed(() => settings.timezone)

  /**
   * Format a UTC timestamp string (ISO 8601) as a locale date+time string
   * in the configured timezone.
   * @param {string|Date} ts
   * @returns {string}
   */
  function fmtDateTime(ts) {
    if (!ts) return '—'
    try {
      return new Intl.DateTimeFormat('de-CH', {
        timeZone:  settings.timezone,
        year:      'numeric',
        month:     '2-digit',
        day:       '2-digit',
        hour:      '2-digit',
        minute:    '2-digit',
        second:    '2-digit',
      }).format(new Date(ts))
    } catch {
      return new Date(ts).toLocaleString('de-CH')
    }
  }

  /**
   * Format a UTC timestamp as a date-only string in the configured timezone.
   * @param {string|Date} ts
   * @returns {string}
   */
  function fmtDate(ts) {
    if (!ts) return '—'
    try {
      return new Intl.DateTimeFormat('de-CH', {
        timeZone: settings.timezone,
        year:     'numeric',
        month:    '2-digit',
        day:      '2-digit',
      }).format(new Date(ts))
    } catch {
      return new Date(ts).toLocaleDateString('de-CH')
    }
  }

  /**
   * Format a UTC timestamp for a chart axis label (compact).
   * @param {string|Date} ts
   * @returns {string}
   */
  function fmtChartLabel(ts) {
    if (!ts) return ''
    try {
      return new Intl.DateTimeFormat('de-CH', {
        timeZone: settings.timezone,
        month:    'short',
        day:      '2-digit',
        hour:     '2-digit',
        minute:   '2-digit',
      }).format(new Date(ts))
    } catch {
      return new Date(ts).toLocaleString('de-CH', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    }
  }

  /**
   * Convert a UTC timestamp (or Date) to a "YYYY-MM-DDTHH:MM" string
   * in the configured timezone, suitable for <input type="datetime-local">.
   * @param {string|Date} ts
   * @returns {string}
   */
  function toDatetimeLocal(ts) {
    if (!ts) return ''
    try {
      // sv-SE locale yields "YYYY-MM-DD HH:MM" — no AM/PM, no slashes
      const s = new Intl.DateTimeFormat('sv-SE', {
        timeZone: settings.timezone,
        year:     'numeric',
        month:    '2-digit',
        day:      '2-digit',
        hour:     '2-digit',
        minute:   '2-digit',
        hour12:   false,
      }).format(new Date(ts))
      // "2026-03-29 14:30" → "2026-03-29T14:30"
      return s.replace(' ', 'T').slice(0, 16)
    } catch {
      return new Date(ts).toISOString().slice(0, 16)
    }
  }

  /**
   * Convert a "YYYY-MM-DDTHH:MM" string (entered in the configured timezone)
   * back to a UTC ISO 8601 string for API calls.
   *
   * The browser's Date constructor treats strings without a timezone suffix as
   * LOCAL browser time, which may differ from the configured app timezone.
   * This function always interprets the input as the configured timezone.
   *
   * @param {string} localStr  — e.g. "2026-03-29T14:30"
   * @returns {string|undefined}
   */
  function fromDatetimeLocal(localStr) {
    if (!localStr) return undefined
    try {
      const tz = settings.timezone
      const [y, mo, d, h, mi] = localStr.split(/[-T:]/).map(Number)

      // Start with a UTC candidate at the nominal time
      let utc = new Date(Date.UTC(y, mo - 1, d, h, mi))

      // Iterate: compare what the target TZ says that UTC moment is,
      // then correct the offset. Converges in ≤ 3 steps.
      for (let i = 0; i < 4; i++) {
        const parts = new Intl.DateTimeFormat('en-CA', {
          timeZone: tz,
          year: 'numeric', month: '2-digit', day: '2-digit',
          hour: '2-digit', minute: '2-digit', hour12: false,
        }).formatToParts(utc)

        const get = type => +parts.find(p => p.type === type).value
        const tzH = get('hour') % 24  // en-CA may give 24 for midnight
        const diff =
          Date.UTC(y, mo - 1, d, h, mi) -
          Date.UTC(get('year'), get('month') - 1, get('day'), tzH, get('minute'))

        utc = new Date(utc.getTime() + diff)
        if (diff === 0) break
      }
      return utc.toISOString()
    } catch {
      return new Date(localStr).toISOString()
    }
  }

  return { timezone, fmtDateTime, fmtDate, fmtChartLabel, toDatetimeLocal, fromDatetimeLocal }
}
