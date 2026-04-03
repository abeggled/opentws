<script setup lang="ts">
import { computed } from 'vue'
import type { DataPointValue } from '@/types'

const props = defineProps<{
  config: Record<string, unknown>
  datapointId: string | null
  value: DataPointValue | null
  statusValue: DataPointValue | null
  editorMode: boolean
}>()

const label = computed(() => (props.config.label as string | undefined) ?? '—')

function resolveBool(v: DataPointValue | null): boolean | null {
  if (v === null) return null
  const raw = v.v
  if (typeof raw === 'boolean') return raw
  if (typeof raw === 'number') return raw !== 0
  if (typeof raw === 'string') return raw === '1' || raw.toLowerCase() === 'true'
  return null
}

/** Ausgang: ob der Zeitplan gerade aktiv schaltet */
const outputActive = computed(() => {
  if (props.editorMode) return null
  return resolveBool(props.value)
})

/** Einheit-Status: ob die Zeitschaltuhr-Einheit aktiviert ist (optionaler Status-Datenpunkt) */
const unitEnabled = computed(() => {
  if (props.editorMode || props.statusValue === null) return null
  return resolveBool(props.statusValue)
})

const quality = computed(() => props.value?.q ?? null)
</script>

<template>
  <div class="flex flex-col h-full p-3 select-none gap-1.5">
    <!-- Kopfzeile: Icon + Beschriftung -->
    <div class="flex items-center gap-1.5 min-w-0">
      <span class="text-sm leading-none flex-shrink-0">🕐</span>
      <span class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ label }}</span>
      <span
        v-if="quality === 'bad'"
        class="ml-auto w-2 h-2 rounded-full bg-red-500 flex-shrink-0"
        title="Qualität: schlecht"
      />
      <span
        v-else-if="quality === 'uncertain'"
        class="ml-auto w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0"
        title="Qualität: undefiniert"
      />
    </div>

    <!-- Ausgang-Zustand -->
    <div class="flex items-center gap-2 mt-1">
      <span
        class="inline-flex items-center px-2.5 py-1 rounded-md text-sm font-semibold leading-none"
        :class="outputActive === null
          ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
          : outputActive
            ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'"
      >
        {{ outputActive === null ? '…' : outputActive ? 'AKTIV' : 'INAKTIV' }}
      </span>
    </div>

    <!-- Einheit-Status (nur wenn Status-Datenpunkt konfiguriert) -->
    <div v-if="unitEnabled !== null" class="flex items-center gap-1.5 mt-auto">
      <span
        class="w-1.5 h-1.5 rounded-full flex-shrink-0"
        :class="unitEnabled ? 'bg-blue-400' : 'bg-gray-400 dark:bg-gray-600'"
      />
      <span class="text-xs text-gray-400 dark:text-gray-500">
        {{ unitEnabled ? 'Einheit aktiv' : 'Einheit deaktiviert' }}
      </span>
    </div>
  </div>
</template>
