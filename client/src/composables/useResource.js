import { ref, watch, onMounted } from 'vue'

// Standardizes the loading/error/fetch scaffolding used across data views.
//
// The fetchFn does the actual work (calling the API and assigning to the
// view's own refs) so each view keeps its domain-specific state shape. This
// composable owns the loading flag, error handling, the optional reload-on-
// change watch, and the initial mount fetch.
//
// Options:
//   watchSources  - reactive sources that should trigger a reload when they change
//   immediate     - fetch on mount (default true)
//   errorMessage  - prefix for the error string (kept per-view to preserve UX)
//
// Returns { loading, error, reload }. `error` is reset on every reload, so a
// prior failure clears once a subsequent fetch succeeds.
export function useResource(fetchFn, { watchSources = [], immediate = true, errorMessage = 'Failed to load data' } = {}) {
  const loading = ref(true)
  const error = ref(null)

  const reload = async () => {
    try {
      loading.value = true
      error.value = null
      await fetchFn()
    } catch (err) {
      error.value = `${errorMessage}: ${err.message}`
    } finally {
      loading.value = false
    }
  }

  if (watchSources.length) {
    watch(watchSources, reload)
  }

  if (immediate) {
    onMounted(reload)
  }

  return { loading, error, reload }
}
