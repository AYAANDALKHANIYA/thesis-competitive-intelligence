import { apiClient } from './client'
import type { DashboardResponse, SentimentSummary, TopicSummary } from '@/types'

export const analyticsApi = {
  getDashboard: async (companyId?: number): Promise<DashboardResponse> => {
    const params = companyId ? { company_id: companyId } : {}
    const { data } = await apiClient.get('/api/v1/analytics/dashboard', { params })
    return data
  },

  getSentiment: async (companyId?: number): Promise<SentimentSummary> => {
    const params = companyId ? { company_id: companyId } : {}
    const { data } = await apiClient.get('/api/v1/analytics/sentiment', { params })
    return data
  },

  getTopics: async (companyId?: number): Promise<TopicSummary[]> => {
    const params = companyId ? { company_id: companyId } : {}
    const { data } = await apiClient.get('/api/v1/analytics/topics', { params })
    return data
  },

  getTrends: async (companyId?: number): Promise<any> => {
    const params = companyId ? { company_id: companyId } : {}
    const { data } = await apiClient.get('/api/v1/analytics/trends', { params })
    return data
  },

  getMarketIndex: async (companyId?: number): Promise<any> => {
    const params = companyId ? { company_id: companyId } : {}
    const { data } = await apiClient.get('/api/v1/analytics/market-index', { params })
    return data
  }
}
