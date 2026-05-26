import { useConsoleStore } from '../stores/console'

/**
 * Log level types
 */
export type LogLevel = 'info' | 'success' | 'warning' | 'error'

/**
 * Where to send log messages
 */
export type LogDestination = 'both' | 'browserOnly' | 'uiOnly'

/**
 * Unified logging interface that routes to browser console and/or UI console
 *
 * @example
 * const logger = useLogger()
 *
 * // Logs to both browser DevTools and UI console
 * logger.info('Operation started')
 *
 * // Only in browser DevTools (hidden from user)
 * logger.debug('Full response object:', data)
 *
 * // Only in UI (user-facing notification)
 * logger.notify('Document saved successfully', 'success')
 */
export function useLogger() {
  const uiConsole = useConsoleStore()

  /**
   * Log a message with specified level and destination
   */
  function log(
    message: string,
    level: LogLevel = 'info',
    destination: LogDestination = 'both',
    data?: unknown,
  ): void {
    const shouldLogToBrowser = destination === 'both' || destination === 'browserOnly'
    const shouldLogToUI = destination === 'both' || destination === 'uiOnly'

    // Browser console (DevTools)
    if (shouldLogToBrowser) {
      const logMethod = getBrowserLogMethod(level)
      if (data !== undefined) {
        logMethod(message, data)
      }
      else {
        logMethod(message)
      }
    }

    // UI console (GlobalConsole.vue)
    if (shouldLogToUI) {
      uiConsole.log(message, level)
    }
  }

  /**
   * Info message (default: both consoles)
   */
  function info(message: string, destination: LogDestination = 'both', data?: unknown): void {
    log(message, 'info', destination, data)
  }

  // TODO: I think we should weed out some of the specialised message types
  /**
   * Success message (default: both consoles)
   */
  function success(message: string, destination: LogDestination = 'both', data?: unknown): void {
    log(message, 'success', destination, data)
  }

  /**
   * Warning message (default: both consoles)
   */
  function warn(message: string, destination: LogDestination = 'both', data?: unknown): void {
    log(message, 'warning', destination, data)
  }

  /**
   * Error message (default: both consoles)
   */
  function error(message: string, destination: LogDestination = 'both', errorData?: unknown): void {
    log(message, 'error', destination, errorData)
  }

  /**
   * Debug message (browser console only by default)
   * Use for technical details not relevant to users
   */
  function debug(message: string, data?: unknown): void {
    console.debug(message, data !== undefined ? data : '')
  }

  /**
   * User notification (UI console only by default)
   * Use for user-facing status updates
   */
  function notify(message: string, level: LogLevel = 'info'): void {
    log(message, level, 'uiOnly')
  }

  /**
   * Get appropriate browser console method for log level
   */
  function getBrowserLogMethod(level: LogLevel): (...args: unknown[]) => void {
    switch (level) {
      case 'error':
        return console.error
      case 'warning':
        return console.warn
      case 'info':
      case 'success':
      default:
        return console.log
    }
  }

  return {
    log,
    info,
    success,
    warn,
    error,
    debug,
    notify,
  }
}
