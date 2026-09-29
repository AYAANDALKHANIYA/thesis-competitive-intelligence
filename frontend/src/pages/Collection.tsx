import { useQuery } from '@tanstack/react-query'
import { systemApi } from '@/api/documents'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Activity, Clock, CheckCircle2, XCircle } from 'lucide-react'

export default function Collection() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['collection-runs'],
    queryFn: () => systemApi.getIngestionRuns({ limit: 50 })
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Collection Runs</h2>
          <p className="text-muted-foreground mt-1">
            Execution history of the ingestion engine.
          </p>
        </div>
      </div>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="font-serif text-xl flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Ingestion Pipeline Logs
          </CardTitle>
          <CardDescription>
            Recent automated and manual data collection jobs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-12 w-full rounded-md" />
              ))}
            </div>
          ) : runs && runs.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Source ID</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Items (New/Total)</TableHead>
                  <TableHead>Errors</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>
                      {run.status === 'COMPLETED' ? (
                        <Badge variant="outline" className="border-emerald-200 text-emerald-700 bg-emerald-50">
                          <CheckCircle2 className="mr-1 h-3 w-3" /> Completed
                        </Badge>
                      ) : run.status === 'FAILED' ? (
                        <Badge variant="outline" className="border-destructive/30 text-destructive bg-destructive/10">
                          <XCircle className="mr-1 h-3 w-3" /> Failed
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <Clock className="mr-1 h-3 w-3" /> {run.status}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {run.source_id}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(run.started_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm">
                      <span className="font-medium text-emerald-600">+{run.items_new}</span> / {run.items_found}
                    </TableCell>
                    <TableCell className="text-sm max-w-[200px] truncate">
                      {run.error_message ? (
                        <span className="text-destructive truncate inline-block w-full" title={run.error_message}>
                          {run.error_message}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed">
              <p className="text-sm text-muted-foreground">No ingestion runs found.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
