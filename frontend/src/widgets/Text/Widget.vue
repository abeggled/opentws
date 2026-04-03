<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { DataPointValue } from '@/types'

const props = defineProps<{
  config: Record<string, unknown>
  datapointId: string | null
  value: DataPointValue | null
  statusValue: DataPointValue | null
  editorMode: boolean
}>()

const content   = computed(() => (props.config.content  as string | undefined) ?? '')
const align     = computed(() => (props.config.align    as string | undefined) ?? 'left')
const fontSize  = computed(() => (props.config.fontSize as string | undefined) ?? 'base')

const fontSizeClass = computed(() => ({
  xs:   'text-xs',
  sm:   'text-sm',
  base: 'text-base',
  lg:   'text-lg',
  xl:   'text-xl',
  '2xl': 'text-2xl',
}[fontSize.value] ?? 'text-base'))

const alignClass = computed(() => ({
  left:    'text-left',
  center:  'text-center',
  right:   'text-right',
}[align.value] ?? 'text-left'))

const html = computed(() => {
  const raw = content.value.trim()
  if (!raw) return ''
  return marked.parse(raw) as string
})
</script>

<template>
  <div
    class="h-full w-full overflow-auto p-3"
    :class="[fontSizeClass, alignClass]"
  >
    <div
      v-if="html"
      class="markdown-body"
      v-html="html"
    />
    <span v-else class="text-gray-400 dark:text-gray-600 text-sm italic">Kein Text</span>
  </div>
</template>

<style scoped>
.markdown-body :deep(h1) { font-size: 1.75em; font-weight: 700; margin: 0.5em 0; }
.markdown-body :deep(h2) { font-size: 1.4em;  font-weight: 700; margin: 0.5em 0; }
.markdown-body :deep(h3) { font-size: 1.15em; font-weight: 600; margin: 0.4em 0; }
.markdown-body :deep(p)  { margin: 0.4em 0; line-height: 1.6; }

.markdown-body :deep(ul) { list-style: disc;    padding-left: 1.5em; margin: 0.4em 0; }
.markdown-body :deep(ol) { list-style: decimal; padding-left: 1.5em; margin: 0.4em 0; }
.markdown-body :deep(li) { margin: 0.15em 0; }

.markdown-body :deep(a)  {
  color: #60a5fa;
  text-decoration: underline;
}
.markdown-body :deep(a:hover) { color: #93c5fd; }

.markdown-body :deep(code) {
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
  background: rgba(0,0,0,0.2);
  border-radius: 3px;
  padding: 0.1em 0.35em;
}

.markdown-body :deep(pre) {
  background: rgba(0,0,0,0.25);
  border-radius: 6px;
  padding: 0.75em 1em;
  overflow-x: auto;
  margin: 0.5em 0;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
}

.markdown-body :deep(strong) { font-weight: 700; }
.markdown-body :deep(em)     { font-style: italic; }

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(128,128,128,0.3);
  margin: 0.75em 0;
}
</style>
