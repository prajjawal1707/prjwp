export const MIN_DAY = '2026-01-02'
export const MAX_DAY = '2026-02-01'
export const validDay = (d) => /^\d{4}-\d{2}-\d{2}$/.test(d) && d >= MIN_DAY && d <= MAX_DAY
export const validCutoff = (c) => /^([01]\d|2[0-3]):[0-5]\d$/.test(c)
export const hhmm = (t) => (t ? t.slice(11, 16) : '')
export const dayHhmm = (t) => (t ? t.slice(5, 16).replace('T', ' ') : '')