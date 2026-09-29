import { useQuery } from '@tanstack/react-query'
import { systemApi } from '@/api/documents' // Placed system calls in documents for now
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Database, AlertTriangle, CheckCircle2 } from 'lucide-react'

export default function Sources() {
  const { data: sources, isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => systemApi.getSources()
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Data Sources</h2>
          <p className="text-muted-foreground mt-1">
            Active intelligence feeds, scrapers, and API integrations.
          </p>
        </div>
      </div>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="font-serif text-xl flex items-center gap-2">
            <Database className="h-5 w-5" />
            Source Health
          </CardTitle>
          <CardDescription>
            Real-time status of all configured data sources.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-12 w-full rounded-md" />
              ))}
            </div>
          ) : sources && sources.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Success</TableHead>
                  <TableHead>Errors</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((source) => (
                  <TableRow key={source.source_id}>
                    <TableCell className="font-medium">
                      {source.source_name}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="uppercase text-[10px]">
                        {source.source_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {source.is_active ? (
                        source.is_healthy ? (
                          <div className="flex items-center gap-1 text-emerald-600 text-sm font-medium">
                            <CheckCircle2 className="h-4 w-4" /> Healthy
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-destructive text-sm font-medium">
                            <AlertTriangle className="h-4 w-4" /> Failing
                          </div>
                        )
                      ) : (
                        <div className="text-muted-foreground text-sm">Disabled</div>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {source.last_success ? new Date(source.last_success).toLocaleString() : "Never"}
                    </TableCell>
                    <TableCell>
                      {source.consecutive_errors > 0 ? (
                        <span className="text-destructive font-medium">{source.consecutive_errors}</span>
                      ) : (
                        <span className="text-muted-foreground">0</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed">
              <p className="text-sm text-muted-foreground">No data sources configured.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
