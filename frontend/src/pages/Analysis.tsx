import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import {
  ArrowLeft,
  Download,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  DollarSign,
  Percent,
  Building,
  TrendingUp,
  FileText,
  Share2,
} from 'lucide-react'
import { format } from 'date-fns'

export default function Analysis() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'overview' | 'metrics' | 'raw'>('overview')

  const { data: status, refetch, isLoading } = useQuery({
    queryKey: ['document-status', id],
    queryFn: () => apiClient.getDocumentStatus(id!),
    refetchInterval: 5000,
  })

  const { data: metrics } = useQuery({
    queryKey: ['document-analysis', id],
    queryFn: () => apiClient.getDocumentAnalysis(id!),
    enabled: status?.status === 'completed',
  })

  const getMetricColor = (value: number, thresholds: { warning: number; critical: number }, higherIsBetter: boolean = true) => {
    if (higherIsBetter) {
      if (value >= thresholds.warning) return 'text-emerald-400'
      if (value >= thresholds.critical) return 'text-amber-400'
      return 'text-red-400'
    } else {
      if (value <= thresholds.warning) return 'text-emerald-400'
      if (value <= thresholds.critical) return 'text-amber-400'
      return 'text-red-400'
    }
  }

  const getMetricBg = (value: number, thresholds: { warning: number; critical: number }, higherIsBetter: boolean = true) => {
    if (higherIsBetter) {
      if (value >= thresholds.warning) return 'bg-emerald-500/20'
      if (value >= thresholds.critical) return 'bg-amber-500/20'
      return 'bg-red-500/20'
    } else {
      if (value <= thresholds.warning) return 'bg-emerald-500/20'
      if (value <= thresholds.critical) return 'bg-amber-500/20'
      return 'bg-red-500/20'
    }
  }

  const metricCards = [
    {
      label: 'NOI',
      value: metrics?.noi ? `$${metrics.noi.toLocaleString()}` : '-',
      icon: DollarSign,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/20',
      thresholds: { warning: 0, critical: 0 },
      higherIsBetter: true,
    },
    {
      label: 'Cap Rate',
      value: metrics?.capRate ? `${(metrics.capRate * 100).toFixed(2)}%` : '-',
      icon: Percent,
      color: 'text-blue-400',
      bg: 'bg-blue-500/20',
      thresholds: { warning: 5, critical: 4 },
      higherIsBetter: true,
    },
    {
      label: 'DSCR',
      value: metrics?.dscr?.toFixed(2) || '-',
      icon: TrendingUp,
      color: 'text-purple-400',
      bg: 'bg-purple-500/20',
      thresholds: { warning: 1.25, critical: 1.0 },
      higherIsBetter: true,
    },
    {
      label: 'LTV',
      value: metrics?.ltv ? `${metrics.ltv.toFixed(1)}%` : '-',
      icon: Building,
      color: 'text-amber-400',
      bg: 'bg-amber-500/20',
      thresholds: { warning: 75, critical: 80 },
      higherIsBetter: false,
    },
    {
      label: 'Occupancy',
      value: metrics?.occupancyRate ? `${metrics.occupancyRate.toFixed(1)}%` : '-',
      icon: CheckCircle,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/20',
      thresholds: { warning: 85, critical: 70 },
      higherIsBetter: true,
    },
    {
      label: 'Debt Yield',
      value: metrics?.debtYield ? `${metrics.debtYield.toFixed(2)}%` : '-',
      icon: DollarSign,
      color: 'text-pink-400',
      bg: 'bg-pink-500/20',
      thresholds: { warning: 8, critical: 6 },
      higherIsBetter: true,
    },
  ]

  const isProcessing = status?.status === 'pending' || status?.status === 'processing'

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">Document Analysis</h1>
            <p className="text-slate-400 mt-1">ID: {id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {status?.status === 'completed' && (
            <button className="btn btn-primary">
              <Download className="w-4 h-4" />
              Export
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={`w-3 h-3 rounded-full ${
            status?.status === 'completed'
              ? 'bg-emerald-500'
              : status?.status === 'error'
              ? 'bg-red-500'
              : 'bg-amber-500 animate-pulse'
          }`}
        />
        <span className="text-white capitalize">{status?.status || 'Loading...'}</span>
        {status?.extractions && status.extractions.length > 0 && (
          <span className="text-slate-500 text-sm">
            ({status.extractions.length} extractions)
          </span>
        )}
      </div>

      {isProcessing ? (
        <div className="card text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-500/20 mb-4">
            <RefreshCw className="w-8 h-8 text-primary-400 animate-spin" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Processing Document
          </h2>
          <p className="text-slate-400">
            AI is analyzing your document. This may take a few moments...
          </p>
        </div>
      ) : status?.status === 'error' ? (
        <div className="card text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/20 mb-4">
            <AlertCircle className="w-8 h-8 text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Processing Error
          </h2>
          <p className="text-slate-400">
            There was an error processing your document. Please try uploading
            again.
          </p>
        </div>
      ) : metrics ? (
        <>
          <div className="flex gap-2 border-b border-slate-700">
            {(['overview', 'metrics', 'raw'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  activeTab === tab
                    ? 'text-primary-400 border-b-2 border-primary-400'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'overview' && (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {metricCards.map((metric) => (
                <div
                  key={metric.label}
                  className={`card ${getMetricBg(
                    Number(metric.value) || 0,
                    metric.thresholds,
                    metric.higherIsBetter
                  )}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">{metric.label}</span>
                    <metric.icon className={`w-5 h-5 ${metric.color}`} />
                  </div>
                  <p className={`text-2xl font-bold ${getMetricColor(
                    Number(metric.value) || 0,
                    metric.thresholds,
                    metric.higherIsBetter
                  )}`}>
                    {metric.value}
                  </p>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'metrics' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-6">
                Detailed Metrics
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">
                        Metric
                      </th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">
                        Value
                      </th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {metricCards.map((metric) => (
                      <tr key={metric.label} className="border-b border-slate-800">
                        <td className="py-3 px-4 text-white">{metric.label}</td>
                        <td className="py-3 px-4 text-white font-medium">
                          {metric.value}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`badge ${
                              getMetricColor(
                                Number(metric.value) || 0,
                                metric.thresholds,
                                metric.higherIsBetter
                              ).includes('emerald')
                                ? 'badge-success'
                                : getMetricColor(
                                    Number(metric.value) || 0,
                                    metric.thresholds,
                                    metric.higherIsBetter
                                  ).includes('amber')
                                ? 'badge-warning'
                                : 'badge-error'
                            }`}
                          >
                            {getMetricColor(
                              Number(metric.value) || 0,
                              metric.thresholds,
                              metric.higherIsBetter
                            ).includes('emerald')
                              ? 'Good'
                              : getMetricColor(
                                  Number(metric.value) || 0,
                                  metric.thresholds,
                                  metric.higherIsBetter
                                ).includes('amber')
                              ? 'Warning'
                              : 'Critical'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-4">
                Raw Analysis Data
              </h2>
              <pre className="bg-slate-900 p-4 rounded-lg text-sm text-slate-300 overflow-x-auto">
                {JSON.stringify(metrics, null, 2)}
              </pre>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}
