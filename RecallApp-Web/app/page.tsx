'use client'

import { useState } from 'react'
import { Search, Clock, Activity, Database, Menu, X, Calendar, Filter } from 'lucide-react'
import { SearchSection } from '@/components/SearchSection'
import { TimelineView } from '@/components/TimelineView'
import { StatsPanel } from '@/components/StatsPanel'
import { RecentActivities } from '@/components/RecentActivities'

export default function Home() {
  const [activeTab, setActiveTab] = useState('search')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🧠</span>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Recall
              </h1>
              <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                Memory Search
              </span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              <button
                onClick={() => setActiveTab('search')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === 'search'
                    ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Search className="w-4 h-4 mr-2" />
                Search
              </button>
              <button
                onClick={() => setActiveTab('timeline')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === 'timeline'
                    ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Clock className="w-4 h-4 mr-2" />
                Timeline
              </button>
              <button
                onClick={() => setActiveTab('recent')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === 'recent'
                    ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Activity className="w-4 h-4 mr-2" />
                Recent
              </button>
              <button
                onClick={() => setActiveTab('stats')}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === 'stats'
                    ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Database className="w-4 h-4 mr-2" />
                Stats
              </button>
            </nav>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-700 dark:text-gray-300"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden px-4 pb-4 space-y-2">
            <button
              onClick={() => {
                setActiveTab('search')
                setMobileMenuOpen(false)
              }}
              className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md ${
                activeTab === 'search'
                  ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                  : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Search className="w-4 h-4 mr-2" />
              Search
            </button>
            <button
              onClick={() => {
                setActiveTab('timeline')
                setMobileMenuOpen(false)
              }}
              className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md ${
                activeTab === 'timeline'
                  ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                  : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Clock className="w-4 h-4 mr-2" />
              Timeline
            </button>
            <button
              onClick={() => {
                setActiveTab('recent')
                setMobileMenuOpen(false)
              }}
              className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md ${
                activeTab === 'recent'
                  ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                  : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Activity className="w-4 h-4 mr-2" />
              Recent Activities
            </button>
            <button
              onClick={() => {
                setActiveTab('stats')
                setMobileMenuOpen(false)
              }}
              className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md ${
                activeTab === 'stats'
                  ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                  : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              <Database className="w-4 h-4 mr-2" />
              Statistics
            </button>
          </nav>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'search' && <SearchSection />}
        {activeTab === 'timeline' && <TimelineView />}
        {activeTab === 'recent' && <RecentActivities />}
        {activeTab === 'stats' && <StatsPanel />}
      </main>

      {/* Footer */}
      <footer className="mt-auto py-4 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>Recall Memory System • Web Version</p>
        <p className="mt-1">
          {new Date().toLocaleString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </p>
      </footer>
    </div>
  )
}