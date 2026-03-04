<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePosSessionStore } from '@/stores/posSession'
import { useSettingsStore } from '@/stores/settings'
import { useCurrency } from '@/composables/useCurrency'
import { LogIn } from 'lucide-vue-next'

const router = useRouter()
const sessionStore = usePosSessionStore()
const settingsStore = useSettingsStore()
const { formatCurrency } = useCurrency()

const selectedProfile = ref('')
const company = ref('')
const openingBalances = ref<{ mode_of_payment: string; opening_amount: number }[]>([])
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  const data = await settingsStore.fetchPOSProfiles()
  if (data?.openEntry) {
    router.replace('/posify')
    return
  }
  if (settingsStore.posProfiles.length === 1) {
    selectedProfile.value = settingsStore.posProfiles[0].name
    company.value = settingsStore.posProfiles[0].company
    await loadProfilePaymentMethods()
  }
})

async function onProfileChange() {
  const profile = settingsStore.posProfiles.find(
    (p) => p.name === selectedProfile.value
  )
  if (profile) {
    company.value = profile.company
    await loadProfilePaymentMethods()
  }
}

async function loadProfilePaymentMethods() {
  if (!selectedProfile.value) {
    openingBalances.value = []
    return
  }
  try {
    await settingsStore.loadPOSProfile(selectedProfile.value)
    const methods = settingsStore.paymentMethods
    openingBalances.value = methods.map((pm) => ({
      mode_of_payment: pm.mode_of_payment,
      opening_amount: 0,
    }))
  } catch {
    openingBalances.value = [{ mode_of_payment: 'Cash', opening_amount: 0 }]
  }
}

async function openShift() {
  if (!selectedProfile.value) {
    error.value = 'Please select a POS Profile'
    return
  }
  // Validate opening balances are non-negative
  for (const balance of openingBalances.value) {
    if (balance.opening_amount < 0) {
      error.value = 'Opening amounts cannot be negative'
      return
    }
  }
  loading.value = true
  error.value = ''
  try {
    await sessionStore.createOpeningEntry({
      pos_profile: selectedProfile.value,
      company: company.value,
      balance_details: openingBalances.value,
    })
    await settingsStore.loadPOSProfile(selectedProfile.value)
    router.replace('/posify')
  } catch (e: any) {
    error.value = e.messages?.[0] || e.message || 'Failed to open shift'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
      <div class="flex items-center gap-3 mb-6">
        <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/30">
          <LogIn class="text-blue-600 dark:text-blue-400" :size="20" />
        </div>
        <div>
          <h1 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Open POS Shift</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Select profile and enter opening balances</p>
        </div>
      </div>

      <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg text-sm">
        {{ error }}
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            POS Profile
          </label>
          <select
            v-model="selectedProfile"
            @change="onProfileChange"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select Profile...</option>
            <option
              v-for="profile in settingsStore.posProfiles"
              :key="profile.name"
              :value="profile.name"
            >
              {{ profile.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Company
          </label>
          <input
            :value="company"
            readonly
            class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-600 dark:text-gray-400"
          />
        </div>

        <!-- Opening balances for each payment method -->
        <div v-if="openingBalances.length > 0">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Opening Balances
          </label>
          <div class="space-y-2">
            <div
              v-for="(balance, index) in openingBalances"
              :key="balance.mode_of_payment"
              class="flex items-center gap-3"
            >
              <span class="text-sm text-gray-600 dark:text-gray-400 w-28 shrink-0">
                {{ balance.mode_of_payment }}
              </span>
              <input
                v-model.number="openingBalances[index].opening_amount"
                type="number"
                min="0"
                step="0.01"
                class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
              />
            </div>
          </div>
        </div>

        <button
          @click="openShift"
          :disabled="loading || !selectedProfile"
          class="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ loading ? 'Opening...' : 'Open Shift' }}
        </button>
      </div>
    </div>
  </div>
</template>
