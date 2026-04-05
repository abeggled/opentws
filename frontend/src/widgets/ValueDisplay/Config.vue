<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{
  modelValue: Record<string, unknown>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, unknown>): void
}>()

type ValueMapEntry = { key: string; value: string }

function toEntries(map: Record<string, string> | undefined): ValueMapEntry[] {
  if (!map || Object.keys(map).length === 0) return []
  return Object.entries(map).map(([key, value]) => ({ key, value }))
}

function fromEntries(entries: ValueMapEntry[]): Record<string, string> {
  const result: Record<string, string> = {}
  for (const e of entries) {
    if (e.key !== '') result[e.key] = e.value
  }
  return result
}

const cfg = reactive({
  label: (props.modelValue.label as string) ?? '',
  unit: (props.modelValue.unit as string) ?? '',
  decimals: (props.modelValue.decimals as number) ?? 1,
  value_formula: (props.modelValue.value_formula as string) ?? '',
  value_map_entries: toEntries(props.modelValue.value_map as Record<string, string> | undefined),
})

watch(
  cfg,
  () =>
    emit('update:modelValue', {
      ...cfg,
      value_map_entries: undefined,
      value_map: fromEntries(cfg.value_map_entries),
    }),
  { deep: true },
)

function addEntry() {
  cfg.value_map_entries.push({ key: '', value: '' })
}

function removeEntry(i: number) {
  cfg.value_map_entries.splice(i, 1)
}
</script>

<template>
  <div class="space-y-3">
    <div>
      <label class="block text-xs text-gray-400 mb-1">Beschriftung</label>
      <input
        v-model="cfg.label"
        type="text"
        placeholder="z.B. Vorlauftemperatur"
        class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
      />
    </div>
    <div>
      <label class="block text-xs text-gray-400 mb-1">Einheit (überschreibt DP-Einheit)</label>
      <input
        v-model="cfg.unit"
        type="text"
        placeholder="z.B. °C"
        class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
      />
    </div>
    <div>
      <label class="block text-xs text-gray-400 mb-1">Dezimalstellen</label>
      <input
        v-model.number="cfg.decimals"
        type="number"
        min="0"
        max="6"
        class="w-24 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
      />
    </div>

    <!-- Transformation -->
    <div class="border-t border-gray-700 pt-3">
      <p class="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">Transformation</p>
      <div>
        <label class="block text-xs text-gray-400 mb-1">Formel (Variable: x)</label>
        <input
          v-model="cfg.value_formula"
          type="text"
          placeholder="z.B. x * 0.1"
          class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 font-mono focus:outline-none focus:border-blue-500"
        />
        <p class="text-xs text-gray-500 mt-1">Nur für numerische Werte. Erlaubt: +&nbsp;−&nbsp;*&nbsp;/&nbsp;**&nbsp;round()&nbsp;abs()&nbsp;…</p>
      </div>

      <div class="mt-3">
        <label class="block text-xs text-gray-400 mb-1">Wertzuordnung</label>
        <div class="space-y-1">
          <div
            v-for="(entry, i) in cfg.value_map_entries"
            :key="i"
            class="flex gap-1 items-center"
          >
            <input
              v-model="entry.key"
              type="text"
              placeholder="Wert"
              class="w-24 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100 font-mono focus:outline-none focus:border-blue-500"
            />
            <span class="text-gray-500 text-xs">→</span>
            <input
              v-model="entry.value"
              type="text"
              placeholder="Anzeige"
              class="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
            />
            <button
              type="button"
              class="text-gray-500 hover:text-red-400 text-xs px-1"
              @click="removeEntry(i)"
            >✕</button>
          </div>
        </div>
        <button
          type="button"
          class="mt-1 text-xs text-blue-400 hover:text-blue-300"
          @click="addEntry"
        >+ Eintrag hinzufügen</button>
        <p class="text-xs text-gray-500 mt-1">z.B. 0 → AUS, 1 → EIN, true → Offen</p>
      </div>
    </div>
  </div>
</template>
