<template>
  <div :class="['logic-node rounded-lg border shadow-lg min-w-[140px]', borderClass]"
       :style="{ borderTopColor: color, borderTopWidth: '3px' }">
    <!-- Header -->
    <div class="px-3 py-1.5 flex items-center gap-2"
         :style="{ background: color + '22' }">
      <span class="text-xs font-bold text-slate-100 uppercase tracking-wide">{{ label }}</span>
    </div>
    <!-- Slots for handles and content injected by parent -->
    <div class="px-3 py-2 flex flex-col gap-1 text-xs text-slate-300">
      <slot />
    </div>
  </div>
</template>
<script setup>
defineProps({
  label: { type: String, required: true },
  color: { type: String, default: '#475569' },
  borderClass: { type: String, default: 'border-slate-600' },
})
</script>
<style scoped>
.logic-node { background: #1e293b; }
</style>
