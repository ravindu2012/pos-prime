import path from 'path'
import { defineConfig, Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import Icons from 'unplugin-icons/vite'

// Inject Frappe context into built HTML.
// Frappe processes www/*.html through Jinja, so {{ }} syntax
// gets replaced with actual values at serve time.
function injectFrappeContext(): Plugin {
  return {
    name: 'inject-frappe-context',
    apply: 'build',
    transformIndexHtml(html) {
      // Fetch user theme + Website Settings via Jinja (www pages don't have desk_theme in context)
      const jinjaBlock = [
        '{%- set _user_theme = (frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light").lower() -%}',
        '{%- set ws = frappe.get_doc("Website Settings") -%}',
      ].join('\n')

      // Add theme attributes to <html> tag
      html = html.replace(
        '<html lang="en">',
        jinjaBlock + '\n<html lang="en" data-theme-mode="{{ _user_theme }}" data-theme="{{ _user_theme }}">'
      )

      // Inject title + favicon from Website Settings
      html = html.replace(
        '<title>POS Prime</title>',
        [
          '<title>{{ ws.app_name or "POS Prime" }}</title>',
          '  {% if ws.favicon %}<link rel="icon" href="{{ ws.favicon }}">{% endif %}',
        ].join('\n  ')
      )

      // Inject CSRF token + theme auto-detection script
      html = html.replace(
        '</head>',
        [
          '  <script>window.csrf_token = "{{ frappe.session.csrf_token }}";</script>',
          '  <script>',
          '    (function() {',
          '      var m = document.documentElement.getAttribute("data-theme-mode");',
          '      if (m === "automatic") {',
          '        var q = window.matchMedia("(prefers-color-scheme: dark)");',
          '        document.documentElement.setAttribute("data-theme", q.matches ? "dark" : "light");',
          '        q.addEventListener("change", function(e) {',
          '          document.documentElement.setAttribute("data-theme", e.matches ? "dark" : "light");',
          '        });',
          '      }',
          '    })();',
          '  </script>',
          '  </head>',
        ].join('\n')
      )

      return html
    },
  }
}

export default defineConfig({
  plugins: [
    frappeui({
      buildConfig: {
        indexHtmlPath: path.resolve(
          __dirname,
          '../pos_prime/www/pos_prime.html'
        ),
      },
    }),
    vue(),
    Icons({
      autoInstall: true,
      compiler: 'vue3',
    }),
    injectFrappeContext(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client'],
  },
})
