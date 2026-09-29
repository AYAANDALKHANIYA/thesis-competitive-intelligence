import { useQuery } from '@tanstack/react-query'
import { companiesApi } from '@/api/companies'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Building2 } from 'lucide-react'
import { useWorkspaceEntities } from '@/hooks/useWorkspaceEntities'

export default function Competitors() {
  const { allEntities, isLoading, selectedCompanyId } = useWorkspaceEntities()

  const { error } = useQuery({
    queryKey: ['competitors', selectedCompanyId],
    queryFn: () => companiesApi.getCompetitors(selectedCompanyId!),
    enabled: !!selectedCompanyId
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[400px] w-full rounded-xl" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[400px] items-center justify-center rounded-xl border border-dashed text-destructive">
        Failed to load competitors data. Please try again later.
      </div>
    )
  }

  if (!selectedCompanyId) {
    return (
      <div className="flex h-[400px] items-center justify-center rounded-xl border border-dashed text-muted-foreground">
        No organization selected.
      </div>
    )
  }

  // Strictly filter to the requested entities to prevent global data leakage
  const allowedNames = ['Curato', 'Breef', 'DesignRush']
  const filteredEntities = (allEntities || []).filter(company => 
    company && company.name && allowedNames.includes(company.name)
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Monitored Entities</h2>
          <p className="text-muted-foreground mt-1">
            Companies and competitors currently tracked by the intelligence engine.
          </p>
        </div>
      </div>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="font-serif text-xl flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Entity Roster
          </CardTitle>
          <CardDescription>
            {filteredEntities.length} organizations in this workspace.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Organization</TableHead>
                <TableHead>Ticker</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEntities.map((company) => {
                if (!company || !company.id) return null;
                return (
                  <TableRow key={company.id}>
                    <TableCell className="font-medium">
                      {company.name || 'Unknown Entity'}
                    </TableCell>
                    <TableCell>
                      {company.ticker ? (
                        <Badge variant="outline" className="font-mono">{company.ticker}</Badge>
                      ) : (
                        <span className="text-muted-foreground text-xs">Private</span>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {company.industry || "Technology"}
                    </TableCell>
                    <TableCell>
                      {company.id === selectedCompanyId ? (
                        <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">Primary</Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-slate-100 text-slate-800 hover:bg-slate-200">Competitor</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
              {filteredEntities.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                    No entities found matching the current workspace profile.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
