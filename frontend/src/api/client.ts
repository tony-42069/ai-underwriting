import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = useAuthStore.getState().token
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          useAuthStore.getState().logout()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post<UploadResponse>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  }

  async getDocumentStatus(id: string): Promise<DocumentStatus> {
    const response = await this.client.get<DocumentStatus>(
      `/documents/${id}/status`
    )
    return response.data
  }

  async getDocumentAnalysis(id: string): Promise<FinancialMetrics> {
    const response = await this.client.get<FinancialMetrics>(
      `/documents/${id}/analysis`
    )
    return response.data
  }

  async getHealth(): Promise<{ status: string; service: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await this.client.post<AuthResponse>(
      '/auth/token',
      formData
    )
    return response.data
  }

  async register(data: {
    email: string
    username: string
    password: string
    full_name?: string
  }): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/register', data)
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me')
    return response.data
  }

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(
      '/auth/change-password',
      { current_password: currentPassword, new_password: newPassword }
    )
    return response.data
  }
}

export const apiClient = new ApiClient()
