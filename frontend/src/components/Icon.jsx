// Hand-drawn 24px stroke icons. One small file instead of an icon library.
const PATHS = {
  'arrow-right': <path d="M5 12h14M13 6l6 6-6 6" />,
  'arrow-left': <path d="M19 12H5M11 6l-6 6 6 6" />,
  search: <><circle cx="11" cy="11" r="6.5" /><path d="M20 20l-4-4" /></>,
  mic: <><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></>,
  send: <path d="M21 3 10 14M21 3l-7 18-4-8-8-4 19-6z" />,
  external: <path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  chat: <path d="M4 5h16v11H9l-5 4z" />,
  check: <path d="M5 12.5l4.5 4.5L19 7" />,
  'check-circle': <><circle cx="12" cy="12" r="9" /><path d="M8 12.5l3 3 5-6" /></>,
  'x-circle': <><circle cx="12" cy="12" r="9" /><path d="M9 9l6 6M15 9l-6 6" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.5v.5" /></>,
  help: <><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1.9-1.1 1.8M12 16.5v.5" /></>,
  speaker: <><path d="M4 9v6h4l5 4V5L8 9z" /><path d="M16.5 8.5a5 5 0 0 1 0 7" /></>,
  copy: <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a1 1 0 0 1 1-1h10" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  shield: <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />,
  globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3.5 3 14 0 18M12 3c-3 3.5-3 14 0 18" /></>,
  doc: <><path d="M7 3h7l5 5v13H7z" /><path d="M14 3v5h5M10 13h6M10 17h6" /></>,
  chevron: <path d="M6 9l6 6 6-6" />,
  stop: <rect x="6.5" y="6.5" width="11" height="11" rx="2" />,
  // category glyphs
  rings: <><circle cx="9" cy="14" r="5" /><circle cx="15" cy="14" r="5" /><path d="M12 3.5l1.6 2.4L12 8.3 10.4 5.9z" /></>,
  family: <><circle cx="8" cy="7" r="3" /><circle cx="17" cy="9.5" r="2.4" /><path d="M2.5 20a5.5 5.5 0 0 1 11 0M14 20a4 4 0 0 1 7.5 0" /></>,
  elder: <><circle cx="10" cy="5" r="2.4" /><path d="M10 8.5v5.5l-2.5 6.5M10 14l3 6.5M6.5 11.5H13M18 10v10.5" /></>,
  briefcase: <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 13h18" /></>,
  cap: <><path d="M2 9l10-5 10 5-10 5z" /><path d="M6 11.5V16c0 1.5 3 3 6 3s6-1.5 6-3v-4.5M22 9v6" /></>,
  wheat: <><path d="M12 21V9" /><path d="M12 9c-2.8 0-4-1.8-4-4 2.8 0 4 1.8 4 4zM12 9c2.8 0 4-1.8 4-4-2.8 0-4 1.8-4 4zM12 15c-2.8 0-4-1.8-4-4 2.8 0 4 1.8 4 4zM12 15c2.8 0 4-1.8 4-4-2.8 0-4 1.8-4 4z" /></>,
}

export default function Icon({ name, size = 20, className = '', ...rest }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
      className={`icon ${className}`} aria-hidden="true" focusable="false" {...rest}
    >
      {PATHS[name] || PATHS.doc}
    </svg>
  )
}
