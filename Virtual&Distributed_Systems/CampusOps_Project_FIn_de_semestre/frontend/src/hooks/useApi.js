import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'

export function useApi(url, options = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data: result } = await api.get(url, options)
      setData(result)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => { fetch() }, [fetch])

  return { data, loading, error, refetch: fetch }
}
