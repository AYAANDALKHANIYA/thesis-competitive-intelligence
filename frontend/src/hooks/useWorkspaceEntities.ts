import { useQuery } from '@tanstack/react-query'
import { companiesApi } from '@/api/companies'
import { useWorkspace } from '@/context/ConfigurationContext'
import type { Company } from '@/types'

export function useWorkspaceEntities() {
  const { selectedCompanyId } = useWorkspace()

  const { data: primaryCompany, isLoading: isCompanyLoading } = useQuery({
    queryKey: ['company', selectedCompanyId],
    queryFn: () => companiesApi.getCompany(selectedCompanyId!),
    enabled: !!selectedCompanyId
  })

  const { data: competitorsResponse, isLoading: isCompetitorsLoading } = useQuery({
    queryKey: ['competitors', selectedCompanyId],
    queryFn: () => companiesApi.getCompetitors(selectedCompanyId!),
    enabled: !!selectedCompanyId
  })

  // Safely extract competitors array, handling potential pagination or unexpected structures
  const competitorsList = Array.isArray(competitorsResponse) 
    ? competitorsResponse 
    : (competitorsResponse as any)?.items 
      ? (competitorsResponse as any).items 
      : []

  const validCompetitors = competitorsList
    .map((c: any) => c?.competitor_company)
    .filter((c: any) => c && typeof c === 'object' && c.id && c.name) as Company[]

  const validPrimary = primaryCompany && typeof primaryCompany === 'object' && primaryCompany.id && primaryCompany.name 
    ? primaryCompany 
    : null

  const allEntities = validPrimary ? [validPrimary, ...validCompetitors] : validCompetitors

  return {
    primaryCompany: validPrimary,
    competitors: validCompetitors,
    allEntities,
    isLoading: isCompanyLoading || isCompetitorsLoading,
    selectedCompanyId
  }
}
