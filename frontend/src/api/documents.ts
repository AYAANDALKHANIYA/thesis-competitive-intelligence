import { apiClient } from './client'
import type { PaginatedResponse, DocumentSummary, IngestionRun, SourceHealth } from '@/types'

export const documentsApi = {
  getDocuments: async (params?: { 
    company_id?: number, 
    source_id?: number,
    start_date?: string,
    end_date?: string,
    page?: number,
    page_size?: number
  }): Promise<PaginatedResponse<DocumentSummary>> => {
    const { data } = await apiClient.get('/api/v1/documents', { params })
    return data
  },

  getDocument: async (id: number): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/documents/${id}`)
    return data
  }
}

export const systemApi = {
  getSources: async (): Promise<SourceHealth[]> => {
    const { data } = await apiClient.get('/health/sources')
    return data
  },
  
  getIngestionRuns: async (params?: { limit?: number }): Promise<IngestionRun[]> => {
    const { data } = await apiClient.get('/api/v1/ingestion/runs', { params })
    return data
  }
}
