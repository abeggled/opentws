/**
 * API helpers for E2E tests.
 *
 * Each function does a fresh login before the request using credentials from
 * E2E_USER / E2E_PASS env vars (default: admin / admin).
 * This is acceptable because tests run sequentially and there is no rate
 * limiting in the test environment.
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:8080'
const E2E_USER = process.env.E2E_USER ?? 'admin'
const E2E_PASS = process.env.E2E_PASS ?? 'admin'

async function getToken(): Promise<string> {
  const res = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username: E2E_USER, password: E2E_PASS }),
  })
  if (!res.ok) throw new Error(`Login failed: ${res.status}`)
  const data = await res.json()
  return data.access_token as string
}

export async function apiGet(path: string): Promise<unknown> {
  const token = await getToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

export async function apiPost(path: string, body: unknown): Promise<unknown> {
  const token = await getToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`POST ${path} failed: ${res.status} — ${text}`)
  }
  // Some POST endpoints return 204 No Content (e.g. set datapoint value)
  if (res.status === 204) return null
  return res.json()
}

export async function apiPut(path: string, body: unknown): Promise<unknown> {
  const token = await getToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`PUT ${path} failed: ${res.status} — ${text}`)
  }
  // PUT /api/v1/visu/pages returns 204 No Content
  if (res.status === 204) return null
  return res.json()
}

export async function apiDelete(path: string): Promise<void> {
  const token = await getToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok && res.status !== 404) {
    throw new Error(`DELETE ${path} failed: ${res.status}`)
  }
}
