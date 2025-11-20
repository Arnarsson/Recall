'use client'

import { Database, HardDrive, Clock, Archive, TrendingUp, Monitor, Bot } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export function StatsPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await axios.get('/api/stats')
      return response.data
    },
    refetchInterval: 60000 // Refresh every minute
  })

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <Database className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {data?.total_events || 0}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Events</h3>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Across all sources</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <Clock className="w-8 h-8 text-green-600 dark:text-green-400" />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {data?.recent_events_24h || 0}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Recent (24h)</h3>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Last 24 hours</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <HardDrive className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {data?.archive_status?.size_mb?.toFixed(1) || 0} MB
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Database Size</h3>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Current storage</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <Archive className="w-8 h-8 text-orange-600 dark:text-orange-400" />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {data?.archive_status?.age_days || 0}d
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Archive Age</h3>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Days since last archive</p>
        </div>
      </div>

      {/* Sources Breakdown */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Event Sources
        </h2>
        
        <div className="space-y-3">
          {data?.sources && Object.entries(data.sources).map(([source, count]) => (
            <div key={source}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  {source === 'windrecorder' ? (
                    <Monitor className="w-4 h-4 text-gray-500" />
                  ) : (
                    <Bot className="w-4 h-4 text-gray-500" />
                  )}
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {source.charAt(0).toUpperCase() + source.slice(1)}
                  </span>
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {count as number} events
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    source === 'windrecorder' 
                      ? 'bg-blue-600 dark:bg-blue-400' 
                      : 'bg-green-600 dark:bg-green-400'
                  }`}
                  style={{
                    width: `${((count as number) / (data.total_events || 1)) * 100}%`
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          System Status
        </h2>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-400">Database Status</span>
            <span className="text-sm font-medium text-green-600 dark:text-green-400">
              {data?.database_status || 'Unknown'}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-400">Last Updated</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {data?.last_updated ? formatDate(data.last_updated) : 'N/A'}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-400">Next Archive</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {data?.archive_status?.next_archive ? formatDate(data.archive_status.next_archive) : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading statistics...</p>
        </div>
      )}
    </div>
  )
}