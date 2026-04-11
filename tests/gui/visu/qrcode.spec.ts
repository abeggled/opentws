import { test, expect } from '@playwright/test'
import { randomUUID } from 'crypto'
import { apiPost, apiPut, apiDelete } from '../helpers'

/**
 * E2E-Tests für das QR-Code-Widget.
 *
 * Typen:
 *   - url   (url_url)
 *   - wifi  (wifi_ssid, wifi_password, wifi_encryption, wifi_hidden)
 *   - vcard (vcard_firstname, vcard_lastname, vcard_company, vcard_mobile, vcard_email)
 *
 * Priorität hoch:
 *   1. Kein Inhalt → Platzhalter sichtbar
 *   2. Typ URL mit URL → <svg> wird gerendert
 *   3. Typ WiFi mit SSID → <svg> wird gerendert
 *   4. Typ vCard mit Name → <svg> wird gerendert
 *
 * Priorität mittel:
 *   5. Bezeichnung erscheint oberhalb des QR-Codes
 *   6. Bezeichnung fehlt → kein Label-Element gerendert
 *   7. WiFi ohne Passwort (Unverschlüsselt) → QR-Code trotzdem gerendert
 *   8. Kein <img> oder <video> gerendert (SVG-basiert)
 */

// ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

async function createVisuPage() {
  return (await apiPost('/api/v1/visu/nodes', {
    name: `E2E-QrCode-Page-${Date.now()}`,
    type: 'PAGE',
    order: 999,
    access: 'public',
  })) as { id: string }
}

function baseConfig(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    qrType:          'url',
    label:           '',
    errorCorrection: 'M',
    darkColor:       '#000000',
    lightColor:      '#ffffff',
    url_url:         '',
    wifi_ssid:       '',
    wifi_password:   '',
    wifi_encryption: 'WPA',
    wifi_hidden:     false,
    vcard_firstname: '',
    vcard_lastname:  '',
    vcard_company:   '',
    vcard_mobile:    '',
    vcard_email:     '',
    ...overrides,
  }
}

async function buildQrPage(
  pageId: string,
  widgetId: string,
  config: Record<string, unknown>,
) {
  await apiPut(`/api/v1/visu/pages/${pageId}`, {
    grid_cols: 12,
    grid_row_height: 80,
    grid_cell_width: 80,
    background: null,
    widgets: [
      {
        id: widgetId,
        name: 'E2E QR-Code',
        type: 'QrCode',
        datapoint_id: null,
        status_datapoint_id: null,
        x: 0, y: 0, w: 4, h: 4,
        config,
      },
    ],
  })
}

// ─── Test 1 (hoch): Kein Inhalt → Platzhalter ────────────────────────────────

test('QrCode: kein Inhalt → Platzhalter "QR-Code-Inhalt konfigurieren"', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({ qrType: 'url', url_url: '' }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    await expect(widget.locator('[data-testid="qrcode-placeholder"]')).toBeVisible({ timeout: 5_000 })
    await expect(widget).toContainText('QR-Code-Inhalt konfigurieren')
    await expect(widget.locator('[data-testid="qrcode-svg"]')).toHaveCount(0)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 2 (hoch): Typ URL → <svg> gerendert ────────────────────────────────

test('QrCode: Typ URL → <svg>-Element wird gerendert', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({ qrType: 'url', url_url: 'https://example.com' }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    const svgContainer = widget.locator('[data-testid="qrcode-svg"]')
    await expect(svgContainer).toBeVisible({ timeout: 5_000 })
    await expect(svgContainer.locator('svg')).toBeVisible({ timeout: 3_000 })
    await expect(widget.locator('[data-testid="qrcode-placeholder"]')).toHaveCount(0)
    await expect(widget.locator('[data-testid="qrcode-error"]')).toHaveCount(0)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 3 (hoch): Typ WiFi → <svg> gerendert ───────────────────────────────

test('QrCode: Typ WiFi → <svg>-Element wird gerendert', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({
    qrType:          'wifi',
    wifi_ssid:       'GaesteNetz',
    wifi_password:   'Geheim1234',
    wifi_encryption: 'WPA',
    wifi_hidden:     false,
  }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    const svgContainer = widget.locator('[data-testid="qrcode-svg"]')
    await expect(svgContainer).toBeVisible({ timeout: 5_000 })
    await expect(svgContainer.locator('svg')).toBeVisible({ timeout: 3_000 })
    await expect(widget.locator('[data-testid="qrcode-error"]')).toHaveCount(0)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 4 (hoch): Typ vCard → <svg> gerendert ──────────────────────────────

test('QrCode: Typ vCard → <svg>-Element wird gerendert', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({
    qrType:          'vcard',
    vcard_firstname: 'Max',
    vcard_lastname:  'Mustermann',
    vcard_company:   'Musterfirma AG',
    vcard_mobile:    '+41 79 123 45 67',
    vcard_email:     'max@musterfirma.ch',
  }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    const svgContainer = widget.locator('[data-testid="qrcode-svg"]')
    await expect(svgContainer).toBeVisible({ timeout: 5_000 })
    await expect(svgContainer.locator('svg')).toBeVisible({ timeout: 3_000 })
    await expect(widget.locator('[data-testid="qrcode-error"]')).toHaveCount(0)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 5 (mittel): Bezeichnung erscheint OBERHALB des QR-Codes ─────────────

test('QrCode: Bezeichnung erscheint oberhalb des QR-Codes', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({
    qrType:  'url',
    url_url: 'https://example.com',
    label:   'Meine Webseite',
  }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    const label  = widget.locator('[data-testid="qrcode-label"]')
    const svg    = widget.locator('[data-testid="qrcode-svg"]')

    await expect(label).toBeVisible({ timeout: 5_000 })
    await expect(label).toContainText('Meine Webseite')
    await expect(svg).toBeVisible()

    // Bezeichnung liegt im DOM VOR dem SVG-Container → sie erscheint oben
    const labelBox = await label.boundingBox()
    const svgBox   = await svg.boundingBox()
    expect(labelBox).not.toBeNull()
    expect(svgBox).not.toBeNull()
    expect(labelBox!.y).toBeLessThan(svgBox!.y)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 6 (mittel): Kein Label → kein Label-Element ────────────────────────

test('QrCode: leere Bezeichnung → kein Label-Element gerendert', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({ qrType: 'url', url_url: 'https://example.com', label: '' }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    await expect(widget.locator('[data-testid="qrcode-svg"]')).toBeVisible({ timeout: 5_000 })
    await expect(widget.locator('[data-testid="qrcode-label"]')).toHaveCount(0)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 7 (mittel): WiFi unverschlüsselt → QR-Code trotzdem gerendert ───────

test('QrCode: WiFi unverschlüsselt (none) → <svg> wird trotzdem gerendert', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({
    qrType:          'wifi',
    wifi_ssid:       'OeffentlichesNetz',
    wifi_password:   '',
    wifi_encryption: 'none',
  }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    const svgContainer = widget.locator('[data-testid="qrcode-svg"]')
    await expect(svgContainer).toBeVisible({ timeout: 5_000 })
    await expect(svgContainer.locator('svg')).toBeVisible({ timeout: 3_000 })
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})

// ─── Test 8 (mittel): Kein <img> oder <video> (SVG-basiert) ──────────────────

test('QrCode: kein <img>- oder <video>-Element (ausschliesslich SVG)', async ({ page }) => {
  const visuNode = await createVisuPage()
  const pageId   = visuNode.id
  const widgetId = randomUUID()

  await buildQrPage(pageId, widgetId, baseConfig({ qrType: 'url', url_url: 'https://example.com' }))

  try {
    await page.goto(`/visu/${pageId}`)
    await page.waitForLoadState('domcontentloaded')

    const widget = page.locator(`[data-widget-id="${widgetId}"]`)
    await expect(widget.locator('[data-testid="qrcode-svg"]')).toBeVisible({ timeout: 5_000 })
    await expect(widget.locator('img')).toHaveCount(0)
    await expect(widget.locator('video')).toHaveCount(0)
  } finally {
    await apiDelete(`/api/v1/visu/nodes/${pageId}`)
  }
})
