<template>
  <div ref="viewerEl" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import '@toast-ui/editor/dist/toastui-editor.css'
import 'highlight.js/styles/github.css'
import Viewer from '@toast-ui/editor/dist/toastui-editor-viewer'
import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight'
import hljs from 'highlight.js'

const model = defineModel({ type: String, default: '' })

const props = defineProps({
  options: { type: Object, default: () => ({}) },
  mode: { type: String, default: 'markdown' },
  height: { type: String, default: '300px' },
  language: { type: String, default: 'en_US' },
})

const emit = defineEmits(['input'])

const viewerEl = ref(null)
let viewer = null

const defaultOptions = {
  minHeight: '500px',
  previewStyle: 'vertical',
  useCommandShortcut: true,
  useDefaultHTMLSanitizer: true,
  usageStatistics: false,
  hideModeSwitch: false,
  plugins: [[codeSyntaxHighlight, { hljs }]],
  toolbarItems: [
    'heading', 'bold', 'italic', 'strike', 'divider', 'hr', 'quote', 'divider',
    'ul', 'ol', 'task', 'indent', 'outdent', 'divider', 'table', 'image', 'link',
    'divider', 'code', 'codeblock',
  ],
}

function initViewer() {
  if (!viewerEl.value) return

  const viewerOptions = {
    el: viewerEl.value,
    ...defaultOptions,
    ...props.options,
    initialEditType: props.mode,
    height: props.height,
    language: props.language,
    initialValue: model.value || '',
  }

  viewer = new Viewer(viewerOptions)
}

function destroyViewer() {
  if (!viewer) return
  viewer.destroy()
  viewer = null
}

function setValue(value) {
  if (viewer) viewer.setValue(value)
}

function getValue() {
  return viewer ? viewer.getValue() : ''
}

function setHtml(value) {
  if (viewer) viewer.setHtml(value)
}

function getHtml() {
  return viewer ? viewer.getHtml() : ''
}

watch(
  () => model.value,
  (newValue) => {
    if (viewer && newValue !== viewer.getValue()) {
      viewer.setValue(newValue)
    }
  }
)

watch(() => props.language, () => {
  destroyViewer()
  initViewer()
})

watch(() => props.height, (newValue) => {
  if (viewer) viewer.height(newValue)
})

onMounted(() => {
  initViewer()
})

onBeforeUnmount(() => {
  destroyViewer()
})
</script>
