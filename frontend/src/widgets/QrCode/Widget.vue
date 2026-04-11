<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import QRCode from 'qrcode'
import type { DataPointValue } from '@/types'

const props = defineProps<{
  config: Record<string, unknown>
  datapointId: string | null
  value: DataPointValue | null
  statusValue: DataPointValue | null
  editorMode: boolean
}>()

const qrType          = computed(() => (props.config.qrType          as string) ?? 'url')
const label           = computed(() => (props.config.label           as string) ?? '')
const errorCorrection = computed(() => (props.config.errorCorrection as string) ?? 'M')
const darkColor       = computed(() => (props.config.darkColor       as string) ?? '#000000')
const lightColor      = computed(() => (props.config.lightColor      as string) ?? '#ffffff')

// URL
const urlValue = computed(() => (props.config.url_url as string) ?? '')

// WiFi
const wifiSsid       = computed(() => (props.config.wifi_ssid        as string)  ?? '')
const wifiPassword   = computed(() => (props.config.wifi_password    as string)  ?? '')
const wifiEncryption = computed(() => (props.config.wifi_encryption  as string)  ?? 'WPA')
const wifiHidden     = computed(() => (props.config.wifi_hidden      as boolean) ?? false)

// vCard
const vcardFirstname = computed(() => (props.config.vcard_firstname as string) ?? '')
const vcardLastname  = computed(() => (props.config.vcard_lastname  as string) ?? '')
const vcardCompany   = computed(() => (props.config.vcard_company   as string) ?? '')
const vcardMobile    = computed(() => (props.config.vcard_mobile    as string) ?? '')
const vcardEmail     = computed(() => (props.config.vcard_email     as string) ?? '')

/** Baut den QR-Inhalt je nach Typ zusammen */
const qrContent = computed((): string => {
  switch (qrType.value) {
    case 'url':
      return urlValue.value.trim()

    case 'wifi': {
      if (!wifiSsid.value.trim()) return ''
      // Sonderzeichen in SSID/Passwort escapen: \ ; , " :
      const esc = (s: string) => s.replace(/([\\;,":@])/g, '\\$1')
      const enc = wifiEncryption.value === 'none' ? 'nopass' : wifiEncryption.value
      const hidden = wifiHidden.value ? 'true' : 'false'
      return `WIFI:S:${esc(wifiSsid.value)};T:${enc};P:${esc(wifiPassword.value)};H:${hidden};;`
    }

    case 'vcard': {
      if (!vcardFirstname.value.trim() && !vcardLastname.value.trim()) return ''
      const lines = [
        'BEGIN:VCARD',
        'VERSION:3.0',
        `N:${vcardLastname.value};${vcardFirstname.value}`,
        `FN:${vcardFirstname.value} ${vcardLastname.value}`.trim(),
      ]
      if (vcardCompany.value.trim())  lines.push(`ORG:${vcardCompany.value}`)
      if (vcardMobile.value.trim())   lines.push(`TEL;TYPE=CELL:${vcardMobile.value}`)
      if (vcardEmail.value.trim())    lines.push(`EMAIL;TYPE=WORK:${vcardEmail.value}`)
      lines.push('END:VCARD')
      return lines.join('\n')
    }

    default:
      return ''
  }
})

const svgHtml  = ref('')
const genError = ref(false)

async function generateQr() {
  const text = qrContent.value
  if (!text) {
    svgHtml.value = ''
    genError.value = false
    return
  }
  try {
    svgHtml.value = await QRCode.toString(text, {
      type: 'svg',
      errorCorrectionLevel: errorCorrection.value as 'L' | 'M' | 'Q' | 'H',
      color: { dark: darkColor.value, light: lightColor.value },
      margin: 1,
    })
    genError.value = false
  } catch {
    svgHtml.value = ''
    genError.value = true
  }
}

onMounted(generateQr)
watch(qrContent, generateQr)
watch([errorCorrection, darkColor, lightColor], generateQr)
</script>

<template>
  <div class="h-full w-full flex flex-col items-center p-2 gap-1 overflow-hidden">

    <!-- Bezeichnung (oben) -->
    <span
      v-if="label"
      class="shrink-0 text-xs font-medium text-gray-700 dark:text-gray-300 truncate max-w-full text-center"
      data-testid="qrcode-label"
    >{{ label }}</span>

    <!-- Kein Inhalt konfiguriert -->
    <div
      v-if="!qrContent"
      class="flex flex-col items-center justify-center flex-1 gap-2 text-gray-400 dark:text-gray-600"
      data-testid="qrcode-placeholder"
    >
      <span class="text-4xl">▣</span>
      <span class="text-xs">QR-Code-Inhalt konfigurieren</span>
    </div>

    <!-- Fehler beim Generieren -->
    <div
      v-else-if="genError"
      class="flex-1 flex items-center justify-center text-red-400 text-xs"
      data-testid="qrcode-error"
    >
      Ungültiger Inhalt
    </div>

    <!-- QR-Code als SVG -->
    <div
      v-else
      class="flex-1 flex items-center justify-center overflow-hidden w-full [&_svg]:w-full [&_svg]:h-full [&_svg]:max-h-full"
      data-testid="qrcode-svg"
      v-html="svgHtml"
    />

  </div>
</template>
