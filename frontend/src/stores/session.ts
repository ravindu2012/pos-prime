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
