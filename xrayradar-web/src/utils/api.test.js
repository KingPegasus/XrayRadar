import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readErrorMessage, fetchMe, fetchJson } from './api'

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  describe('readErrorMessage', () => {
    it('extracts detail from response', async () => {
      const resp = {
        status: 400,
        json: async () => ({ detail: 'Custom error message' }),
      }
      const result = await readErrorMessage(resp)
      expect(result).toBe('Custom error message')
    })

    it('returns default message when detail is missing', async () => {
      const resp = {
        status: 404,
        json: async () => ({}),
      }
      const result = await readErrorMessage(resp)
      expect(result).toBe('Request failed (404)')
    })

    it('handles invalid JSON', async () => {
      const resp = {
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      }
      const result = await readErrorMessage(resp)
      expect(result).toBe('Request failed (500)')
    })

    it('handles empty detail string', async () => {
      const resp = {
        status: 400,
        json: async () => ({ detail: '   ' }),
      }
      const result = await readErrorMessage(resp)
      expect(result).toBe('Request failed (400)')
    })
  })

  describe('fetchMe', () => {
    it('returns user data on success', async () => {
      const userData = { id: 1, email: 'test@example.com' }
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => userData,
      })

      const result = await fetchMe()
      expect(result).toEqual(userData)
      expect(fetch).toHaveBeenCalledWith('/api/me', { credentials: 'include' })
    })

    it('returns null on error response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      })

      const result = await fetchMe()
      expect(result).toBeNull()
    })

    it('returns null on network error', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await fetchMe()
      expect(result).toBeNull()
    })
  })

  describe('fetchJson', () => {
    it('returns JSON data on success', async () => {
      const data = { key: 'value' }
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => data,
      })

      const result = await fetchJson('/api/test')
      expect(result).toEqual(data)
      expect(fetch).toHaveBeenCalledWith('/api/test', { credentials: 'include' })
    })

    it('passes options to fetch', async () => {
      const data = { key: 'value' }
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => data,
      })

      const opts = { method: 'POST', headers: { 'Content-Type': 'application/json' } }
      await fetchJson('/api/test', opts)
      expect(fetch).toHaveBeenCalledWith('/api/test', { credentials: 'include', ...opts })
    })

    it('throws error on non-ok response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      })

      await expect(fetchJson('/api/test')).rejects.toThrow('Not found')
    })
  })
})
