const path = require('node:path')
const express = require('express')
const cors = require('cors')
const { Pool } = require('pg')
require('dotenv').config()
require('dotenv').config({ path: path.join(__dirname, '..', 'fairgig-backend', '.env') })

const app = express()
const port = Number(process.env.PORT || 3002)

const allowedOrigin = process.env.CORS_ORIGIN || '*'

app.use(cors({
  origin: allowedOrigin === '*' ? true : allowedOrigin.split(',').map((item) => item.trim()).filter(Boolean),
  methods: ['GET', 'POST', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
}))
app.use(express.json({ limit: '1mb' }))

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

const getSupabaseUser = async (req) => {
  const authHeader = req.header('authorization') || req.header('Authorization') || ''
  const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : ''

  if (!token) {
    const error = new Error('Missing bearer token')
    error.status = 401
    throw error
  }

  const supabaseUrl = (process.env.SUPABASE_URL || '').trim().replace(/\/$/, '')
  const serviceKey = (
    process.env.SUPABASE_SERVICE_KEY ||
    process.env.SUPABASE_KEY ||
    process.env.SUPABASE_ANON_KEY ||
    ''
  ).trim()

  if (!supabaseUrl || !serviceKey) {
    const error = new Error('Supabase credentials are not configured')
    error.status = 503
    throw error
  }

  const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
    headers: {
      Authorization: `Bearer ${token}`,
      apikey: serviceKey,
    },
  })

  if (!response.ok) {
    const error = new Error('Token invalid or expired')
    error.status = 401
    throw error
  }

  const payload = await response.json()
  const role = payload?.user_metadata?.role || payload?.app_metadata?.role || 'worker'
  return { id: payload?.id, role }
}

const requireRole = (...roles) => async (req, res, next) => {
  try {
    const user = await getSupabaseUser(req)
    if (!roles.includes(user.role)) {
      return res.status(403).json({ detail: 'Insufficient role' })
    }
    req.user = user
    return next()
  } catch (error) {
    return res.status(error.status || 500).json({ detail: error.message || 'Unauthorized' })
  }
}

const requireAuth = async (req, res, next) => {
  try {
    req.user = await getSupabaseUser(req)
    return next()
  } catch (error) {
    return res.status(error.status || 500).json({ detail: error.message || 'Unauthorized' })
  }
}

app.get('/health', async (_req, res) => {
  res.json({ status: 'ok', service: 'fairgig-grievance-node' })
})

app.post('/grievances', requireRole('worker'), async (req, res) => {
  const { platform, category, title, description, tags = [] } = req.body || {}

  if (!platform || !category || !title || !description) {
    return res.status(400).json({ detail: 'Missing required grievance fields' })
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
      [req.user.id, platform, category, title, description, Array.isArray(tags) ? tags : []]
    )

    const row = result.rows[0]
    return res.json({
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
      return res.status(400).json({ detail: 'Worker profile missing. Complete /auth/setup-profile first.' })
    }
    return res.status(503).json({ detail: 'Database is unavailable.' })
  }
})

app.get('/grievances', async (req, res) => {
  const { platform = null, category = null, status = null } = req.query || {}
  const clauses = ['1=1']
  const params = []

  if (platform) {
    params.push(platform)
    clauses.push(`g.platform = $${params.length}`)
  }
  if (category) {
    params.push(category)
    clauses.push(`g.category = $${params.length}`)
  }
  if (status) {
    params.push(status)
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
        platform,
        category,
        status,
      },
    })
  } catch (error) {
    return res.status(503).json({ detail: 'Database is unavailable.' })
  }
})

app.post('/grievances/:grievance_id/upvote', requireAuth, async (req, res) => {
  const { grievance_id: grievanceId } = req.params

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

app.patch('/grievances/:grievance_id/escalate', requireRole('advocate'), async (req, res) => {
  const { grievance_id: grievanceId } = req.params

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

app.listen(port, '0.0.0.0', () => {
  console.log(`FairGig grievance service running on http://0.0.0.0:${port}`)
})