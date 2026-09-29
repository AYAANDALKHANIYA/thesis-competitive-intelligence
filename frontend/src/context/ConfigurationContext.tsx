import { createContext, useContext, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'

interface PrimaryCompany {
  id: number
  name: string
  domain: string | null
  industry: string | null
}

interface SystemConfiguration {
  configured: boolean
  primary_company: PrimaryCompany | null
}

interface ConfigurationContextType {
  configured: boolean
  primaryCompany: PrimaryCompany | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

const ConfigurationContext = createContext<ConfigurationContextType | undefined>(undefined)

export function ConfigurationProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, error, refetch } = useQuery<SystemConfiguration>({
    queryKey: ['system-configuration'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/configuration')
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2
  })

  return (
    <ConfigurationContext.Provider 
      value={{ 
        configured: data?.configured ?? false, 
        primaryCompany: data?.primary_company ?? null,
        isLoading,
        error: error as Error | null,
        refetch
      }}
    >
      {children}
    </ConfigurationContext.Provider>
  )
}

export function useConfiguration() {
  const context = useContext(ConfigurationContext)
  if (context === undefined) {
    throw new Error('useConfiguration must be used within a ConfigurationProvider')
  }
  return context
}

// Keeping the old hook name exported but mapped to the new one for backward compatibility 
// to ease the transition while we remove old references.
export const useWorkspace = () => {
  const config = useConfiguration()
  return {
    selectedCompanyId: config.primaryCompany?.id ?? null,
    selectedCompanyName: config.primaryCompany?.name ?? null,
    setWorkspace: () => {},
    clearWorkspace: () => {}
  }
}
