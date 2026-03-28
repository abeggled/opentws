<template>
  <div v-if="node" class="h-full flex flex-col bg-slate-900 border-l border-slate-700/60 w-72">
    <div class="px-4 py-3 border-b border-slate-700/60 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-200">{{ nodeDef?.label ?? node.type }}</h3>
      <button @click="$emit('close')" class="btn-icon text-slate-500"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
    </div>
    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
      <!-- Description -->
      <p v-if="nodeDef?.description" class="text-xs text-slate-500">{{ nodeDef.description }}</p>

      <!-- Datapoint picker -->
      <template v-if="node.type === 'datapoint_read' || node.type === 'datapoint_write'">
        <div class="form-group">
          <label class="label">DataPoint</label>
          <input v-model="dpSearch" type="text" class="input text-sm" placeholder="Suchen…" @input="searchDps" />
          <div v-if="dpResults.length" class="mt-1 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden max-h-40 overflow-y-auto">
            <button v-for="dp in dpResults" :key="dp.id"
              @click="selectDp(dp)"
              class="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-700 text-slate-200">
              {{ dp.name }}
              <span class="text-slate-500 ml-1">{{ dp.data_type }}</span>
            </button>
          </div>
          <div v-if="localData.datapoint_name" class="mt-1 text-xs text-teal-400">
            ✓ {{ localData.datapoint_name }}
          </div>
        </div>
      </template>

      <!-- Generic config fields from schema -->
      <template v-if="nodeDef?.config_schema">
        <div v-for="(schema, key) in configFields" :key="key" class="form-group">
          <label class="label">{{ schema.label ?? key }}</label>
          <textarea v-if="schema.type === 'string' && key === 'script'"
            v-model="localData[key]" rows="6"
            class="input text-xs font-mono resize-y" @change="emitUpdate" />
          <select v-else-if="schema.enum"
            v-model="localData[key]" class="input text-sm" @change="emitUpdate">
            <option v-for="opt in schema.enum" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <input v-else
            v-model="localData[key]"
            :type="schema.type === 'number' ? 'number' : 'text'"
            class="input text-sm" @change="emitUpdate" />
        </div>
      </template>
    </div>
    <div class="p-3 border-t border-slate-700/60">
      <button @click="emitUpdate" class="btn-primary w-full btn-sm">Übernehmen</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { dpApi } from '@/api/client'

const props = defineProps({
  node:      { type: Object, default: null },
  nodeTypes: { type: Array,  default: () => [] },
})
const emit = defineEmits(['update', 'close'])

const localData  = ref({})
const dpSearch   = ref('')
const dpResults  = ref([])

const nodeDef = computed(() => props.nodeTypes.find(nt => nt.type === props.node?.type))

const configFields = computed(() => {
  const schema = nodeDef.value?.config_schema ?? {}
  // exclude datapoint fields — handled separately
  return Object.fromEntries(
    Object.entries(schema).filter(([k]) => !k.startsWith('datapoint_'))
  )
})

watch(() => props.node, (n) => {
  if (n) {
    localData.value = { ...n.data }
    dpSearch.value  = n.data.datapoint_name || ''
    dpResults.value = []
  }
}, { immediate: true })

async function searchDps() {
  if (dpSearch.value.length < 1) { dpResults.value = []; return }
  try {
    const { data } = await dpApi.list(0, 20)
    dpResults.value = (data.items || data).filter(dp =>
      dp.name.toLowerCase().includes(dpSearch.value.toLowerCase())
    )
  } catch { dpResults.value = [] }
}

function selectDp(dp) {
  localData.value.datapoint_id   = dp.id
  localData.value.datapoint_name = dp.name
  dpSearch.value  = dp.name
  dpResults.value = []
  emitUpdate()
}

function emitUpdate() {
  emit('update', { ...localData.value })
}
</script>
