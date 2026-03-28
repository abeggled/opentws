<template>
  <div class="gn-root" @mouseenter="hovered = true" @mouseleave="hovered = false">

    <!-- Input handles (LEFT) — z-index via inline style -->
    <Handle
      v-for="(inp, i) in def.inputs" :key="'in-' + inp.id"
      type="target" :id="inp.id" :position="Position.Left"
      :style="hStyle(i, def.inputs.length)"
    />

    <!-- Card — height controlled so handles align with rows -->
    <div class="gn-card"
         :style="{ borderTopColor: def.color, background: def.color + '12', minHeight: cardH + 'px' }">

      <div class="gn-header" :style="{ background: def.color + '28' }">
        <span class="gn-title">{{ data.label || def.label }}</span>
        <button v-show="hovered" class="gn-del nodrag" @click.stop="remove">✕</button>
      </div>

      <div class="gn-body">
        <div v-if="summary" class="gn-summary">{{ summary }}</div>

        <!-- Port rows — height matches handle spacing -->
        <div class="gn-ports-rows">
          <div
            v-for="r in portRows" :key="r"
            class="gn-port-row"
            :style="{ height: PORT_H + 'px' }"
          >
            <span class="gn-port-left">{{ def.inputs[r]?.label }}</span>
            <span class="gn-port-right">{{ def.outputs[r]?.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Output handles (RIGHT) -->
    <Handle
      v-for="(out, i) in def.outputs" :key="'out-' + out.id"
      type="source" :id="out.id" :position="Position.Right"
      :style="hStyle(i, def.outputs.length)"
      class="gn-out"
    />

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Handle, Position, useVueFlow } from '@vue-flow/core'

const props = defineProps({
  id:   { type: String, required: true },
  type: { type: String, required: true },
  data: { type: Object, default: () => ({}) },
})

// ── Node definitions ───────────────────────────────────────────────────────
const NODE_DEFS = {
  and:          { label: 'AND',         color: '#1d4ed8', inputs: [{id:'a',label:'A'},{id:'b',label:'B'}],           outputs: [{id:'out',   label:'Out'}]       },
  or:           { label: 'OR',          color: '#1d4ed8', inputs: [{id:'a',label:'A'},{id:'b',label:'B'}],           outputs: [{id:'out',   label:'Out'}]       },
  not:          { label: 'NOT',         color: '#1d4ed8', inputs: [{id:'in',label:'In'}],                            outputs: [{id:'out',   label:'Out'}]       },
  xor:          { label: 'XOR',         color: '#1d4ed8', inputs: [{id:'a',label:'A'},{id:'b',label:'B'}],           outputs: [{id:'out',   label:'Out'}]       },
  compare:      { label: 'Vergleich',   color: '#1d4ed8', inputs: [{id:'a',label:'A'},{id:'b',label:'B'}],           outputs: [{id:'out',   label:'Erg.'}]      },
  hysteresis:   { label: 'Hysterese',   color: '#1d4ed8', inputs: [{id:'value',label:'Wert'}],                       outputs: [{id:'out',   label:'Out'}]       },
  math_formula: { label: 'Formel',      color: '#7c3aed', inputs: [{id:'a',label:'a'},{id:'b',label:'b'}],           outputs: [{id:'result',label:'Erg.'}]      },
  math_map:     { label: 'Skalieren',   color: '#7c3aed', inputs: [{id:'value',label:'Wert'}],                       outputs: [{id:'result',label:'Erg.'}]      },
  timer_delay:  { label: 'Verzögerung', color: '#b45309', inputs: [{id:'trigger',label:'Trigger'}],                  outputs: [{id:'trigger',label:'Trigger'}]  },
  timer_pulse:  { label: 'Impuls',      color: '#b45309', inputs: [{id:'trigger',label:'Trigger'}],                  outputs: [{id:'out',   label:'Out'}]       },
  timer_cron:   { label: 'Zeitplan',    color: '#b45309', inputs: [],                                                outputs: [{id:'trigger',label:'Trigger'}]  },
  mcp_tool:     { label: 'MCP Tool',    color: '#0e7490', inputs: [{id:'trigger',label:'Trigger'},{id:'input',label:'Input'}], outputs: [{id:'result',label:'Erg.'},{id:'done',label:'Fertig'}] },
}

const def = computed(() => NODE_DEFS[props.type] ?? { label: props.type, color: '#475569', inputs: [], outputs: [] })

// ── Config summary ─────────────────────────────────────────────────────────
const summary = computed(() => {
  const d = props.data
  if (props.type === 'compare')      return `A ${d.operator ?? '>'} B`
  if (props.type === 'hysteresis')   return `ON≥${d.threshold_on ?? 25}  OFF≤${d.threshold_off ?? 20}`
  if (props.type === 'math_formula') return d.formula || 'a + b'
  if (props.type === 'math_map')     return `[${d.in_min ?? 0}‒${d.in_max ?? 100}] → [${d.out_min ?? 0}‒${d.out_max ?? 1}]`
  if (props.type === 'timer_delay')  return `${d.delay_s ?? 1} s`
  if (props.type === 'timer_pulse')  return `${d.duration_s ?? 1} s`
  if (props.type === 'timer_cron')   return d.cron || '0 7 * * *'
  if (props.type === 'mcp_tool')     return d.tool_name || '—'
  return null
})

// ── Layout constants ───────────────────────────────────────────────────────
const HEADER_H = 28   // px  header height
const SUMMARY_H = 20  // px  summary line height (only when present)
const PORT_H   = 22   // px  per port row height

const rowCount  = computed(() => Math.max(def.value.inputs.length, def.value.outputs.length, 1))
const summaryPx = computed(() => summary.value ? SUMMARY_H : 0)
const cardH     = computed(() => HEADER_H + summaryPx.value + rowCount.value * PORT_H + 8)

// port row indices (0..rowCount-1)
const portRows  = computed(() => Array.from({ length: rowCount.value }, (_, i) => i))

// ── Handle positioning — aligned with port rows ────────────────────────────
function hStyle(index, _total) {
  const bodyStart = HEADER_H + summaryPx.value
  const posY      = bodyStart + index * PORT_H + PORT_H / 2
  const topPct    = (posY / cardH.value * 100).toFixed(1)
  return {
    top:     topPct + '%',
    zIndex:  '100',
    width:   '12px',
    height:  '12px',
    background: '#94a3b8',
    border:  '2px solid #0f172a',
    borderRadius: '50%',
    cursor:  'crosshair',
  }
}

// ── Delete ─────────────────────────────────────────────────────────────────
const { removeNodes } = useVueFlow()
const hovered = ref(false)
function remove() { removeNodes([props.id]) }
</script>

<style scoped>
.gn-root  { position: relative; }

.gn-card  {
  min-width: 130px;
  border: 1px solid #334155;
  border-top: 3px solid #475569;
  border-radius: 8px;
  box-shadow: 0 4px 14px rgba(0,0,0,.5);
  background: #1e293b;
  overflow: visible;
}

.gn-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 10px;
  border-radius: 5px 5px 0 0;
}
.gn-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#f1f5f9; }
.gn-del   { font-size:11px; color:#64748b; background:none; border:none; cursor:pointer; padding:0 2px; line-height:1; transition:color .15s; }
.gn-del:hover { color:#f87171; }

.gn-body  { padding: 0; }

.gn-summary {
  font-size: 10px;
  color: #94a3b8;
  padding: 2px 10px;
  font-family: ui-monospace, monospace;
  border-bottom: 1px solid #263347;
}

.gn-ports-rows { padding: 0 10px; }

.gn-port-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.gn-port-left  { font-size: 9px; color: #64748b; }
.gn-port-right { font-size: 9px; color: #64748b; }

/* Output handles are blue — applied via class on Handle */
.gn-root :deep(.vue-flow__handle.gn-out) {
  background: #60a5fa !important;
}
.gn-root :deep(.vue-flow__handle:hover) {
  transform: translate(-50%, -50%) scale(1.4) !important;
  background: #38bdf8 !important;
}
</style>
