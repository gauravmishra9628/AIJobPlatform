import React from "react";
import { motion } from "framer-motion";
import { Search, FileText, Users, Briefcase, AlertCircle, Loader2 } from "lucide-react";

export function LoadingState({ message = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-3" />
      <p className="text-gray-500 text-sm">{message}</p>
    </div>
  );
}

export function EmptyState({
  icon: Icon = Search,
  title = "No results found",
  description = "Try adjusting your search or filters",
  action = null
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 px-4"
    >
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 text-center max-w-sm mb-4">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message = "Please try again later",
  onRetry = null
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-12 px-4"
    >
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 text-center max-w-sm mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
        >
          Try Again
        </button>
      )}
    </motion.div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 animate-pulse">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-gray-200 rounded-lg" />
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
          <div className="h-3 bg-gray-100 rounded w-1/2" />
        </div>
      </div>
      <div className="mt-4 h-3 bg-gray-100 rounded w-full" />
      <div className="mt-2 h-3 bg-gray-100 rounded w-2/3" />
    </div>
  );
}

export function StatsCard({ icon: Icon, label, value, color = "blue" }) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    orange: "bg-orange-50 text-orange-600",
  };

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-4"
    >
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </motion.div>
  );
}

export function Chip({ label, onClick, active = false, removable = false, onRemove = null }) {
  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium cursor-pointer transition ${
        active
          ? "bg-blue-600 text-white"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
    >
      {label}
      {removable && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-2 hover:text-red-300"
        >
          ×
        </button>
      )}
    </span>
  );
}

export function Toast({ message, type = "info", onClose }) {
  const types = {
    info: "bg-blue-500",
    success: "bg-green-500",
    error: "bg-red-500",
    warning: "bg-yellow-500",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className={`fixed bottom-4 right-4 ${types[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 z-50`}
    >
      <span>{message}</span>
      <button onClick={onClose} className="hover:opacity-80">×</button>
    </motion.div>
  );
}

export function ResponsiveGrid({ children, className = "" }) {
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 ${className}`}>
      {children}
    </div>
  );
}

export function TabGroup({ tabs, activeTab, onChange }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition ${
            activeTab === tab.id
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {tab.icon && <tab.icon className="w-4 h-4 inline mr-2" />}
          {tab.label}
        </button>
      ))}
    </div>
  );
}