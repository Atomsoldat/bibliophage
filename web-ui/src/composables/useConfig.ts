import { readonly, ref } from 'vue'

/**
 * Application configuration interface
 */
export interface AppConfig {
  backendHost: string
}

/**
 * Hardcoded fallback values
 */
const HARDCODED_DEFAULTS: AppConfig = {
  backendHost: 'http://localhost:8000',
}

// Shared state across all component instances
const config = ref<AppConfig>({ ...HARDCODED_DEFAULTS })
const isLoaded = ref(false)
const isLoading = ref(false)
const error = ref<Error | null>(null)

/**
 * Composable for accessing application configuration
 *
 * Loads configuration with the following precedence:
 * 1. Environment variables (highest priority)
 * 2. Runtime config file (/config.json)
 * 3. Hardcoded defaults (lowest priority)
 *
 * Configuration is loaded once and shared across all components.
 *
 * @example
 * const { config, loadConfig, isLoaded } = useConfig()
 * await loadConfig()
 * const client = createClient(PdfService, createConnectTransport({ baseUrl: config.backendHost }))
 */
export function useConfig() {
  /**
   * Load configuration from /config.json and environment variables
   * Safe to call multiple times - will only fetch once
   */
  async function loadConfig(): Promise<void> {
    // Skip if already loaded or currently loading
    if (isLoaded.value || isLoading.value) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      // Start with hardcoded defaults
      let loadedConfig: AppConfig = { ...HARDCODED_DEFAULTS }

      // Layer 2: Try to load from config.json
      try {
        const response = await fetch('/config.json')
        if (response.ok) {
          const fileConfig = await response.json() as Partial<AppConfig>
          loadedConfig = {
            ...loadedConfig,
            ...fileConfig,
          }
        }
      }
      catch (err) {
        // we convert whatever is thrown into a strictly formated Error
        // technically, something entirely different could be thrown, so this
        // guards against that
        error.value = err instanceof Error ? err : new Error(String(err))
        console.error('Failed to load config file:', error.value.message)
        console.warn('config.json not available, using defaults and environment variables')
      }

      // Layer 3: Environment variables override everything (highest priority)
      const envBackendHost = import.meta.env.VITE_BACKEND_HOST
      if (envBackendHost) {
        loadedConfig.backendHost = envBackendHost
      }

      config.value = loadedConfig
      isLoaded.value = true
    }
    catch (err) {
      error.value = err instanceof Error ? err : new Error(String(err))
      console.error('Failed to load config:', error.value.message)

      // TODO: do we really want to have some kind of hard coded stuff in the code?
      // It sounds convenient, but it  might also surprise people
      config.value = { ...HARDCODED_DEFAULTS }
      isLoaded.value = true
    }
    finally {
      isLoading.value = false
    }
  }

  return {
    config: readonly(config),
    isLoaded: readonly(isLoaded),
    isLoading: readonly(isLoading),
    error: readonly(error),
    loadConfig,
  }
}
