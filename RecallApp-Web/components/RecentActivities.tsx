'use client'

import { useState } from 'react'
import { Activity, Clock, Monitor, Bot, RefreshCw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface RecentEvent {
  id: string
  timestamp: string
  source: string
  title: string
  text: string
  tags: string[]
}

export function RecentActivities() {
  const [hours, setHours] = useState(4)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['recent', hours],
    queryFn: async () => {
      const response = await axios.get(`/api/events/recent?hours=${hours}`)
      return response.data
    },
    refetchInterval: 60000 // Refresh every minute
  })

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
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Recent Activities
          </h2>
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2">
          {[1, 4, 12, 24].map((h) => (
            <button
              key={h}
              onClick={() => setHours(h)}
              className={`px-4 py-2 text-sm rounded-lg ${
                hours === h
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {h} hour{h > 1 ? 's' : ''}
            </button>
          ))}
        </div>
      </div>

      {/* Activities List */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading activities...</p>
        </div>
      )}

      {data && data.events && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="space-y-4">
            {data.events.length > 0 ? (
              data.events.map((event: RecentEvent) => (
                <div
                  key={event.id}
                  className="flex items-start gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    <div className="p-2 bg-gray-100 dark:bg-gray-600 rounded-lg">
                      {getSourceIcon(event.source)}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatTimestamp(event.timestamp)}
                      </span>
                      <span className="text-xs text-gray-400 dark:text-gray-500">•</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {event.source}
                      </span>
                    </div>
                    <h3 className="font-medium text-gray-900 dark:text-white text-sm">
                      {event.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                      {event.text}
                    </p>
                    {event.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {event.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">
                  No activities in the last {hours} hour{hours > 1 ? 's' : ''}
                </p>
              </div>
            )}
          </div>

          {data.events.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                Showing {data.events.length} activities from the last {hours} hour{hours > 1 ? 's' : ''}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}