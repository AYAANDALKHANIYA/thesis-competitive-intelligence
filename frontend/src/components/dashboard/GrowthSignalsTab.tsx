import { AlertCircle, Zap, Shield, BarChart3, Clock } from 'lucide-react'
import { Card, CardContent } from '../ui/card'

export function GrowthSignalsTab({ signals, companies }: { signals: any[], companies: any[] }) {
  if (!signals || !companies) return <div className="p-8 text-center text-slateGray">Loading growth signals...</div>

  // Check if all signals are insufficient historical data
  const isInsufficient = signals.every(s => 
    s.description === "INSUFFICIENT HISTORICAL DATA" || 
    s.signal_type === "INSUFFICIENT_DATA"
  )

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">Growth Signals</h2>
            <p className="text-slateGray mt-1">Observed evidence and early indicators of market growth.</p>
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
                  The system requires additional observations over time before it can establish reliable growth signals. Once sufficient data is collected, observed evidence of growth will appear here.
                </p>
             </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
            {companies.map(company => {
                const companySignals = signals.filter(s => s.company_id === company.id && s.description !== "INSUFFICIENT HISTORICAL DATA")
                
                if (companySignals.length === 0) return null;

                return (
                    <div key={company.id} className="space-y-4">
                        <h3 className="text-xl font-serif text-navy flex items-center gap-2 border-b border-lightBorder pb-2">
                            <span className="w-2 h-2 rounded-full bg-tealAccent"></span>
                            {company.name}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {companySignals.map((signal, idx) => (
                                <Card key={idx} className="bg-white border-lightBorder shadow-sm">
                                    <CardContent className="p-6">
                                        <div className="flex items-start justify-between mb-4">
                                            <div className="flex items-center gap-2">
                                                <Zap className="w-5 h-5 text-tealAccent" />
                                                <span className="font-semibold text-navy uppercase text-sm tracking-wide">
                                                    {signal.signal_type || "Observed Signal"}
                                                </span>
                                            </div>
                                            {signal.confidence && (
                                                <div className="flex items-center gap-1 text-xs font-medium bg-slate-100 text-slateGray px-2 py-1 rounded">
                                                    <Shield className="w-3 h-3" />
                                                    Confidence: {signal.confidence}
                                                </div>
                                            )}
                                        </div>
                                        
                                        <p className="text-navy font-medium mb-4">{signal.description}</p>
                                        
                                        <div className="bg-offwhite p-4 rounded-md border border-lightBorder space-y-3">
                                            <div className="text-sm">
                                                <span className="text-slateGray font-medium uppercase text-xs tracking-wide block mb-1">Observed Evidence</span>
                                                <span className="text-navy">{signal.evidence}</span>
                                            </div>
                                            
                                            {(signal.metric || signal.comparison_period) && (
                                                <div className="flex gap-4 pt-3 border-t border-slate-200 mt-3">
                                                    {signal.metric && (
                                                        <div className="flex items-center gap-1.5 text-sm text-navy">
                                                            <BarChart3 className="w-4 h-4 text-slateGray" />
                                                            <span className="font-medium">{signal.metric}</span>
                                                        </div>
                                                    )}
                                                    {signal.comparison_period && (
                                                        <div className="flex items-center gap-1.5 text-sm text-slateGray">
                                                            <Clock className="w-4 h-4" />
                                                            <span>{signal.comparison_period}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                )
            })}
        </div>
      )}
    </div>
  )
}
