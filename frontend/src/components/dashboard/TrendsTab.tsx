import { AlertCircle, TrendingUp, TrendingDown, Minus, Activity, MessageSquare } from 'lucide-react'
import { Card, CardContent } from '../ui/card'

export function TrendsTab({ trends }: { trends: any }) {
  if (!trends) return <div className="p-8 text-center text-slateGray">Loading trends...</div>

  const isInsufficient = trends.status === "unavailable" || trends.status === "INSUFFICIENT_DATA"

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">Market Trends</h2>
            <p className="text-slateGray mt-1">Temporal analysis of topics, sentiment, and content activity.</p>
        </div>
      </div>

      {isInsufficient ? (
        <Card className="border border-lightBorder bg-white shadow-sm overflow-hidden">
             <CardContent className="p-16 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-amber-50 rounded-full flex items-center justify-center mb-6">
                   <AlertCircle className="w-8 h-8 text-amber-500" />
                </div>
                <h3 className="text-2xl font-serif text-navy mb-3">Insufficient historical data</h3>
                <p className="text-slateGray max-w-lg mx-auto leading-relaxed">
                  Additional observations over time are required before reliable temporal trends can be established. 
                  Once sufficient historical data is collected, this section will display topic momentum, sentiment trajectories, and content activity trends.
                </p>
             </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
            {trends.topic_momentum && trends.topic_momentum.length > 0 && (
                <div>
                    <h3 className="text-xl font-serif text-navy mb-4 flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-tealAccent" />
                        Topic Momentum
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {trends.topic_momentum.map((topic: any) => (
                            <Card key={topic.topic_id} className="border border-lightBorder shadow-sm hover:shadow-md transition-shadow">
                                <CardContent className="p-6">
                                    <div className="flex justify-between items-start mb-4">
                                        <h4 className="font-semibold text-navy text-lg capitalize truncate pr-2" title={topic.topic_name}>
                                            {topic.topic_name}
                                        </h4>
                                        <div className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 shrink-0 ${
                                            topic.momentum === 'accelerating' ? 'bg-emerald-50 text-emerald-700' :
                                            topic.momentum === 'decelerating' ? 'bg-rose-50 text-rose-700' :
                                            'bg-slate-100 text-slate-700'
                                        }`}>
                                            {topic.momentum === 'accelerating' && <TrendingUp className="w-3 h-3" />}
                                            {topic.momentum === 'decelerating' && <TrendingDown className="w-3 h-3" />}
                                            {topic.momentum === 'stable' && <Minus className="w-3 h-3" />}
                                            <span className="capitalize">{topic.momentum}</span>
                                        </div>
                                    </div>
                                    <div className="flex gap-6">
                                        <div>
                                            <p className="text-xs text-slateGray mb-1">Recent</p>
                                            <p className="text-2xl font-medium text-navy">{topic.recent_count}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-slateGray mb-1">Historical</p>
                                            <p className="text-2xl font-medium text-slate-400">{topic.historical_count}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-slateGray mb-1">Growth</p>
                                            <p className={`text-xl font-medium ${topic.growth_rate > 1 ? 'text-emerald-600' : topic.growth_rate < 1 ? 'text-rose-600' : 'text-slate-500'}`}>
                                                {topic.growth_rate > 1 ? '+' : ''}{((topic.growth_rate - 1) * 100).toFixed(0)}%
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}
            
            {((trends.activity_trend && trends.activity_trend.length > 0) || (trends.sentiment_trend && trends.sentiment_trend.length > 0)) && (
                <div>
                     <h3 className="text-xl font-serif text-navy mb-4 flex items-center gap-2 mt-8">
                        <Activity className="w-5 h-5 text-tealAccent" />
                        Temporal Metrics
                    </h3>
                    <Card className="border border-lightBorder bg-white shadow-sm overflow-hidden">
                        <CardContent className="p-8">
                            <p className="text-slateGray text-sm">
                                Additional temporal visualizations require more time-series data to render meaningful charts.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
      )}
    </div>
  )
}
