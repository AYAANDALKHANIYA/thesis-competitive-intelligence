import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { useWorkspace } from '@/context/ConfigurationContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import Plot from 'react-plotly.js'

export default function Trends() {
  const { selectedCompanyId } = useWorkspace()

  const { data: trendData, isLoading, error } = useQuery({
    queryKey: ['market-index-trends', selectedCompanyId],
    queryFn: () => analyticsApi.getTrends(selectedCompanyId!),
    enabled: !!selectedCompanyId
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[500px] w-full rounded-xl" />
      </div>
    )
  }

  if (!selectedCompanyId) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-xl border border-dashed text-muted-foreground">
        No organization selected.
      </div>
    )
  }

  if (error || !trendData) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-xl border border-dashed text-muted-foreground">
        Failed to load trend data.
      </div>
    )
  }

  const activityData = Array.isArray(trendData.activity_trend) ? trendData.activity_trend : []
  const xData = activityData.map((d: any) => d.date)
  const yData = activityData.map((d: any) => d.value)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Market Trends</h2>
          <p className="text-muted-foreground mt-1">
            Historical Market Activity Index across the ecosystem.
          </p>
        </div>
      </div>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="font-serif text-xl">MAI Trajectory</CardTitle>
          <CardDescription>
            Long-term sentiment and momentum aggregated into the Market Activity Index.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {activityData.length > 1 ? (
            <div className="h-[400px] w-full">
              <Plot
                data={[
                  {
                    x: xData,
                    y: yData,
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: '#0B1736', size: 6 },
                    line: { color: '#0B1736', width: 2, shape: 'spline' },
                    name: 'Market Activity Index',
                    fill: 'tozeroy',
                    fillcolor: 'rgba(11, 23, 54, 0.05)'
                  },
                ]}
                layout={{
                  autosize: true,
                  margin: { t: 10, l: 40, r: 20, b: 40 },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  xaxis: {
                    showgrid: false,
                    zeroline: false,
                    color: '#667085'
                  },
                  yaxis: {
                    showgrid: true,
                    gridcolor: '#E5E7EB',
                    zeroline: false,
                    color: '#667085'
                  }
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>
          ) : (
            <div className="flex flex-col h-[400px] items-center justify-center rounded-lg border border-dashed text-center">
              <p className="text-sm font-medium text-foreground">Insufficient historical data to plot trends.</p>
              <p className="text-xs text-muted-foreground mt-1">At least two chronological data points are required to establish a trajectory.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
