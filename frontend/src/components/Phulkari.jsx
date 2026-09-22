// Phulkari-inspired woven pattern: the one bold decorative element of the site.
// Diamonds (lozenges) in mustard, rani pink and white on field green, like the
// darning-stitch embroidery of Punjab.
export function PhulkariDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true" focusable="false">
      <defs>
        <pattern id="phulkari" width="36" height="36" patternUnits="userSpaceOnUse">
          <rect width="36" height="36" fill="var(--pk-ground)" />
          <path d="M18 2 34 18 18 34 2 18Z" fill="none" stroke="var(--pk-line)" strokeWidth="2.2" />
          <path d="M18 9 27 18 18 27 9 18Z" fill="var(--pk-accent)" />
          <path d="M18 14 22 18 18 22 14 18Z" fill="var(--pk-light)" />
          <g fill="var(--pk-line)">
            <rect x="-1.5" y="-1.5" width="3" height="3" transform="rotate(45)" />
            <rect x="34.5" y="-1.5" width="3" height="3" transform="rotate(45 36 0)" />
            <rect x="-1.5" y="34.5" width="3" height="3" transform="rotate(45 0 36)" />
            <rect x="34.5" y="34.5" width="3" height="3" transform="rotate(45 36 36)" />
          </g>
        </pattern>
      </defs>
    </svg>
  )
}

/** A strip of the woven pattern. Pass a height in px. */
export function PhulkariBand({ height = 36, className = '' }) {
  return (
    <svg className={`phulkari-band ${className}`} width="100%" height={height} aria-hidden="true" focusable="false">
      <rect width="100%" height="100%" fill="url(#phulkari)" />
    </svg>
  )
}

/** A filled panel of the woven pattern (used behind the hero conversation). */
export function PhulkariPanel({ className = '' }) {
  return (
    <svg className={`phulkari-panel ${className}`} width="100%" height="100%" aria-hidden="true" focusable="false">
      <rect width="100%" height="100%" fill="url(#phulkari)" />
    </svg>
  )
}
