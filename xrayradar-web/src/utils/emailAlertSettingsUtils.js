export function normalizeEmailList(items) {
  const seen = new Set()
  const out = []
  for (const item of Array.isArray(items) ? items : []) {
    const value = String(item || '').trim().toLowerCase()
    if (!value || seen.has(value)) continue
    seen.add(value)
    out.push(value)
  }
  return out
}

export function normalizeEnvSettings(items) {
  const out = []
  for (const item of Array.isArray(items) ? items : []) {
    const environment = String(item?.environment || '').trim()
    if (!environment) continue
    out.push({
      environment,
      enabled: item?.enabled ?? true,
      cooldown_minutes: item?.cooldown_minutes == null ? null : Number(item.cooldown_minutes),
      additional_emails: normalizeEmailList(item?.additional_emails),
    })
  }
  return out.sort((a, b) => a.environment.localeCompare(b.environment))
}

export function parseCooldownValue(raw) {
  const value = String(raw ?? '').trim()
  if (!value) return null
  const num = parseInt(value, 10)
  return Number.isNaN(num) ? null : num
}

export function isTeamsPlan(plan) {
  return plan === 'Teams' || plan === 'Teams Pro'
}
