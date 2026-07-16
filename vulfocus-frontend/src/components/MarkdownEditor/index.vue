<template>
  <div ref="editorEl" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import '@toast-ui/editor/dist/toastui-editor.css'
import 'highlight.js/styles/github.css'
import Editor from '@toast-ui/editor'
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

const editorEl = ref(null)
let editor = null

const defaultOptions = {
  minHeight: '500px',
  previewStyle: 'vertical',
  useCommandShortcut: true,
  useDefaultHTMLSanitizer: true,
  usageStatistics: false,
  hideModeSwitch: false,
  toolbarItems: [
    'heading', 'bold', 'italic', 'strike', 'divider', 'hr', 'quote', 'divider',
    'ul', 'ol', 'task', 'indent', 'outdent', 'divider', 'table', 'image', 'link',
    'divider', 'code', 'codeblock',
  ],
  plugins: [[codeSyntaxHighlight, { hljs }]],
}

function initEditor() {
  if (!editorEl.value) return

  const editorOptions = {
    el: editorEl.value,
    ...defaultOptions,
    ...props.options,
    initialEditType: props.mode,
    height: props.height,
    language: props.language,
    initialValue: model.value || '',
  }

  editor = new Editor(editorOptions)

  editor.on('change', () => {
    const val = editor.getValue()
    emit('input', val)
    model.value = val
  })
}

function destroyEditor() {
  if (!editor) return
  editor.off('change')
  editor.destroy()
  editor = null
}

function setValue(value) {
  if (editor) editor.setValue(value)
}

function getValue() {
  return editor ? editor.getValue() : ''
}

function setHtml(value) {
  if (editor) editor.setHtml(value)
}

function getHtml() {
  return editor ? editor.getHtml() : ''
}

watch(
  () => model.value,
  (newValue) => {
    if (editor && newValue !== editor.getValue()) {
      editor.setValue(newValue)
    }
  }
)

watch(() => props.language, () => {
  destroyEditor()
  initEditor()
})

watch(() => props.height, (newValue) => {
  if (editor) editor.height(newValue)
})

watch(() => props.mode, (newValue) => {
  if (editor) editor.changeMode(newValue)
})

onMounted(() => {
  initEditor()
})

onBeforeUnmount(() => {
  destroyEditor()
})
</script>
