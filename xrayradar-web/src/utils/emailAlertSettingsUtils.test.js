import { describe, it, expect } from 'vitest'
import {
  normalizeEmailList,
  normalizeEnvSettings,
  parseCooldownValue,
  isTeamsPlan,
} from './emailAlertSettingsUtils'

describe('emailAlertSettingsUtils', () => {
  describe('normalizeEmailList', () => {
    it('returns empty array for non-array input', () => {
      expect(normalizeEmailList(null)).toEqual([])
      expect(normalizeEmailList(undefined)).toEqual([])
      expect(normalizeEmailList('a@b.com')).toEqual([])
    })

    it('skips empty and duplicate values', () => {
      expect(normalizeEmailList(['a@b.com', '', '  ', 'a@b.com', 'A@B.COM', 'b@c.com'])).toEqual([
        'a@b.com',
        'b@c.com',
      ])
    })

    it('trims and lowercases and deduplicates', () => {
      expect(normalizeEmailList(['  A@B.COM  ', 'a@b.com'])).toEqual(['a@b.com'])
    })
  })

  describe('normalizeEnvSettings', () => {
    it('skips items with empty environment', () => {
      expect(normalizeEnvSettings([{ environment: '' }, { environment: '  ' }, { environment: 'prod' }])).toEqual([
        { environment: 'prod', enabled: true, cooldown_minutes: null, additional_emails: [] },
      ])
    })

    it('normalizes enabled, cooldown_minutes, and additional_emails', () => {
      expect(
        normalizeEnvSettings([
          {
            environment: 'staging',
            enabled: false,
            cooldown_minutes: 5,
            additional_emails: ['x@y.com', 'x@y.com'],
          },
        ])
      ).toEqual([
        {
          environment: 'staging',
          enabled: false,
          cooldown_minutes: 5,
          additional_emails: ['x@y.com'],
        },
      ])
    })

    it('uses defaults when fields missing (enabled true, cooldown null)', () => {
      expect(normalizeEnvSettings([{ environment: 'prod' }])).toEqual([
        { environment: 'prod', enabled: true, cooldown_minutes: null, additional_emails: [] },
      ])
    })

    it('sorts by environment name', () => {
      expect(normalizeEnvSettings([{ environment: 'z' }, { environment: 'a' }])).toEqual([
        { environment: 'a', enabled: true, cooldown_minutes: null, additional_emails: [] },
        { environment: 'z', enabled: true, cooldown_minutes: null, additional_emails: [] },
      ])
    })
  })

  describe('parseCooldownValue', () => {
    it('returns null for empty or whitespace', () => {
      expect(parseCooldownValue('')).toBeNull()
      expect(parseCooldownValue('   ')).toBeNull()
      expect(parseCooldownValue(null)).toBeNull()
      expect(parseCooldownValue(undefined)).toBeNull()
    })

    it('parses valid integer string', () => {
      expect(parseCooldownValue('10')).toBe(10)
      expect(parseCooldownValue('  5  ')).toBe(5)
    })

    it('returns null for NaN', () => {
      expect(parseCooldownValue('abc')).toBeNull()
      expect(parseCooldownValue('10.5')).toBe(10)
    })
  })

  describe('isTeamsPlan', () => {
    it('returns true for Teams and Teams Pro', () => {
      expect(isTeamsPlan('Teams')).toBe(true)
      expect(isTeamsPlan('Teams Pro')).toBe(true)
    })

    it('returns false for other plans and invalid input', () => {
      expect(isTeamsPlan('Free')).toBe(false)
      expect(isTeamsPlan('Basic')).toBe(false)
      expect(isTeamsPlan(null)).toBe(false)
      expect(isTeamsPlan(undefined)).toBe(false)
      expect(isTeamsPlan('')).toBe(false)
    })
  })
})
