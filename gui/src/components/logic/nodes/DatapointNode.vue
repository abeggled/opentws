<template>
  <div class="logic-node-wrap">
    <Handle v-if="isWrite"
      type="target" id="value" :position="Position.Left" class="logic-handle" style="top: 55%"/>
    <Handle v-if="isWrite"
      type="target" id="trigger" :position="Position.Left" class="logic-handle" style="top: 75%"/>

    <div class="logic-node rounded-lg border border-slate-600 shadow-lg min-w-[160px]"
         style="background:#1e293b; border-top: 3px solid #0f766e;">
      <div class="px-3 py-1.5 flex items-center gap-2" style="background:#0f766e22">
        <span class="text-xs font-bold text-slate-100 uppercase tracking-wide">
          {{ isWrite ? 'DP Schreiben' : 'DP Lesen' }}
        </span>
      </div>
      <div class="px-3 py-2 flex flex-col gap-1">
        <div class="text-xs text-slate-400">DataPoint:</div>
        <div class="text-xs text-teal-300 font-medium truncate max-w-[140px]">
          {{ data.datapoint_name || data.datapoint_id || '— nicht gewählt —' }}
        </div>
      </div>
    </div>

    <Handle v-if="!isWrite"
      type="source" id="value" :position="Position.Right" class="logic-handle" style="top: 55%"/>
    <Handle v-if="!isWrite"
      type="source" id="changed" :position="Position.Right" class="logic-handle" style="top: 75%"/>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps({
  id:   String,
  type: String,
  data: { type: Object, default: () => ({}) },
})
const isWrite = computed(() => props.type === 'datapoint_write')
</script>
<style scoped>
.logic-node-wrap { position: relative; }
.logic-handle { width: 10px; height: 10px; background: #94a3b8; border: 2px solid #1e293b; }
</style>
