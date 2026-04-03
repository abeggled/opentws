<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{
  modelValue: Record<string, unknown>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, unknown>): void
}>()

const cfg = reactive({
  label: (props.modelValue.label as string) ?? '',
})

watch(cfg, () => emit('update:modelValue', { ...cfg }), { deep: true })
</script>

<template>
  <div class="space-y-3">
    <div>
      <label class="block text-xs text-gray-400 mb-1">Beschriftung</label>
      <input
        v-model="cfg.label"
        type="text"
        placeholder="z.B. Licht EG Nacht"
        class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-blue-500"
      />
    </div>
    <p class="text-xs text-gray-500">
      Der Datenpunkt gibt den aktuellen Schaltausgang der Zeitschaltuhr wieder (BOOLEAN).<br />
      Optional: Status-Datenpunkt für den Aktivierungszustand der Einheit.
    </p>
  </div>
</template>
