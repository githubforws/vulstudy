<template>
  <div class="verification-wrap">
    <canvas
      ref="canvasRef"
      :width="width"
      :height="height"
      class="verification-canvas"
      @click="refreshCode"
    />
    <el-button v-if="showRefresh" link type="primary" size="small" @click="refreshCode" class="refresh-btn">
      看不清？换一张
    </el-button>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  width: { type: Number, default: 120 },
  height: { type: Number, default: 40 },
  showRefresh: { type: Boolean, default: true },
})

const emit = defineEmits(['update:code'])

const canvasRef = ref(null)
const code = ref('')

// Characters excluding confusing ones (0,O,1,l,I)
const chars = '23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ'

function randomNum(min, max) {
  return Math.floor(Math.random() * (max - min) + min)
}

function randomColor(min = 64, max = 255) {
  const r = randomNum(min, max)
  const g = randomNum(min, max)
  const b = randomNum(min, max)
  return `rgb(${r},${g},${b})`
}

function drawCode() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  // Background
  ctx.fillStyle = randomColor(220, 255)
  ctx.fillRect(0, 0, props.width, props.height)

  // Generate 4-char code
  let text = ''
  for (let i = 0; i < 4; i++) {
    text += chars[randomNum(0, chars.length)]
  }
  code.value = text
  emit('update:code', text)

  // Draw characters
  const charSpacing = props.width / (text.length + 1)
  for (let i = 0; i < text.length; i++) {
    ctx.font = `${randomNum(20, 28)}px "Comic Sans MS", sans-serif`
    ctx.fillStyle = randomColor(30, 160)
    ctx.textBaseline = 'middle'
    ctx.textAlign = 'center'
    const x = charSpacing * (i + 1) + randomNum(-5, 5)
    const y = props.height / 2 + randomNum(-5, 5)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate((randomNum(-30, 30) * Math.PI) / 180)
    ctx.fillText(text[i], 0, 0)
    ctx.restore()
  }

  // Interference lines
  for (let i = 0; i < 3; i++) {
    ctx.beginPath()
    ctx.moveTo(randomNum(0, props.width), randomNum(0, props.height))
    ctx.lineTo(randomNum(0, props.width), randomNum(0, props.height))
    ctx.strokeStyle = randomColor(100, 200)
    ctx.lineWidth = randomNum(1, 2)
    ctx.stroke()
  }

  // Interference dots
  for (let i = 0; i < 40; i++) {
    ctx.beginPath()
    ctx.arc(randomNum(0, props.width), randomNum(0, props.height), 1, 0, 2 * Math.PI)
    ctx.fillStyle = randomColor(150, 220)
    ctx.fill()
  }
}

function refreshCode() {
  drawCode()
}

defineExpose({ refreshCode })

onMounted(() => {
  drawCode()
})
</script>

<style lang="scss" scoped>
.verification-wrap {
  display: flex;
  align-items: center;
  gap: 10px;

  .verification-canvas {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    cursor: pointer;
  }

  .refresh-btn {
    padding: 0;
  }
}
</style>
