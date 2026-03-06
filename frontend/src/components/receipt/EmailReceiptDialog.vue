<script setup lang="ts">
import { ref } from 'vue'
import { call } from 'frappe-ui'
import { X, Mail, Loader2 } from 'lucide-vue-next'
import { toast } from '@/composables/useToast'

const props = defineProps<{
  invoiceName: string
  defaultEmail?: string
}>()

const emit = defineEmits<{
  close: []
}>()

const email = ref(props.defaultEmail || '')
const message = ref('')
const sending = ref(false)

async function sendEmail() {
  if (!email.value.trim()) {
    toast.error('Please enter an email address')
    return
  }
  sending.value = true
  try {
    await call('pos_prime.api.orders.email_invoice', {
      invoice_name: props.invoiceName,
      recipient: email.value.trim(),
      content: message.value.trim(),
    })
    toast.success(`Receipt sent to ${email.value.trim()}`)
    emit('close')
  } catch (e: any) {
    toast.error(e.message || 'Failed to send email')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/30 dark:bg-black/50" @click="emit('close')" />
      <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-xl dark:shadow-black/30 w-full max-w-sm">
        <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Email Receipt</h3>
          <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <X :size="16" />
          </button>
        </div>

        <div class="p-4 space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Recipient Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="customer@example.com"
              class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500"
              @keydown.enter="sendEmail"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Message (optional)</label>
            <textarea
              v-model="message"
              rows="2"
              placeholder="Add a note..."
              class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500 resize-none"
            />
          </div>

          <button
            @click="sendEmail"
            :disabled="sending || !email.trim()"
            class="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Loader2 v-if="sending" :size="14" class="animate-spin" />
            <Mail v-else :size="14" />
            {{ sending ? 'Sending...' : 'Send Receipt' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
