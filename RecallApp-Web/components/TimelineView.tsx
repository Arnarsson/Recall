'use client'

import { useState } from 'react'
import { Calendar, Clock, Monitor, Bot, ChevronDown, ChevronRight } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface TimelineEvent {
  id: string
  timestamp: string
  source: string
  title: string
  text: string
  tags: string[]
}

export function TimelineView() {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [expandedHours, setExpandedHours] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['timeline', selectedDate],
    queryFn: async () => {
      const response = await axios.get(`/api/timeline?date=${selectedDate}`)
      return response.data
    }
  })

  const toggleHour = (hour: string) => {
    const newExpanded = new Set(expandedHours)
    if (newExpanded.has(hour)) {
      newExpanded.delete(hour)
    } else {
      newExpanded.add(hour)
    }
    setExpandedHours(newExpanded)
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

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Date Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Timeline View
          </h2>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Quick Date Selection */}
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedDate(new Date().toISOString().split('T')[0])}
            className="px-4 py-2 text-sm bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800"
          >
            Today
          </button>
          <button
            onClick={() => {
              const yesterday = new Date()
              yesterday.setDate(yesterday.getDate() - 1)
              setSelectedDate(yesterday.toISOString().split('T')[0])
            }}
            className="px-4 py-2 text-sm bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            Yesterday
          </button>
          <button
            onClick={() => {
              const weekAgo = new Date()
              weekAgo.setDate(weekAgo.getDate() - 7)
              setSelectedDate(weekAgo.toISOString().split('T')[0])
            }}
            className="px-4 py-2 text-sm bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            Week Ago
          </button>
        </div>
      </div>

      {/* Timeline */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading timeline...</p>
        </div>
      )}

      {data && data.timeline && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="space-y-4">
            {Object.entries(data.timeline)
              .sort(([a], [b]) => b.localeCompare(a))
              .map(([hour, events]) => (
                <div key={hour} className="border-l-2 border-gray-200 dark:border-gray-700 pl-4">
                  <button
                    onClick={() => toggleHour(hour)}
                    className="flex items-center gap-2 w-full text-left hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded-lg"
                  >
                    {expandedHours.has(hour) ? (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    )}
                    <span className="font-medium text-gray-900 dark:text-white">
                      {hour.split(' ')[1]}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      ({(events as TimelineEvent[]).length} events)
                    </span>
                  </button>

                  {expandedHours.has(hour) && (
                    <div className="ml-6 mt-2 space-y-2">
                      {(events as TimelineEvent[]).map((event) => (
                        <div
                          key={event.id}
                          className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  {formatTime(event.timestamp)}
                                </span>
                                <span className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                                  {getSourceIcon(event.source)}
                                  {event.source}
                                </span>
                              </div>
                              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                                {event.title}
                              </h4>
                              <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                                {event.text}
                              </p>
                              {event.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {event.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-full"
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
                  )}
                </div>
              ))}
          </div>

          {Object.keys(data.timeline).length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-600 dark:text-gray-400">No events found for {selectedDate}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}