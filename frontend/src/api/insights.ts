import { apiClient } from './client'
import type { PaginatedResponse, InsightResponse } from '@/types'

export const insightsApi = {
  getInsights: async (params?: {
    company_id?: number,
    insight_type?: string,
    start_date?: string,
    end_date?: string,
    page?: number,
    page_size?: number
  }): Promise<PaginatedResponse<InsightResponse>> => {
    const { data } = await apiClient.get('/api/v1/insights', { params })
    return data
  },
  
  getInsight: async (id: number): Promise<InsightResponse> => {
    const { data } = await apiClient.get(`/api/v1/insights/${id}`)
    return data
  }
}
