'use client'

import { useState } from 'react'
import { Search, Filter, X, Monitor, Bot, Clock } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface SearchResult {
  id: string
  timestamp: string
  source: string
  title: string
  text: string
  tags: string[]
  relevance: number
}

export function SearchSection() {
  const [query, setQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['search', query, sourceFilter],
    queryFn: async () => {
      if (!query) return null
      const params = new URLSearchParams({ q: query })
      if (sourceFilter) params.append('source', sourceFilter)
      
      const response = await axios.get(`/api/search?${params}`)
      return response.data
    },
    enabled: false
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      refetch()
    }
  }

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'windrecorder':
        return <Monitor className="w-4 h-4" />
      case 'claude':
        return <Bot className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search your memory timeline..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Search
            </button>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="p-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <Filter className="w-5 h-5" />
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Source:</span>
              <button
                type="button"
                onClick={() => setSourceFilter(null)}
                className={`px-3 py-1 text-sm rounded-full ${
                  sourceFilter === null 
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setSourceFilter('windrecorder')}
                className={`px-3 py-1 text-sm rounded-full ${
                  sourceFilter === 'windrecorder'
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                WindRecorder
              </button>
              <button
                type="button"
                onClick={() => setSourceFilter('claude')}
                className={`px-3 py-1 text-sm rounded-full ${
                  sourceFilter === 'claude'
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                Claude
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Searching...</p>
        </div>
      )}

      {data && data.results && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {data.results.length} Results
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              for "{query}"
            </span>
          </div>

          <div className="space-y-3">
            {data.results.map((result: SearchResult) => (
              <div
                key={result.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                        {getSourceIcon(result.source)}
                        {result.source}
                      </span>
                      <span className="text-sm text-gray-400 dark:text-gray-500">•</span>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {formatTimestamp(result.timestamp)}
                      </span>
                      <span className="ml-auto text-sm text-green-600 dark:text-green-400">
                        {(result.relevance * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <h3 className="font-medium text-gray-900 dark:text-white mb-1">
                      {result.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                      {result.text}
                    </p>
                    {result.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {result.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data && data.results && data.results.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-600 dark:text-gray-400">No results found for "{query}"</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Try different keywords or remove filters
          </p>
        </div>
      )}
    </div>
  )
}