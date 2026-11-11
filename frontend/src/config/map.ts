import type { LatLngBoundsExpression } from 'leaflet'

/** Bounding box of Massachusetts (approximate view extent, not data). */
export const MASSACHUSETTS_BOUNDS: LatLngBoundsExpression = [
  [41.18, -73.55],
  [42.9, -69.85],
]

export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
export const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
