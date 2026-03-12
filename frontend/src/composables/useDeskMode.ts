// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { ref, readonly } from 'vue'

const _isDeskMode = ref(false)

export function setDeskMode(value: boolean) {
  _isDeskMode.value = value
}

export function useDeskMode() {
  return { isDeskMode: readonly(_isDeskMode) }
}
