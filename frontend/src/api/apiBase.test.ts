import { describe, it, expect } from 'vitest'
import { getApiBase } from './apiBase'

describe('getApiBase', () => {
  it('returns /api when env value is empty or unset', () => {
    expect(getApiBase(undefined)).toBe('/api')
    expect(getApiBase('')).toBe('/api')
    expect(getApiBase('   ')).toBe('/api')
  })

  it('appends /api when value is origin without /api', () => {
    expect(getApiBase('http://localhost:8000')).toBe('http://localhost:8000/api')
    expect(getApiBase('http://localhost:8000/')).toBe('http://localhost:8000/api')
  })

  it('does not append /api when value already ends with /api', () => {
    expect(getApiBase('http://localhost:8000/api')).toBe('http://localhost:8000/api')
    expect(getApiBase('http://localhost:8000/api/')).toBe('http://localhost:8000/api')
  })

  it('normalizes trailing slashes before checking', () => {
    expect(getApiBase('http://localhost:8000/api///')).toBe('http://localhost:8000/api')
  })

  it('treats /api suffix case-insensitively', () => {
    expect(getApiBase('http://localhost:8000/API')).toBe('http://localhost:8000/API')
  })
})
