/**
 * Applies a math formula to a numeric value.
 * Variable: x (the current value).
 * Returns the original value on any error.
 */
export function applyFormula(formula: string, value: number): number {
  if (!formula.trim()) return value
  try {
    // eslint-disable-next-line no-new-func
    const fn = new Function('x', `'use strict'; return (${formula})`)
    const result = fn(value)
    return typeof result === 'number' && isFinite(result) ? result : value
  } catch {
    return value
  }
}

/**
 * Applies a value map (enum substitution) to any value.
 * Booleans are normalized to lowercase ("true" / "false").
 * Returns the original value if no match is found.
 */
export function applyValueMap(
  valueMap: Record<string, string>,
  value: unknown,
): unknown {
  if (!valueMap || Object.keys(valueMap).length === 0) return value
  const key = typeof value === 'boolean' ? String(value) : String(value)
  return Object.prototype.hasOwnProperty.call(valueMap, key) ? valueMap[key] : value
}
