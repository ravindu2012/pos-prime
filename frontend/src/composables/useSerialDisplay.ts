import { ref, computed } from 'vue'

// Standard VFD/ESC-POS commands
const CMD_CLEAR = new Uint8Array([0x0c]) // Form feed - clear display
const CMD_INIT = new Uint8Array([0x1b, 0x40]) // ESC @ - initialize
const CMD_HOME = new Uint8Array([0x1b, 0x5b, 0x48]) // ESC [ H - cursor home

const LINE_WIDTH = 20

function formatLine(text: string): string {
  const clean = text.normalize('NFKD').replace(/[^\x20-\x7E]/g, '')
  if (clean.length > LINE_WIDTH) return clean.substring(0, LINE_WIDTH)
  return clean.padEnd(LINE_WIDTH, ' ')
}

// Shared state (singleton) so all components see the same connection
const port = ref<SerialPort | null>(null)
const writer = ref<WritableStreamDefaultWriter<Uint8Array> | null>(null)
const isConnected = ref(false)
const baudRate = ref(9600)

const isSupported = computed(() => 'serial' in navigator)

async function sendRaw(data: Uint8Array) {
  if (!writer.value) return
  try {
    await writer.value.write(data)
  } catch {
    isConnected.value = false
  }
}

async function connect(baud?: number) {
  if (!isSupported.value) return
  if (baud) baudRate.value = baud

  try {
    const selectedPort = await navigator.serial.requestPort()
    await selectedPort.open({ baudRate: baudRate.value })

    port.value = selectedPort
    if (selectedPort.writable) {
      writer.value = selectedPort.writable.getWriter()
    }
    isConnected.value = true

    await sendRaw(CMD_INIT)
    await sendRaw(CMD_CLEAR)
  } catch {
    port.value = null
    writer.value = null
    isConnected.value = false
  }
}

async function disconnect() {
  try {
    if (writer.value) {
      await sendRaw(CMD_CLEAR)
      writer.value.releaseLock()
      writer.value = null
    }
    if (port.value) {
      await port.value.close()
      port.value = null
    }
  } catch {
    // ignore close errors
  } finally {
    isConnected.value = false
  }
}

async function sendToVFD(line1: string, line2: string) {
  if (!isConnected.value || !writer.value) return

  const formatted = formatLine(line1) + formatLine(line2)
  const encoder = new TextEncoder()

  await sendRaw(CMD_HOME)
  await sendRaw(encoder.encode(formatted))
}

async function clearDisplay() {
  if (!isConnected.value) return
  await sendRaw(CMD_CLEAR)
}

export function useSerialDisplay() {
  return {
    connect,
    disconnect,
    sendToVFD,
    clearDisplay,
    isConnected,
    isSupported,
    baudRate,
  }
}
