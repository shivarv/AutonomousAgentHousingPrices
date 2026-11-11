/** Base URL for the backend API. Empty means same origin (Vite proxies /api in development). */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''
