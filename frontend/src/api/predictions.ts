import { apiClient } from './client'
import type { Prediction, ModelVersion } from '@/types'

export const predictionsApi = {
  getPredictions: async (companyId: number): Promise<{ predictions: Prediction[], observation_count: number, required_observations: number }> => {
    const { data } = await apiClient.get(`/api/v1/predictions/${companyId}`)
    return data
  },
  
  getModels: async (): Promise<ModelVersion[]> => {
    const { data } = await apiClient.get('/api/v1/predictions/models')
    return data
  }
}
