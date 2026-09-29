import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { useWorkspace } from '@/context/ConfigurationContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { MessageSquareText, Hash } from 'lucide-react'
import Plot from 'react-plotly.js'

export default function SentimentTopics() {
  const { selectedCompanyId } = useWorkspace()

  const { data: sentiment, isLoading: isSentimentLoading } = useQuery({
    queryKey: ['sentiment-summary', selectedCompanyId],
    queryFn: () => analyticsApi.getSentiment(selectedCompanyId!),
    enabled: !!selectedCompanyId
  })

  const { data: topics, isLoading: isTopicsLoading } = useQuery({
    queryKey: ['topic-summary', selectedCompanyId],
    queryFn: () => analyticsApi.getTopics(selectedCompanyId!),
    enabled: !!selectedCompanyId
  })

  if (isSentimentLoading || isTopicsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[300px] w-full rounded-xl" />
        <Skeleton className="h-[400px] w-full rounded-xl" />
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Sentiment & Topics</h2>
          <p className="text-muted-foreground mt-1">
            Deep dive into NLP-driven sentiment distribution and BERTopic thematic clusters.
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <MessageSquareText className="h-5 w-5" />
              Aggregate Sentiment
            </CardTitle>
            <CardDescription>
              Volume of positive, neutral, and negative documents.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sentiment && sentiment.total > 0 ? (
              <div className="h-[250px] w-full">
                <Plot
                  data={[
                    {
                      x: ['Positive', 'Neutral', 'Negative'],
                      y: [sentiment.positive, sentiment.neutral, sentiment.negative],
                      type: 'bar',
                      marker: {
                        color: ['#10b981', '#cbd5e1', '#f43f5e'],
                      }
                    }
                  ]}
                  layout={{
                    autosize: true,
                    margin: { t: 10, l: 40, r: 20, b: 40 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    xaxis: {
                      showgrid: false,
                      color: '#667085'
                    },
                    yaxis: {
                      showgrid: true,
                      gridcolor: '#E5E7EB',
                      color: '#667085'
                    }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                  config={{ displayModeBar: false, responsive: true }}
                />
              </div>
            ) : (
              <div className="flex h-[250px] items-center justify-center rounded-lg border border-dashed">
                <p className="text-sm text-muted-foreground">Insufficient sentiment data.</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <Hash className="h-5 w-5" />
              Prevalent Topics
            </CardTitle>
            <CardDescription>
              Dominant narratives extracted via BERTopic.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {topics && topics.length > 0 ? (
              <ul className="space-y-4">
                {topics.map(topic => (
                  <li key={topic.topic_id} className="flex items-center justify-between p-3 rounded-lg border bg-card/50">
                    <div className="flex flex-col gap-1">
                      <span className="font-medium">{topic.name}</span>
                      <span className="text-xs text-muted-foreground">{topic.count} documents mentioned</span>
                    </div>
                    <Badge variant={topic.momentum > 0 ? "default" : "secondary"}>
                      {topic.momentum > 0 ? "+" : ""}{topic.momentum.toFixed(1)} mom
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex h-[250px] items-center justify-center rounded-lg border border-dashed">
                <p className="text-sm text-muted-foreground">No topic data available.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
