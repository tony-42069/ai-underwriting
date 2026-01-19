import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import {
  FileText,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Upload,
  ArrowRight,
  DollarSign,
  Percent,
  Building,
} from 'lucide-react'
import { format } from 'date-fns'

export default function Dashboard() {
  const [recentDocuments] = useState<any[]>([])

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000,
  })

  const stats = [
    {
      label: 'Total Documents',
      value: recentDocuments.length,
      icon: FileText,
      color: 'text-blue-400',
      bg: 'bg-blue-500/20',
    },
    {
      label: 'Completed',
      value: recentDocuments.filter((d) => d.status === 'completed').length,
      icon: CheckCircle,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/20',
    },
    {
      label: 'Processing',
      value: recentDocuments.filter((d) => d.status === 'processing').length,
      icon: Clock,
      color: 'text-amber-400',
      bg: 'bg-amber-500/20',
    },
    {
      label: 'Risk Flags',
      value: 2,
      icon: AlertTriangle,
      color: 'text-red-400',
      bg: 'bg-red-500/20',
    },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">
            Overview of your underwriting documents
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          <Upload className="w-5 h-5" />
          Upload Document
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="card hover:border-slate-600 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{stat.label}</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {stat.value}
                </p>
              </div>
              <div className={`p-3 rounded-xl ${stat.bg}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">
              Recent Documents
            </h2>
            <Link
              to="/upload"
              className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1"
            >
              View all
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {recentDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No documents uploaded yet</p>
              <Link to="/upload" className="btn btn-primary mt-4 inline-flex">
                <Upload className="w-4 h-4" />
                Upload your first document
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentDocuments.slice(0, 5).map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg hover:bg-slate-900 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-800 rounded-lg">
                      <FileText className="w-5 h-5 text-slate-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-slate-500">
                        {format(new Date(doc.created_at), 'MMM d, yyyy')}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`badge ${
                      doc.status === 'completed'
                        ? 'badge-success'
                        : doc.status === 'processing'
                        ? 'badge-info'
                        : doc.status === 'error'
                        ? 'badge-error'
                        : 'badge-warning'
                    }`}
                  >
                    {doc.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">
            Portfolio Summary
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <DollarSign className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Average NOI</p>
                  <p className="text-xl font-bold text-white">$851,250</p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-emerald-400">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">+5.2%</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Percent className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Average Occupancy</p>
                  <p className="text-xl font-bold text-white">94.5%</p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-emerald-400">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">+2.1%</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/20 rounded-lg">
                  <Building className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Average Cap Rate</p>
                  <p className="text-xl font-bold text-white">6.8%</p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-red-400">
                <TrendingDown className="w-4 h-4" />
                <span className="text-sm">-0.3%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">System Status</h2>
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-red-500'
            }`}
          />
          <span className="text-white">
            API {health?.status || 'unknown'}
          </span>
          <span className="text-slate-500 text-sm ml-2">
            Last checked: {format(new Date(), 'HH:mm:ss')}
          </span>
        </div>
      </div>
    </div>
  )
}
