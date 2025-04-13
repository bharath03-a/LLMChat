"use client"

import { motion } from "framer-motion"
import { FiUsers, FiFileText, FiClock, FiTrendingUp, FiArrowUp, FiArrowDown } from "react-icons/fi"
import { useState, useEffect } from "react"

// Placeholder data for legal metrics
const initialMetrics = [
  {
    id: 1,
    title: "Active Cases",
    value: 0,
    target: 124,
    icon: <FiFileText className="text-2xl text-orange-500" />,
    change: "+12%",
    positive: true,
  },
  {
    id: 2,
    title: "Client Consultations",
    value: 0,
    target: 87,
    icon: <FiUsers className="text-2xl text-orange-500" />,
    change: "+5%",
    positive: true,
  },
  {
    id: 3,
    title: "Average Response Time",
    value: 0,
    target: 3.2,
    unit: "hours",
    icon: <FiClock className="text-2xl text-orange-500" />,
    change: "-8%",
    positive: true,
  },
  {
    id: 4,
    title: "Case Success Rate",
    value: 0,
    target: 92,
    unit: "%",
    icon: <FiTrendingUp className="text-2xl text-orange-500" />,
    change: "+2%",
    positive: true,
  },
]

// Recent activity data
const recentActivity = [
  {
    id: 1,
    action: "Case file updated",
    case: "Johnson vs. State",
    time: "2 hours ago",
  },
  {
    id: 2,
    action: "New document uploaded",
    case: "Smith Property Dispute",
    time: "4 hours ago",
  },
  {
    id: 3,
    action: "Client consultation scheduled",
    case: "Corporate Merger Review",
    time: "Yesterday",
  },
  {
    id: 4,
    action: "Case status changed",
    case: "Insurance Claim #45892",
    time: "Yesterday",
  },
]

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(initialMetrics)
  const [isLoading, setIsLoading] = useState(true)

  // Simulate loading data from API
  useEffect(() => {
    const timer = setTimeout(() => {
      setMetrics(
        metrics.map((metric) => ({
          ...metric,
          value: metric.target,
        })),
      )
      setIsLoading(false)
    }, 1500)

    window.scrollTo(0, 0)

    return () => clearTimeout(timer)
  }, [])

  // Animate counter effect
  useEffect(() => {
    let interval: NodeJS.Timeout

    // Only start animation if values are still at 0
    if (metrics.some((metric) => metric.value === 0)) {
      interval = setInterval(() => {
        setMetrics((currentMetrics) =>
          currentMetrics.map((metric) => ({
            ...metric,
            value:
              metric.value < metric.target
                ? metric.value + (metric.target / 20 > 1 ? Math.ceil(metric.target / 20) : 0.1)
                : metric.target,
          })),
        )
      }, 50)
    }

    return () => clearInterval(interval)
  }, [metrics])

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
        <motion.h1
          className="text-3xl font-bold"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          Legal Dashboard
        </motion.h1>

        <div className="mt-4 sm:mt-0 flex space-x-3">
          <select className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500">
            <option>Last 7 days</option>
            <option>Last 30 days</option>
            <option>Last 90 days</option>
            <option>This year</option>
          </select>

          <button className="bg-orange-500 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-orange-600 transition">
            Export Data
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.id}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">{metric.icon}</div>
              <span
                className={`text-sm font-medium ${
                  metric.positive ? "text-green-500" : "text-red-500"
                } flex items-center`}
              >
                {metric.positive ? <FiArrowUp className="mr-1" /> : <FiArrowDown className="mr-1" />}
                {metric.change}
              </span>
            </div>
            <h3 className="text-gray-500 dark:text-gray-400 text-sm mb-1">{metric.title}</h3>
            {isLoading ? (
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            ) : (
              <div className="flex items-baseline">
                <span className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                  {metric.unit === "%" ? Math.round(metric.value) : metric.value.toFixed(1)}
                </span>
                {metric.unit && <span className="ml-1 text-gray-500 dark:text-gray-400">{metric.unit}</span>}
              </div>
            )}
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Case Distribution</h2>
            <div className="flex space-x-2">
              <button className="text-sm text-gray-500 dark:text-gray-400 hover:text-orange-500 transition">
                By Type
              </button>
              <button className="text-sm text-gray-500 dark:text-gray-400 hover:text-orange-500 transition">
                By Status
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
          ) : (
            <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-900 rounded-lg">
              <p className="text-gray-400">Chart placeholder - Legal case distribution by type</p>
            </div>
          )}
        </motion.div>

        <motion.div
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Recent Activity</h2>
            <button className="text-sm text-orange-500 hover:underline">View All</button>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="border-b border-gray-100 dark:border-gray-700 pb-3 last:border-0">
                  <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2 animate-pulse"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 animate-pulse"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="border-b border-gray-100 dark:border-gray-700 pb-3 last:border-0">
                  <p className="font-medium text-gray-800 dark:text-gray-200">{activity.action}</p>
                  <div className="flex justify-between mt-1">
                    <span className="text-sm text-gray-500 dark:text-gray-400">{activity.case}</span>
                    <span className="text-xs text-gray-400 dark:text-gray-500">{activity.time}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
