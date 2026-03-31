<template>
  <div class="logic-node-wrap">
    <!-- Input handles -->
    <Handle v-for="inp in inputs" :key="inp.id"
      type="target" :id="inp.id"
      :position="Position.Left"
      class="logic-handle" />

    <BaseNode :label="data.label || type.toUpperCase()" :color="color">
      <div class="text-center text-slate-400 text-xs py-1">{{ description }}</div>
    </BaseNode>

    <!-- Output handles -->
    <Handle v-for="out in outputs" :key="out.id"
      type="source" :id="out.id"
      :position="Position.Right"
      class="logic-handle" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import BaseNode from './BaseNode.vue'

const props = defineProps({
  id:    String,
  type:  String,
  data:  { type: Object, default: () => ({}) },
  inputs:  { type: Array, default: () => [] },
  outputs: { type: Array, default: () => [] },
  color:   { type: String, default: '#1d4ed8' },
  description: { type: String, default: '' },
})
</script>
<style scoped>
.logic-node-wrap { position: relative; }
.logic-handle { width: 10px; height: 10px; background: #94a3b8; border: 2px solid #1e293b; }
</style>
