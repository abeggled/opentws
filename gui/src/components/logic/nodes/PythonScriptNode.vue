<template>
  <div class="logic-node-wrap">
    <Handle type="target" id="a" :position="Position.Left" class="logic-handle" style="top:35%" />
    <Handle type="target" id="b" :position="Position.Left" class="logic-handle" style="top:55%" />
    <Handle type="target" id="c" :position="Position.Left" class="logic-handle" style="top:75%" />

    <div class="logic-node rounded-lg border border-slate-600 shadow-lg min-w-[180px]"
         style="background:#1e293b; border-top: 3px solid #be185d;">
      <div class="px-3 py-1.5" style="background:#be185d22">
        <span class="text-xs font-bold text-slate-100 uppercase tracking-wide">Python Script</span>
      </div>
      <div class="px-3 py-2">
        <pre class="text-xs text-pink-300 font-mono max-w-[160px] overflow-hidden" style="max-height:60px">{{ shortScript }}</pre>
      </div>
    </div>

    <Handle type="source" id="result" :position="Position.Right" class="logic-handle" style="top:55%" />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
const props = defineProps({ id: String, type: String, data: { type: Object, default: () => ({}) } })
const shortScript = computed(() => {
  const s = props.data.script || '# script'
  return s.length > 80 ? s.slice(0, 77) + '…' : s
})
</script>
<style scoped>
.logic-node-wrap { position: relative; }
.logic-handle { width: 10px; height: 10px; background: #94a3b8; border: 2px solid #1e293b; }
</style>
