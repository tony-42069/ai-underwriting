export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  role: 'admin' | 'analyst' | 'viewer'
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AuthResponse {
  user: User
  token: Token
}

export interface Document {
  id: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  created_at: string
  processing_result?: ProcessingResult
  analysis_result?: FinancialMetrics
}

export interface ProcessingResult {
  status: string
  text: string
  extractions: Extraction[]
  processed_at: string
}

export interface Extraction {
  extractor: string
  data: Record<string, unknown>
  confidence: {
    overall: number
    [key: string]: unknown
  }
}

export interface DocumentStatus {
  status: 'pending' | 'processing' | 'completed' | 'error'
  extractions?: {
    type: string
    confidence: number
  }[]
}

export interface FinancialMetrics {
  noi: number
  capRate: number
  dscr: number
  ltv: number
  occupancyRate: number
  grossIncome?: number
  totalExpenses?: number
  expenseRatio?: number
  debtYield?: number
  loanAmount?: number
  propertyValue?: number
  debtService?: number
}

export interface ValidationReport {
  overall_valid: boolean
  confidence_score: number
  risk_flags: string[]
  validated_at: string
}

export interface UploadResponse {
  status: string
  id: string
  filename: string
  extractions?: {
    type: string
    confidence: number
  }[]
}

export interface ApiError {
  status: string
  error: string
  detail?: string
}
