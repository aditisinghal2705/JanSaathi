// // // All network calls live here.
// // Development: Vite proxies /api -> http://localhost:8002
// // Production: FastAPI serves both the site and API from one origin.

// const BASE = import.meta.env.VITE_API_URL ?? ''

// export class ApiError extends Error {
//   constructor(message, status) {
//     super(message)
//     this.status = status
//   }
// }

// async function request(path, options = {}) {
//   let res

//   try {
//     res = await fetch(`${BASE}${path}`, {
//       headers: {
//         'Content-Type': 'application/json',
//         ...(options.headers || {}),
//       },
//       ...options,
//     })
//   } catch (err) {
//     if (err.name === 'AbortError') {
//       throw err
//     }

//     throw new ApiError('offline', 0)
//   }

//   if (!res.ok) {
//     let message = res.statusText || 'error'

//     try {
//       const data = await res.json()

//       if (data?.detail) {
//         message = data.detail
//       }
//     } catch {
//       // Ignore JSON parsing errors
//     }

//     throw new ApiError(message, res.status)
//   }

//   return res.json()
// }

// const post = (path, body, signal) =>
//   request(path, {
//     method: 'POST',
//     body: JSON.stringify(body),
//     signal,
//   })

// export const api = {
//   health: () => request('/api/health'),

//   categories: () => request('/api/categories'),

//   schemes: ({ category, search } = {}) => {
//     const q = new URLSearchParams()

//     if (category) {
//       q.set('category', category)
//     }

//     if (search) {
//       q.set('search', search)
//     }

//     const qs = q.toString()

//     return request(`/api/schemes${qs ? `?${qs}` : ''}`)
//   },

//   scheme: (id) =>
//     request(`/api/schemes/${encodeURIComponent(id)}`),

//   eligibility: (body) =>
//     post('/api/eligibility', body),

//   chat: (body, signal) =>
//     post('/api/chat', body, signal),
// }


// /*
//  * Chat interface used by the frontend.
//  *
//  * IMPORTANT:
//  * We are temporarily using /api/chat instead of
//  * /api/chat/stream because the backend streaming endpoint
//  * is currently returning HTTP 500.
//  *
//  * The normal /api/chat endpoint has already been tested
//  * successfully and returns HTTP 200.
//  */
// export async function streamChat(
//   body,
//   { onMeta, onDelta, onDone, signal } = {}
// ) {
//   const data = await api.chat(body, signal)

//   // Send metadata to the UI
//   onMeta?.({
//     matched_schemes: data.matched_schemes || [],
//     provider: data.provider,
//   })

//   // Send the complete response as one chunk
//   if (data.reply) {
//     onDelta?.(data.reply)
//   }

//   // Tell the UI that the response is finished
//   onDone?.({
//     suggestions: data.suggestions || [],
//     provider: data.provider,
//     degraded: data.degraded,
//   })
// }
// ============================================================
// JanSaathi API Client
// Development:
//   Vite proxies /api -> http://localhost:8002
//
// Production:
//   FastAPI serves both frontend and API from the same origin.
// ============================================================

const BASE = import.meta.env.VITE_API_URL ?? ''


// ============================================================
// API ERROR
// ============================================================

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}


// ============================================================
// SANITIZE CHAT HISTORY
// Backend allows maximum 4000 characters per message.
// We also limit the number of previous messages so the
// request does not become unnecessarily large.
// ============================================================

function sanitizeChatBody(body) {
  const history = Array.isArray(body?.history)
    ? body.history
        .filter(
          (message) =>
            message &&
            typeof message.content === 'string'
        )
        .map((message) => ({
          role: message.role,
          content: message.content.slice(0, 4000),
        }))
        .slice(-10)
    : []

  return {
    ...body,
    history,
  }
}


// ============================================================
// GENERIC REQUEST
// ============================================================

async function request(path, options = {}) {
  let res

  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,

      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    })
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw err
    }

    throw new ApiError(
      'Cannot connect to the server.',
      0
    )
  }


  // ----------------------------------------------------------
  // Handle HTTP errors
  // ----------------------------------------------------------

  if (!res.ok) {
    let message = res.statusText || 'Request failed'

    try {
      const data = await res.json()

      if (Array.isArray(data?.detail)) {
        message = data.detail
          .map((item) => {
            if (item?.msg) {
              return item.msg
            }

            return JSON.stringify(item)
          })
          .join(', ')
      } else if (typeof data?.detail === 'string') {
        message = data.detail
      }
    } catch {
      // Response was not JSON
    }

    throw new ApiError(message, res.status)
  }


  // ----------------------------------------------------------
  // Parse JSON
  // ----------------------------------------------------------

  try {
    return await res.json()
  } catch {
    throw new ApiError(
      'Server returned an invalid response.',
      res.status
    )
  }
}


// ============================================================
// POST HELPER
// ============================================================

function post(path, body, signal) {
  return request(path, {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  })
}


// ============================================================
// PUBLIC API
// ============================================================

export const api = {

  // ----------------------------------------------------------
  // Health
  // GET /api/health
  // ----------------------------------------------------------

  health: () =>
    request('/api/health'),


  // ----------------------------------------------------------
  // Categories
  // GET /api/categories
  // ----------------------------------------------------------

  categories: () =>
    request('/api/categories'),


  // ----------------------------------------------------------
  // Schemes
  // GET /api/schemes
  // ----------------------------------------------------------

  schemes: ({ category, search } = {}) => {

    const params = new URLSearchParams()

    if (category) {
      params.set('category', category)
    }

    if (search) {
      params.set('search', search)
    }

    const query = params.toString()

    const path = query
      ? `/api/schemes?${query}`
      : '/api/schemes'

    return request(path)
  },


  // ----------------------------------------------------------
  // Single scheme
  // GET /api/schemes/:id
  // ----------------------------------------------------------

  scheme: (id) =>
    request(
      `/api/schemes/${encodeURIComponent(id)}`
    ),


  // ----------------------------------------------------------
  // Eligibility
  // POST /api/eligibility
  // ----------------------------------------------------------

  eligibility: (body) =>
    post('/api/eligibility', body),


  // ----------------------------------------------------------
  // Normal Chat
  // POST /api/chat
  // ----------------------------------------------------------

  chat: (body, signal) => {

    const safeBody = sanitizeChatBody(body)

    return post(
      '/api/chat',
      safeBody,
      signal
    )
  },
}


// ============================================================
// CHAT
//
// We are intentionally using /api/chat instead of
// /api/chat/stream because normal /api/chat is working.
// ============================================================

export async function streamChat(
  body,
  {
    onMeta,
    onDelta,
    onDone,
    signal,
  } = {}
) {

  // ----------------------------------------------------------
  // Sanitize BEFORE sending to backend
  // ----------------------------------------------------------

  const safeBody = sanitizeChatBody(body)


  // ----------------------------------------------------------
  // Call backend
  // ----------------------------------------------------------

  const data = await api.chat(
    safeBody,
    signal
  )


  // ----------------------------------------------------------
  // Send metadata to UI
  // ----------------------------------------------------------

  onMeta?.({
    matched_schemes:
      data?.matched_schemes || [],

    provider:
      data?.provider || null,
  })


  // ----------------------------------------------------------
  // Send answer
  // ----------------------------------------------------------

  if (typeof data?.reply === 'string') {
    onDelta?.(data.reply)
  }


  // ----------------------------------------------------------
  // Tell UI that response is complete
  // ----------------------------------------------------------

  onDone?.({
    suggestions:
      data?.suggestions || [],

    provider:
      data?.provider || null,

    degraded:
      data?.degraded ?? false,
  })
}