import { AlertCircle, TrendingUp, TrendingDown, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'

export function PredictionsTab({ predictions }: { predictions: any }) {
  if (!predictions) return <div className="p-8 text-center text-slateGray">Loading predictions...</div>

  const isInsufficient = predictions.status === "unavailable" || predictions.status === "INSUFFICIENT_DATA"

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">Predictions</h2>
            <p className="text-slateGray mt-1">Data-driven forecasts and future market state modeling.</p>
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
                  The platform requires additional historical observations before a reliable forecast can be generated.
                </p>
             </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {predictions.forecasts && predictions.forecasts.map((forecast: any, idx: number) => (
                    <Card key={idx} className="border border-lightBorder shadow-sm hover:shadow-md transition-shadow flex flex-col h-full">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-lg font-serif text-navy flex items-center justify-between">
                                <span className="truncate pr-2" title={forecast.metric_name}>{forecast.metric_name}</span>
                                <div className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 shrink-0 ${
                                    forecast.trend === 'up' ? 'bg-emerald-50 text-emerald-700' :
                                    forecast.trend === 'down' ? 'bg-rose-50 text-rose-700' :
                                    'bg-slate-100 text-slate-700'
                                }`}>
                                    {forecast.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                                    {forecast.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                                    <span className="uppercase">{forecast.trend}</span>
                                </div>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex flex-col flex-grow">
                            <div className="flex gap-8 mb-6 mt-2">
                                <div>
                                    <p className="text-xs text-slateGray mb-1 uppercase tracking-wider font-semibold">Current</p>
                                    <p className="text-3xl font-medium text-slate-400">{forecast.current_value.toFixed(1)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slateGray mb-1 uppercase tracking-wider font-semibold">30d Forecast</p>
                                    <p className={`text-3xl font-medium ${forecast.trend === 'up' ? 'text-emerald-600' : forecast.trend === 'down' ? 'text-rose-600' : 'text-slate-600'}`}>
                                        {forecast.predicted_value_30d.toFixed(1)}
                                    </p>
                                </div>
                            </div>
                            
                            <div className="mt-auto">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Driving Factors</span>
                                </div>
                                <ul className="space-y-2">
                                    {forecast.factors.map((factor: string, fIdx: number) => (
                                        <li key={fIdx} className="text-sm text-slateGray flex items-start gap-2">
                                            <Info className="w-4 h-4 text-tealAccent shrink-0 mt-0.5" />
                                            <span>{factor}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            
                            <div className="mt-6 pt-4 border-t border-slate-100 flex justify-between items-center text-xs">
                                <span className="text-slate-400">Confidence Score</span>
                                <span className="font-medium text-navy bg-slate-100 px-2 py-0.5 rounded">{forecast.confidence}%</span>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
      )}
    </div>
  )
}
