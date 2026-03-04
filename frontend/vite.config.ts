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
      // Add theme attributes to <html> tag
      html = html.replace(
        '<html lang="en">',
        '<html lang="en" data-theme-mode="{{ desk_theme }}" data-theme="{{ desk_theme }}">'
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
          '../posify/www/posify.html'
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
