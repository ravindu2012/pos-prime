// Copyright (c) 2026, Ravindu Gajanayaka
// Licensed under GPLv3. See license.txt

import { reactive, computed } from 'vue'
import { createResource, call } from 'frappe-ui'

const user = createResource({
  url: 'frappe.auth.get_logged_user',
  cache: 'session-user',
})

export const session = reactive({
  user,
  isLoggedIn: computed(() =>
    user.data && user.data !== 'Guest' ? true : false
  ),
})
