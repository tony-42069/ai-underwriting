import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { Document, FinancialMetrics, UploadResponse } from '../types'
import toast from 'react-hot-toast'

export function useDocumentStatus(documentId: string) {
  return useQuery({
    queryKey: ['document-status', documentId],
    queryFn: () => apiClient.getDocumentStatus(documentId),
    refetchInterval: (data) => {
      if (data?.status === 'pending' || data?.status === 'processing') {
        return 5000
      }
      return false
    },
  })
}

export function useDocumentAnalysis(documentId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['document-analysis', documentId],
    queryFn: () => apiClient.getDocumentAnalysis(documentId),
    enabled: enabled && !!documentId,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['document-status', data.id] })
      toast.success('Document uploaded successfully')
    },
    onError: () => {
      toast.error('Failed to upload document')
    },
  })
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000,
  })
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ['current-user'],
    queryFn: () => apiClient.getCurrentUser(),
    retry: false,
  })
}

export function useChangePassword() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string
      newPassword: string
    }) => apiClient.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] })
      toast.success('Password changed successfully')
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to change password')
    },
  })
}
