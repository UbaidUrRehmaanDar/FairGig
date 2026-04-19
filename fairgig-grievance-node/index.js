const path = require('node:path')
const express = require('express')
const cors = require('cors')
const { Pool } = require('pg')
require('dotenv').config()
require('dotenv').config({ path: path.join(__dirname, '..', 'fairgig-backend', '.env') })

const app = express()
const port = Number(process.env.PORT || 3002)

const HEALTH_ROUTES = ['/health', '/api/health']
const GRIEVANCES_COLLECTION_ROUTES = ['/grievances', '/api/grievances']
const GRIEVANCES_UPVOTE_ROUTES = [
  '/grievances/:grievance_id/upvote',
  '/api/grievances/:grievance_id/upvote',
]
const GRIEVANCES_ESCALATE_ROUTES = [
  '/grievances/:grievance_id/escalate',
  '/api/grievances/:grievance_id/escalate',
]

const parseOriginList = (value) => String(value || '')
  .split(',')
  .map((item) => item.trim().replace(/\/$/, ''))
  .filter(Boolean)

const defaultAllowedOrigins = [
  'http://localhost:3000',
  'http://localhost:3001',
  'http://localhost:3002',
  'http://localhost:3005',
  'http://localhost:3006',
  'http://localhost:3007',
  'http://localhost:3015',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:3001',
  'http://127.0.0.1:3002',
  'http://127.0.0.1:3005',
  'http://127.0.0.1:3006',
  'http://127.0.0.1:3007',
  'http://127.0.0.1:3015',
]

const allowedOrigins = Array.from(
  new Set([
    ...defaultAllowedOrigins,
    ...parseOriginList(process.env.FRONTEND_URL),
    ...parseOriginList(process.env.VERCEL_FRONTEND_URL),
    ...parseOriginList(process.env.CORS_ORIGIN || process.env.GRIEVANCE_ALLOWED_ORIGINS),
  ])
)

app.use(cors({
  origin: allowedOrigins.length ? allowedOrigins : true,
  credentials: true,
  methods: ['GET', 'POST', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
}))
app.use(express.json({ limit: '1mb' }))

// --- DEBUG ROUTE: Place at the top for instant liveness check ---
app.get('/test-me', (req, res) => {
  res.json({ message: "If you see this, the server is alive and routing works!" })
})

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.PGSSLMODE || process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
})

const toJson = (value) => {
  if (value instanceof Date) return value.toISOString()
  if (value && typeof value === 'object' && typeof value.toJSON === 'function') return value.toJSON()
  return value
}

const serializeRow = (row) => {
  const output = {}
  for (const [key, value] of Object.entries(row)) {
    output[key] = toJson(value)
  }
  return output
}

const ALLOWED_PLATFORMS = new Set(['Careem', 'InDrive', 'Bykea', 'Foodpanda', 'Cheetay', 'Other'])
const ALLOWED_CATEGORIES = new Set(['commission_change', 'deactivation', 'payment_delay', 'other'])
const ALLOWED_FILTER_STATUS = new Set(['open', 'escalated', 'resolved'])

const normalizeText = (value) => String(value || '').replace(/\s+/g, ' ').trim()

const validateUuid = (value) => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(String(value || '').trim())

const validateGrievancePayload = (payload) => {
  const platform = normalizeText(payload?.platform)
  const category = normalizeText(payload?.category).toLowerCase()
  const title = normalizeText(payload?.title)
  const description = normalizeText(payload?.description)
  const tags = Array.isArray(payload?.tags)
    ? Array.from(
        new Set(
          payload.tags
            .map((t) => normalizeText(t).toLowerCase())
            .filter(Boolean)
        )
      )
    : []

  if (!ALLOWED_PLATFORMS.has(platform)) {
    return { ok: false, detail: 'Invalid platform' }
  }
  if (!ALLOWED_CATEGORIES.has(category)) {
    return { ok: false, detail: 'Invalid category' }
  }
  if (title.length < 5 || title.length > 120) {
    return { ok: false, detail: 'Title must be between 5 and 120 characters' }
  }
  if (description.length < 15 || description.length > 2000) {
    return { ok: false, detail: 'Description must be between 15 and 2000 characters' }
  }
  if (tags.length > 10 || tags.some((tag) => tag.length > 24)) {
    return { ok: false, detail: 'Tags must be <= 10 items and each <= 24 characters' }
  }

  return {
    ok: true,
    value: {
      platform,
      category,
      title,
      description,
      tags,
    },
  }
}

const getSupabaseUser = async (req) => {
  const authHeader = req.header('authorization') || req.header('Authorization') || ''
  const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : ''

  if (!token) {
    const error = new Error('Missing bearer token')
    error.status = 401
    throw error
  }

  const supabaseUrl = (process.env.SUPABASE_URL || '').trim().replace(/\/$/, '')
  const supabaseServiceKey = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim()

  if (!supabaseUrl || !supabaseServiceKey) {
    const error = new Error('Supabase not configured')
    error.status = 503
    throw error
  }

  const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
    headers: {
      Authorization: `Bearer ${token}`,
      apikey: supabaseServiceKey,
    },
  })

  if (!response.ok) {
    const error = new Error('Invalid or expired token')
    error.status = 401
    throw error
  }

  return response.json()
}

const requireAuth = async (req, res, next) => {
  try {
    req.user = await getSupabaseUser(req)
    next()
  } catch (error) {
    res.status(error.status || 401).json({ detail: error.message })
  }
}

const requireRole = (role) => async (req, res, next) => {
  try {
    const user = await getSupabaseUser(req)
    const userRole = user?.user_metadata?.role || user?.app_metadata?.role
    if (userRole !== role) {
      return res.status(403).json({ detail: `Requires role: ${role}` })
    }
    req.user = user
    next()
  } catch (error) {
    res.status(error.status || 401).json({ detail: error.message })
  }
}

// --- ROOT health check ---
app.get('/', (_req, res) => {
  res.json({ status: 'ok', service: 'fairgig-grievance-node', version: 'demo-v2' })
})

// --- HEALTH ROUTES ---
app.get(HEALTH_ROUTES, (_req, res) => {
  res.json({ status: 'ok', service: 'fairgig-grievance-node', version: 'demo-v2' })
})

// --- POST /grievances (auth optional for demo) ---
app.post(GRIEVANCES_COLLECTION_ROUTES, async (req, res) => {
  const validation = validateGrievancePayload(req.body)
  if (!validation.ok) {
    return res.status(400).json({ detail: validation.detail })
  }

  const { platform, category, title, description, tags } = validation.value

  // Try to get user from token; fall back to a demo UUID if unauthenticated
  let workerId = '00000000-0000-0000-0000-000000000000'
  try {
    const user = await getSupabaseUser(req)
    if (user?.id) workerId = user.id
  } catch (_) {
    // unauthenticated — use demo worker id
  }

  try {
    const result = await pool.query(
      `
      INSERT INTO grievances (
        worker_id,
        platform,
        category,
        title,
        description,
        tags
      )
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING
        id,
        worker_id,
        platform,
        category,
        title,
        description,
        tags,
        status,
        upvotes,
        created_at,
        updated_at
      `,
      [workerId, platform, category, title, description, tags]
    )

    const row = result.rows[0]
    return res.status(201).json({
      id: String(row.id),
      worker_id: String(row.worker_id),
      platform: row.platform,
      category: row.category,
      title: row.title,
      description: row.description,
      tags: row.tags || [],
      status: row.status,
      upvotes: row.upvotes,
      created_at: toJson(row.created_at),
      updated_at: toJson(row.updated_at),
    })
  } catch (error) {
    if (String(error?.message || '').includes('foreign key')) {
      return res.status(400).json({ detail: 'Worker profile missing.' })
    }
    return res.status(503).json({ detail: 'Database is unavailable.' })
  }
})

app.get(GRIEVANCES_COLLECTION_ROUTES, async (req, res) => {
  const { platform = null, category = null, status = null } = req.query || {}

  const normalizedPlatform = platform ? normalizeText(platform) : null
  const normalizedCategory = category ? normalizeText(category).toLowerCase() : null
  const normalizedStatus = status ? normalizeText(status).toLowerCase() : null

  if (normalizedPlatform && !ALLOWED_PLATFORMS.has(normalizedPlatform)) {
    return res.status(400).json({ detail: 'Invalid platform filter' })
  }
  if (normalizedCategory && !ALLOWED_CATEGORIES.has(normalizedCategory)) {
    return res.status(400).json({ detail: 'Invalid category filter' })
  }
  if (normalizedStatus && !ALLOWED_FILTER_STATUS.has(normalizedStatus)) {
    return res.status(400).json({ detail: 'Invalid status filter' })
  }
  const clauses = ['1=1']
  const params = []

  if (normalizedPlatform) {
    params.push(normalizedPlatform)
    clauses.push(`g.platform = $${params.length}`)
  }
  if (normalizedCategory) {
    params.push(normalizedCategory)
    clauses.push(`g.category = $${params.length}`)
  }
  if (normalizedStatus) {
    params.push(normalizedStatus)
    clauses.push(`g.status = $${params.length}`)
  }

  try {
    const result = await pool.query(
      `
      SELECT
        g.id,
        g.worker_id,
        g.platform,
        g.category,
        g.title,
        g.description,
        g.tags,
        g.status,
        g.upvotes,
        g.created_at,
        g.updated_at,
        p.full_name,
        p.city_zone
      FROM grievances g
      LEFT JOIN profiles p ON p.id = g.worker_id
      WHERE ${clauses.join(' AND ')}
      ORDER BY g.created_at DESC
      LIMIT 200
      `,
      params
    )

    const items = result.rows.map((row) => serializeRow(row))
    return res.json({
      items,
      count: items.length,
      filters: {
        platform: normalizedPlatform,
        category: normalizedCategory,
        status: normalizedStatus,
      },
    })
  } catch (error) {
    return res.status(503).json({ detail: 'Database is unavailable.' })
  }
})

app.post(GRIEVANCES_UPVOTE_ROUTES, requireAuth, async (req, res) => {
  const { grievance_id: grievanceId } = req.params
  if (!validateUuid(grievanceId)) {
    return res.status(400).json({ detail: 'Invalid grievance_id format' })
  }

  try {
    const result = await pool.query(
      `
      UPDATE grievances
      SET upvotes = upvotes + 1, updated_at = NOW()
      WHERE id = $1
      RETURNING id, upvotes, updated_at
      `,
      [grievanceId]
    )

    const row = result.rows[0]
    if (!row) {
      return res.status(404).json({ detail: 'Grievance not found' })
    }

    return res.json({
      ok: true,
      grievance_id: String(row.id),
      upvotes: row.upvotes,
      user_id: req.user.id,
      updated_at: toJson(row.updated_at),
    })
  } catch (error) {
    return res.status(503).json({ detail: 'Database is unavailable.' })
  }
})

app.patch(GRIEVANCES_ESCALATE_ROUTES, requireRole('advocate'), async (req, res) => {
  const { grievance_id: grievanceId } = req.params
  if (!validateUuid(grievanceId)) {
    return res.status(400).json({ detail: 'Invalid grievance_id format' })
  }

  try {
    const result = await pool.query(
      `
      UPDATE grievances
      SET status = 'escalated', updated_at = NOW()
      WHERE id = $1
      RETURNING id, status, updated_at
      `,
      [grievanceId]
    )

    const row = result.rows[0]
    if (!row) {
      return res.status(404).json({ detail: 'Grievance not found' })
    }

    return res.json({
      status: row.status,
      grievance_id: String(row.id),
      escalated_by: req.user.id,
      updated_at: toJson(row.updated_at),
    })
  } catch (error) {
    return res.status(503).json({ detail: 'Database is unavailable.' })
  }
})


app.use((error, _req, res, _next) => {
  res.status(500).json({ detail: error?.message || 'Internal server error' })
})

// --- CATCH-ALL 404 LOGGER: Place at the very bottom ---
app.use((req, res) => {
  console.log(`404 occurred for: ${req.method} ${req.url}`)
  res.status(404).send(`Route ${req.url} not found on this server.`)
})

app.listen(port, '0.0.0.0', () => {
  console.log(`FairGig grievance service running on http://0.0.0.0:${port}`)
})