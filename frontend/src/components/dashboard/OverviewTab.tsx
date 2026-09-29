import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Activity, BarChart2, TrendingUp, AlertCircle, Info } from 'lucide-react'

export function OverviewTab({ overview, primaryCompanyId }: { overview: any, primaryCompanyId: number }) {
  if (!overview) return <div className="p-8 text-center text-slateGray">Loading overview...</div>

  const primaryMetric = overview.metrics?.find((m: any) => m.company_id === primaryCompanyId)
  const aiSummary = overview.ai_intelligence || "AI Intelligence: UNAVAILABLE"
  const isAiUnavailable = aiSummary === "AI Intelligence: UNAVAILABLE"

  const renderComponentState = (label: string, stateValue: any) => {
    let displayState = "Available"
    let textColor = "text-navy"
    
    if (stateValue === "UNAVAILABLE") {
        displayState = "Unavailable"
        textColor = "text-slate-400"
    } else if (stateValue === "INSUFFICIENT_DATA" || stateValue === "insufficient_data") {
        displayState = "Insufficient Data"
        textColor = "text-amber-600"
    }

    return (
        <div key={label} className="flex justify-between items-center text-sm py-2 border-b border-lightBorder last:border-0">
            <span className="text-slateGray">{label}</span>
            <span className={`font-medium ${textColor}`}>{displayState}</span>
        </div>
    )
  }

  const getMaiScore = () => {
    if (primaryMetric?.components?.status === "insufficient_data") return "INSUFFICIENT DATA"
    if (primaryMetric?.components?.status === "unavailable") return "UNAVAILABLE"
    if (primaryMetric?.score !== undefined && primaryMetric?.score !== null) return primaryMetric.score.toFixed(1)
    return "UNAVAILABLE"
  }

  const scoreDisplay = getMaiScore()

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Header Section */}
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">Market Overview</h2>
            <p className="text-slateGray mt-1">Current intelligence snapshot based on analyzed signals.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* MAI Card */}
        <Card className="shadow-sm border-lightBorder bg-white overflow-hidden flex flex-col">
          <CardHeader className="bg-offwhite border-b border-lightBorder pb-4 pt-5 px-6">
            <CardTitle className="text-sm font-semibold tracking-widest text-slateGray uppercase flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-tealAccent" />
                Market Activity Index
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 flex-1 flex flex-col">
            <div className="mb-6">
                <div className="flex items-baseline gap-3">
                    <span className={`text-5xl font-bold ${scoreDisplay === "UNAVAILABLE" || scoreDisplay === "INSUFFICIENT DATA" ? "text-slate-300 text-3xl" : "text-navy font-serif"}`}>
                        {scoreDisplay}
                    </span>
                </div>
                <p className="text-sm text-slateGray mt-2 flex items-center gap-1.5">
                    <Info className="w-4 h-4 text-slate-400" />
                    Based on available signals
                </p>
            </div>
            
            <div className="bg-offwhite rounded-md border border-lightBorder px-4 py-2 mt-auto">
                {renderComponentState("Sentiment", primaryMetric?.components?.Sentiment)}
                {renderComponentState("Content Activity", primaryMetric?.components?.["Content Activity"])}
                {renderComponentState("Topic Momentum", primaryMetric?.components?.["Topic Momentum"])}
                {renderComponentState("Review/Mention Activity", primaryMetric?.components?.["Review/Mention Activity"])}
            </div>
          </CardContent>
        </Card>
        
        {/* AI Insight Card */}
        <Card className="shadow-sm border-lightBorder bg-white flex flex-col">
            <CardHeader className="bg-offwhite border-b border-lightBorder pb-4 pt-5 px-6">
                <CardTitle className="text-sm font-semibold tracking-widest text-slateGray uppercase flex items-center gap-2">
                    <Activity className="w-4 h-4 text-tealAccent" />
                    AI Competitive Intelligence
                </CardTitle>
            </CardHeader>
            <CardContent className="p-6 flex-1 flex items-start">
                {isAiUnavailable ? (
                    <div className="w-full flex flex-col items-center justify-center text-slate-400 py-10 space-y-3">
                        <AlertCircle className="w-8 h-8 opacity-20" />
                        <p className="font-medium tracking-wide">INTELLIGENCE UNAVAILABLE</p>
                    </div>
                ) : (
                    <div className="prose prose-slate max-w-none text-navy leading-relaxed text-sm">
                        {aiSummary.split('\n').map((paragraph: string, idx: number) => (
                            <p key={idx} className={paragraph.trim() ? "mb-3 last:mb-0" : ""}>
                                {paragraph}
                            </p>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
      </div>
      
      {/* Competitor Quick Comparison */}
      <Card className="shadow-sm border-lightBorder bg-white overflow-hidden">
        <CardHeader className="bg-offwhite border-b border-lightBorder pb-4 pt-5 px-6">
            <CardTitle className="text-sm font-semibold tracking-widest text-slateGray uppercase flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-tealAccent" />
                Competitor Activity Snapshot
            </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-offwhite/50 text-slateGray border-b border-lightBorder">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Organization</th>
                            <th className="px-6 py-4 font-semibold">Market Activity Index</th>
                            <th className="px-6 py-4 font-semibold text-right">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-lightBorder">
                        {overview.companies?.map((comp: any) => {
                            const compMetric = overview.metrics?.find((m: any) => m.company_id === comp.id)
                            let scoreTxt = "UNAVAILABLE"
                            if (compMetric?.components?.status === "insufficient_data") scoreTxt = "INSUFFICIENT DATA"
                            else if (compMetric?.score !== undefined && compMetric?.score !== null) scoreTxt = compMetric.score.toFixed(1)
                            
                            const isPrimary = comp.id === primaryCompanyId

                            return (
                                <tr key={comp.id} className={`hover:bg-offwhite transition-colors ${isPrimary ? "bg-offwhite/30" : ""}`}>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-navy flex items-center gap-2">
                                            {comp.name}
                                            {isPrimary && <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-navy text-white tracking-wider">PRIMARY</span>}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`font-semibold ${scoreTxt === "UNAVAILABLE" || scoreTxt === "INSUFFICIENT DATA" ? "text-slate-400 font-normal text-xs" : "text-navy"}`}>
                                            {scoreTxt}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                                            Active
                                        </span>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>
            </div>
        </CardContent>
      </Card>
      
    </div>
  )
}
