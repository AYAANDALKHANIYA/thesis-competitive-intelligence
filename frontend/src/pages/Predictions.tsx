import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { predictionsApi } from '@/api/predictions'
import { useWorkspaceEntities } from '@/hooks/useWorkspaceEntities'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LineChart, Network } from 'lucide-react'

export default function Predictions() {
  const { allEntities, selectedCompanyId: workspaceCompanyId } = useWorkspaceEntities()
  const [localCompanyId, setLocalCompanyId] = useState<number | undefined>(workspaceCompanyId || undefined)

  useEffect(() => {
    if (workspaceCompanyId && !localCompanyId) {
      setLocalCompanyId(workspaceCompanyId)
    }
  }, [workspaceCompanyId, localCompanyId])

  const { data: predictionData, isLoading: isPredictionsLoading } = useQuery({
    queryKey: ['predictions', localCompanyId],
    queryFn: () => predictionsApi.getPredictions(localCompanyId!),
    enabled: !!localCompanyId
  })

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: () => predictionsApi.getModels()
  })

  const predictionsList = predictionData?.predictions || []
  const obsCount = predictionData?.observation_count || 0
  const reqObs = predictionData?.required_observations || 30
  const hasInsufficientData = obsCount < reqObs

  // Defensive array handling
  const safeEntities = Array.isArray(allEntities) ? allEntities : []
  const safeModels = Array.isArray(models) ? models : []

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Predictive Analytics</h2>
          <p className="text-muted-foreground mt-1">
            Machine learning forecasts for key metrics based on historical MAI and sentiment.
          </p>
        </div>
        
        <div className="w-full sm:w-[250px]">
          <Select 
            value={localCompanyId?.toString() || ""} 
            onValueChange={(val) => setLocalCompanyId(Number(val))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select Entity" />
            </SelectTrigger>
            <SelectContent>
              {safeEntities.map(c => {
                if (!c || !c.id) return null;
                return <SelectItem key={c.id} value={c.id.toString()}>{c.name || 'Unknown Entity'}</SelectItem>
              })}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="font-serif text-xl flex items-center gap-2">
                <LineChart className="h-5 w-5" />
                Forecasted Metrics
              </CardTitle>
              <CardDescription>
                Near-term projections for selected entity.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isPredictionsLoading ? (
                <Skeleton className="h-[200px] w-full rounded-md" />
              ) : hasInsufficientData ? (
                <div className="flex flex-col h-[200px] items-center justify-center rounded-lg border border-dashed p-6 text-center bg-secondary/20">
                  <p className="text-lg font-medium text-foreground mb-2">Forecast unavailable</p>
                  <p className="text-sm text-muted-foreground mb-4 max-w-md">
                    Insufficient historical observations are currently available to generate a reliable forecast.
                  </p>
                  <Badge variant="outline" className="text-xs">
                    {obsCount} / {reqObs} observations available
                  </Badge>
                </div>
              ) : predictionsList.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {predictionsList.map(pred => {
                    if (!pred || !pred.id) return null;
                    return (
                      <div key={pred.id} className="rounded-lg border p-4">
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                          {(pred.target_metric || '').replace(/_/g, ' ').toUpperCase()}
                        </div>
                        <div className="text-3xl font-serif font-medium">
                          {(pred.predicted_value || 0).toFixed(2)}
                        </div>
                        <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                          <span>Target: {new Date(pred.target_date || Date.now()).toLocaleDateString()}</span>
                          {pred.confidence_lower !== undefined && pred.confidence_upper !== undefined && (
                            <span title="95% Confidence Interval">
                              [{pred.confidence_lower.toFixed(2)} - {pred.confidence_upper.toFixed(2)}]
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="flex flex-col h-[200px] items-center justify-center rounded-lg border border-dashed p-6 text-center">
                  <p className="text-sm font-medium text-muted-foreground mb-1">No forecast data generated.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-1">
          <Card className="shadow-sm h-full">
            <CardHeader>
              <CardTitle className="font-serif text-xl flex items-center gap-2">
                <Network className="h-5 w-5" />
                Active Models
              </CardTitle>
              <CardDescription>
                Models deployed in the current pipeline.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {safeModels.length > 0 ? (
                <ul className="space-y-4">
                  {safeModels.map(model => {
                    if (!model || !model.id) return null;
                    return (
                      <li key={model.id} className="border-b pb-4 last:border-0 last:pb-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{model.model_name || 'Unknown'}</span>
                          {model.is_active && <Badge variant="outline" className="text-[10px]">ACTIVE</Badge>}
                        </div>
                        <div className="text-xs text-muted-foreground font-mono">
                          v{model.version_tag || '1.0.0'}
                        </div>
                        {model.metrics && Object.keys(model.metrics).length > 0 && (
                          <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                            {Object.entries(model.metrics).map(([k, v]) => (
                              <div key={k} className="flex flex-col rounded bg-muted/50 p-1 px-2">
                                <span className="text-muted-foreground uppercase">{k}</span>
                                <span className="font-medium">{(v as number).toFixed(4)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </li>
                    )
                  })}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No models configured.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
