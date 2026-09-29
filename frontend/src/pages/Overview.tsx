import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { companiesApi } from '@/api/companies'
import { useWorkspace } from '@/context/ConfigurationContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Activity, MessageSquare, BrainCircuit, Play, Loader2 } from 'lucide-react'

export default function Overview() {
  const { selectedCompanyId } = useWorkspace()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', selectedCompanyId],
    queryFn: () => analyticsApi.getDashboard(selectedCompanyId ?? undefined),
    enabled: !!selectedCompanyId
  })

  const { mutate: runCollection, isPending: isCollecting } = useMutation({
    mutationFn: () => companiesApi.runInitialCollection(selectedCompanyId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', selectedCompanyId] })
    }
  })

  if (!selectedCompanyId) {
    return (
      <div className="flex flex-col h-[400px] items-center justify-center rounded-xl border border-dashed p-8 text-center bg-secondary/10">
        <h2 className="text-xl font-serif text-primary mb-2">No Organization Selected</h2>
        <p className="text-muted-foreground max-w-md">
          Please select or configure an organization in your workspace to view its competitive intelligence overview.
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
        </div>
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex flex-col h-[400px] items-center justify-center rounded-xl border border-dashed text-muted-foreground p-8 text-center bg-destructive/5 border-destructive/20">
        <AlertTriangle className="h-8 w-8 text-destructive mb-3" />
        <p className="font-medium text-foreground">Failed to load dashboard data.</p>
        <p className="text-sm mt-1">Please try again later or check your connection.</p>
      </div>
    )
  }

  const { market_activity, sentiment, signals, top_topics, recent_insights } = data

  // If we have literally no market activity yet, show the initial collection prompt
  if (market_activity === null && (!sentiment || sentiment.total_documents === 0)) {
    return (
      <div className="flex flex-col h-[400px] items-center justify-center rounded-xl border border-dashed p-8 text-center bg-secondary/10">
        <h2 className="text-xl font-serif text-primary mb-2">Your intelligence workspace is ready.</h2>
        <p className="text-muted-foreground max-w-md mb-6">
          Run an initial collection to begin analyzing your company and competitors.
        </p>
        <Button onClick={() => runCollection()} disabled={isCollecting} className="gap-2">
          {isCollecting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isCollecting ? "Collecting Data..." : "Run Initial Collection"}
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Automation Status Header */}
      {data.automation_status && (
        <div className="flex items-center justify-between text-xs text-muted-foreground bg-secondary/20 py-2 px-4 rounded-md">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              Intelligence updated: {data.automation_status.last_intelligence_update 
                ? new Date(data.automation_status.last_intelligence_update).toLocaleString() 
                : 'Never'}
            </span>
            <span>·</span>
            <span>{data.automation_status.new_documents} new documents (last 24h)</span>
            <span>·</span>
            <span>Next update: {data.automation_status.next_scheduled_collection 
                ? new Date(data.automation_status.next_scheduled_collection).toLocaleString() 
                : 'Pending'}</span>
          </div>
          <span title={`Sources checked: ${data.automation_status.sources_checked}`}>
            {data.automation_status.sources_checked} sources checked
          </span>
        </div>
      )}

      {/* Low Data Banner */}
      {sentiment && sentiment.total_documents > 0 && sentiment.total_documents < 30 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            <div>
              <h3 className="text-sm font-medium text-amber-800 dark:text-amber-500">Building Intelligence</h3>
              <p className="text-xs text-amber-700/80 dark:text-amber-400/80 mt-0.5">
                {sentiment.total_documents} documents collected. More historical data is required for trend detection.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Hero Metrics Row */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Market Activity Index */}
        <Card className="border-l-4 border-l-primary md:col-span-1 shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2 font-medium">
              <Activity className="h-4 w-4" />
              MARKET ACTIVITY INDEX
            </CardDescription>
            <CardTitle className="font-serif text-5xl tracking-tight mt-2">
              {market_activity?.index_value !== undefined ? (
                market_activity.index_value.toFixed(1)
              ) : (
                <span className="text-muted-foreground text-3xl">Pending</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {market_activity ? (
              <div className="text-sm text-muted-foreground mt-2">
                <span className="font-medium text-primary/80 block mb-1">
                  Initial observed activity
                </span>
                Composite metric based on market visibility and current evidence.
              </div>
            ) : (
              <div className="text-sm text-muted-foreground mt-2">
                Awaiting sufficient data to calculate index.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sentiment Summary */}
        <Card className="md:col-span-2 shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2 font-medium">
              <MessageSquare className="h-4 w-4" />
              SENTIMENT DISTRIBUTION
            </CardDescription>
            <CardTitle className="font-serif text-3xl">
              {sentiment ? sentiment.total_documents : 0} <span className="text-xl text-muted-foreground font-sans font-normal">items analyzed</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sentiment && sentiment.total_documents > 0 ? (
              <div className="mt-4 flex h-4 w-full overflow-hidden rounded-full bg-secondary">
                <div 
                  className="bg-emerald-500" 
                  style={{ width: `${(sentiment.distribution?.positive || 0) * 100}%` }}
                  title={`Positive: ${((sentiment.distribution?.positive || 0) * 100).toFixed(0)}%`}
                />
                <div 
                  className="bg-slate-300" 
                  style={{ width: `${(sentiment.distribution?.neutral || 0) * 100}%` }}
                  title={`Neutral: ${((sentiment.distribution?.neutral || 0) * 100).toFixed(0)}%`}
                />
                <div 
                  className="bg-rose-500" 
                  style={{ width: `${(sentiment.distribution?.negative || 0) * 100}%` }}
                  title={`Negative: ${((sentiment.distribution?.negative || 0) * 100).toFixed(0)}%`}
                />
              </div>
            ) : (
              <div className="mt-4 text-sm text-muted-foreground">Insufficient sentiment data to display distribution.</div>
            )}
            <div className="mt-2 flex gap-4 text-xs font-medium text-muted-foreground">
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-emerald-500" /> Positive
              </div>
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-slate-300" /> Neutral
              </div>
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-rose-500" /> Negative
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Emerging Signals */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Emerging Signals
            </CardTitle>
            <CardDescription>Anomalies and notable shifts detected in the market.</CardDescription>
          </CardHeader>
          <CardContent>
            {Array.isArray(signals) && signals.length > 0 ? (
              <ul className="space-y-4">
                {signals.map((signal, idx) => (
                  <li key={`${signal.signal_type}-${idx}`} className="flex items-start justify-between rounded-lg border p-4 transition-colors hover:bg-secondary/20">
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none capitalize">
                        {signal.signal_type.replace(/_/g, ' ')}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(signal.detected_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge variant={signal.growth_rate >= 0.5 ? "destructive" : "secondary"}>
                      Growth: {(signal.growth_rate * 100).toFixed(0)}%
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex flex-col h-[250px] items-center justify-center rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm font-medium text-muted-foreground mb-1">No significant emerging signals have been detected yet.</p>
                <p className="text-xs text-muted-foreground">The system needs sufficient historical activity to identify meaningful changes.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Topics */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="font-serif text-xl">Topic Momentum</CardTitle>
            <CardDescription>Themes accelerating in recent discourse.</CardDescription>
          </CardHeader>
          <CardContent>
            {Array.isArray(top_topics) && top_topics.length > 0 ? (
              <div className="space-y-4">
                {top_topics.map(topic => (
                  <div key={topic.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{topic.name}</span>
                      <span className="text-xs text-muted-foreground">({topic.document_count} mentions)</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex h-32 items-center justify-center rounded-lg border border-dashed">
                <p className="text-sm text-muted-foreground">No topic momentum data available.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Insights */}
      {Array.isArray(recent_insights) && recent_insights.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <BrainCircuit className="h-5 w-5" />
              Latest AI Syntheses
            </CardTitle>
            <CardDescription>Recently generated strategic insights across all monitored entities.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {recent_insights.slice(0, 3).map(insight => (
                <div key={insight.id} className="rounded-lg border bg-card text-card-foreground p-4">
                  <Badge variant="outline" className="mb-2 capitalize">
                    {insight.insight_type.replace(/_/g, ' ')}
                  </Badge>
                  <p className="text-sm leading-relaxed text-muted-foreground line-clamp-4">
                    {typeof insight.content === 'string' ? insight.content : insight.content?.summary || "Complex insight content."}
                  </p>
                  <p className="mt-4 text-xs text-muted-foreground">
                    {new Date(insight.generated_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
