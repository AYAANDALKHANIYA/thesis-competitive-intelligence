import { apiClient } from './client'
import type { Company, Competitor } from '@/types'

export const companiesApi = {
  getCompanies: async (): Promise<Company[]> => {
    const { data } = await apiClient.get('/api/v1/companies')
    return data?.items || data || []
  },
  
  getCompany: async (id: number): Promise<Company> => {
    const { data } = await apiClient.get(`/api/v1/companies/${id}`)
    return data
  },

  getCompetitors: async (id: number): Promise<Competitor[]> => {
    const { data } = await apiClient.get(`/api/v1/companies/${id}/competitors`)
    return data
  },

  createCompany: async (company: Partial<Company>): Promise<Company> => {
    const { data } = await apiClient.post('/api/v1/companies', company)
    return data
  },

  addCompetitor: async (companyId: number, competitorId: number, relationshipType: string = "direct"): Promise<any> => {
    const { data } = await apiClient.post(`/api/v1/companies/${companyId}/competitors`, {
      competitor_id: competitorId,
      relationship_type: relationshipType
    })
    return data
  },

  runInitialCollection: async (companyId: number): Promise<any> => {
    const { data } = await apiClient.post(`/api/v1/companies/${companyId}/collect`)
    return data
  }
}
