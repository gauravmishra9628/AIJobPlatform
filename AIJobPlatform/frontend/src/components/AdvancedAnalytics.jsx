import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, Users, Briefcase, DollarSign, Activity, Target } from 'lucide-react';

const monthlyData = [
  { month: 'Jan', jobs: 45, applications: 320, hires: 28 },
  { month: 'Feb', jobs: 52, applications: 380, hires: 35 },
  { month: 'Mar', jobs: 48, applications: 410, hires: 32 },
  { month: 'Apr', jobs: 61, applications: 450, hires: 40 },
  { month: 'May', jobs: 55, applications: 390, hires: 38 },
  { month: 'Jun', jobs: 68, applications: 520, hires: 45 },
];

const skillDemandData = [
  { name: 'React', demand: 85 },
  { name: 'Python', demand: 78 },
  { name: 'Node.js', demand: 72 },
  { name: 'AWS', demand: 68 },
  { name: 'Machine Learning', demand: 65 },
  { name: 'SQL', demand: 60 },
];

const candidateSourceData = [
  { name: 'Direct Apply', value: 45, color: '#3B82F6' },
  { name: 'Referrals', value: 25, color: '#10B981' },
  { name: 'LinkedIn', value: 20, color: '#F59E0B' },
  { name: 'Job Boards', value: 10, color: '#8B5CF6' },
];

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4'];

export function AdvancedAnalytics() {
  const [timeRange, setTimeRange] = useState('6months');

  const stats = [
    { label: 'Total Hires', value: '218', change: '+12%', icon: Users, color: 'blue' },
    { label: 'Active Jobs', value: '156', change: '+8%', icon: Briefcase, color: 'green' },
    { label: 'Avg. Salary', value: '$85K', change: '+5%', icon: DollarSign, color: 'purple' },
    { label: 'Conversion Rate', value: '24%', change: '+3%', icon: Target, color: 'orange' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Advanced Analytics</h2>
          <p className="text-gray-600 dark:text-gray-400">Comprehensive insights into your hiring performance</p>
        </div>
        <div className="flex gap-2">
          {['7days', '30days', '6months', '1year'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {range === '6months' ? '6M' : range === '1year' ? '1Y' : range === '30days' ? '30D' : '7D'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          const colorClasses = {
            blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
            green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400',
            purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400',
            orange: 'bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400',
          };

          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
            >
              <div className="flex items-center justify-between">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[stat.color]}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <span className="text-sm font-medium text-green-600 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-full">
                  {stat.change}
                </span>
              </div>
              <div className="mt-4">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hiring Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Hiring Trends
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Area type="monotone" dataKey="jobs" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.2} name="Jobs Posted" />
              <Area type="monotone" dataKey="applications" stroke="#10B981" fill="#10B981" fillOpacity={0.2} name="Applications" />
              <Area type="monotone" dataKey="hires" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.2} name="Hires" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Skill Demand */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            In-Demand Skills
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={skillDemandData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
              <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
              <YAxis type="category" dataKey="name" stroke="#9CA3AF" fontSize={12} width={100} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="demand" fill="#3B82F6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Candidate Sources */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-600" />
            Candidate Sources
          </h3>
          <div className="flex items-center">
            <ResponsiveContainer width="60%" height={220}>
              <PieChart>
                <Pie
                  data={candidateSourceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {candidateSourceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-3">
              {candidateSourceData.map((source) => (
                <div key={source.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: source.color }} />
                  <span className="text-sm text-gray-600 dark:text-gray-400">{source.name}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white ml-auto">{source.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-orange-600" />
            Performance Metrics
          </h3>
          <div className="space-y-4">
            {[
              { label: 'Resume to Interview', value: 32, color: '#3B82F6' },
              { label: 'Interview to Offer', value: 68, color: '#10B981' },
              { label: 'Offer to Acceptance', value: 85, color: '#8B5CF6' },
              { label: 'Time to Hire', value: 24, color: '#F59E0B' },
            ].map((metric) => (
              <div key={metric.label}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600 dark:text-gray-400">{metric.label}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{metric.value}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{ width: `${metric.value}%`, backgroundColor: metric.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}