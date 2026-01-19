import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileSpreadsheet,
  FileType,
} from 'lucide-react'
import toast from 'react-hot-toast'

interface UploadedFile {
  file: File
  id?: string
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
}

export default function Upload() {
  const navigate = useNavigate()
  const [files, setFiles] = useState<UploadedFile[]>([])

  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: (data, file) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file.name === file.name
            ? { ...f, id: data.id, status: 'processing' as const }
            : f
        )
      )
      toast.success(`Uploaded: ${file.name}`)
      navigate(`/analysis/${data.id}`)
    },
    onError: (error: Error, file) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file.name === file.name
            ? { ...f, status: 'error' as const, error: error.message }
            : f
        )
      )
      toast.error(`Failed to upload: ${file.name}`)
    },
  })

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.map((file) => ({
        file,
        status: 'pending' as const,
      }))
      setFiles((prev) => [...prev, ...newFiles])

      newFiles.forEach((f) => {
        uploadMutation.mutate(f.file)
      })
    },
    [uploadMutation]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [
        '.xlsx',
      ],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [
        '.docx',
      ],
    },
    maxSize: 50 * 1024 * 1024,
  })

  const removeFile = (name: string) => {
    setFiles((prev) => prev.filter((f) => f.file.name !== name))
  }

  const getFileIcon = (file: File) => {
    if (file.type.includes('pdf')) {
      return <FileText className="w-8 h-8 text-red-400" />
    }
    if (file.type.includes('spreadsheet') || file.name.endsWith('.xlsx')) {
      return <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
    }
    if (file.type.includes('word') || file.name.endsWith('.docx')) {
      return <FileType className="w-8 h-8 text-blue-400" />
    }
    return <FileText className="w-8 h-8 text-slate-400" />
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Upload Documents</h1>
        <p className="text-slate-400 mt-1">
          Upload rent rolls, P&L statements, operating statements, or lease
          documents
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div
            className={`p-4 rounded-full ${
              isDragActive ? 'bg-primary-500/20' : 'bg-slate-800'
            }`}
          >
            <Upload
              className={`w-8 h-8 ${
                isDragActive ? 'text-primary-400' : 'text-slate-400'
              }`}
            />
          </div>
          <div>
            <p className="text-lg font-medium text-white">
              {isDragActive
                ? 'Drop your files here'
                : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-slate-400 mt-1">
              or click to browse
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>Supports:</span>
            <span className="px-2 py-0.5 bg-slate-800 rounded">PDF</span>
            <span className="px-2 py-0.5 bg-slate-800 rounded">Excel</span>
            <span className="px-2 py-0.5 bg-slate-800 rounded">Word</span>
            <span>• Max 50MB</span>
          </div>
        </div>
      </div>

      {files.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">
            Uploaded Files ({files.length})
          </h2>
          <div className="space-y-3">
            {files.map((f) => (
              <div
                key={f.file.name}
                className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg"
              >
                <div className="flex items-center gap-4">
                  {getFileIcon(f.file)}
                  <div>
                    <p className="text-sm font-medium text-white">
                      {f.file.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {(f.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {f.status === 'pending' && (
                    <span className="badge badge-warning">Pending</span>
                  )}
                  {f.status === 'uploading' && (
                    <span className="badge badge-info">
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                      Uploading
                    </span>
                  )}
                  {f.status === 'processing' && (
                    <span className="badge badge-info">
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                      Processing
                    </span>
                  )}
                  {f.status === 'completed' && (
                    <span className="badge badge-success">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Completed
                    </span>
                  )}
                  {f.status === 'error' && (
                    <span className="badge badge-error">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {f.error || 'Error'}
                    </span>
                  )}
                  <button
                    onClick={() => removeFile(f.file.name)}
                    className="p-1 text-slate-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">
          Supported Document Types
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center gap-3 mb-2">
              <FileText className="w-5 h-5 text-red-400" />
              <span className="font-medium text-white">Rent Roll</span>
            </div>
            <p className="text-sm text-slate-400">
              Tenant information, lease terms, occupancy data, and rent analysis
            </p>
          </div>
          <div className="p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center gap-3 mb-2">
              <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
              <span className="font-medium text-white">P&L Statement</span>
            </div>
            <p className="text-sm text-slate-400">
              Revenue items, expense categories, NOI calculations, and historical
              comparisons
            </p>
          </div>
          <div className="p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center gap-3 mb-2">
              <FileType className="w-5 h-5 text-blue-400" />
              <span className="font-medium text-white">Operating Statement</span>
            </div>
            <p className="text-sm text-slate-400">
              Combined financial metrics, budget variance analysis, and period
              comparisons
            </p>
          </div>
          <div className="p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center gap-3 mb-2">
              <FileType className="w-5 h-5 text-amber-400" />
              <span className="font-medium text-white">Lease Document</span>
            </div>
            <p className="text-sm text-slate-400">
              Key lease terms, financial obligations, special provisions, and
              key dates
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
