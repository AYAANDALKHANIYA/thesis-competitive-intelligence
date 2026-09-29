import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Users, XCircle, AlertCircle } from 'lucide-react'

export function CompetitorsTab({ data }: { data: any }) {
  if (!data || !data.comparison) return <div className="p-8 text-center text-slateGray">Loading competitors...</div>

  const renderStateValue = (val: any) => {
    if (val === "UNAVAILABLE") {
      return (
        <span className="inline-flex items-center gap-1.5 text-slate-400 text-sm">
          <XCircle className="w-4 h-4" />
          Unavailable
        </span>
      )
    }
    if (val === "INSUFFICIENT_DATA" || val === "insufficient_data") {
      return (
        <span className="inline-flex items-center gap-1.5 text-amber-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          Insufficient historical data
        </span>
      )
    }
    if (typeof val === 'number') {
      return (
        <span className="font-semibold text-navy">
          {val.toFixed(1)}
        </span>
      )
    }
    return (
      <span className="font-medium text-navy">
        {val}
      </span>
    )
  }

  const getMetricValue = (comp: any, metricName: string) => {
    const m = comp.metrics?.[metricName]
    if (!m) return "UNAVAILABLE"
    
    // Check if the component says it's unavailable or insufficient
    if (m.components?.status === "unavailable") return "UNAVAILABLE"
    if (m.components?.status === "insufficient_data") return "INSUFFICIENT_DATA"
    
    // Otherwise return value
    if (m.value !== undefined && m.value !== null) return m.value
    return "UNAVAILABLE"
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">Competitor Analysis</h2>
            <p className="text-slateGray mt-1">Detailed comparison across key market activity indicators.</p>
        </div>
      </div>

      <Card className="shadow-sm border-lightBorder bg-white overflow-hidden">
        <CardHeader className="bg-offwhite border-b border-lightBorder pb-4 pt-5 px-6">
            <CardTitle className="text-sm font-semibold tracking-widest text-slateGray uppercase flex items-center gap-2">
                <Users className="w-4 h-4 text-tealAccent" />
                Direct Comparison
            </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-offwhite/50 text-slateGray border-b border-lightBorder">
                <tr>
                  <th className="px-6 py-4 font-semibold w-1/4">Metric</th>
                  {data.comparison.map((comp: any) => (
                    <th key={comp.id} className="px-6 py-4 font-semibold text-navy text-base">
                      {comp.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-lightBorder">
                
                {/* Market Activity Index */}
                <tr className="hover:bg-offwhite transition-colors">
                  <td className="px-6 py-4 font-medium text-slateGray">Market Activity Index</td>
                  {data.comparison.map((comp: any) => (
                    <td key={comp.id} className="px-6 py-4">
                      {renderStateValue(getMetricValue(comp, "market_activity_index"))}
                    </td>
                  ))}
                </tr>

                {/* Sub-components of MAI */}
                <tr className="hover:bg-offwhite transition-colors bg-offwhite/10">
                  <td className="px-6 py-4 pl-10 text-slateGray text-xs uppercase tracking-wider">↳ Sentiment</td>
                  {data.comparison.map((comp: any) => {
                    const mai = comp.metrics?.["market_activity_index"]?.components
                    return (
                      <td key={comp.id} className="px-6 py-3">
                        {renderStateValue(mai?.["Sentiment"] || "UNAVAILABLE")}
                      </td>
                    )
                  })}
                </tr>

                <tr className="hover:bg-offwhite transition-colors bg-offwhite/10">
                  <td className="px-6 py-4 pl-10 text-slateGray text-xs uppercase tracking-wider">↳ Content Activity</td>
                  {data.comparison.map((comp: any) => {
                    const mai = comp.metrics?.["market_activity_index"]?.components
                    return (
                      <td key={comp.id} className="px-6 py-3">
                        {renderStateValue(mai?.["Content Activity"] || "UNAVAILABLE")}
                      </td>
                    )
                  })}
                </tr>

                <tr className="hover:bg-offwhite transition-colors bg-offwhite/10">
                  <td className="px-6 py-4 pl-10 text-slateGray text-xs uppercase tracking-wider">↳ Topic Momentum</td>
                  {data.comparison.map((comp: any) => {
                    const mai = comp.metrics?.["market_activity_index"]?.components
                    return (
                      <td key={comp.id} className="px-6 py-3">
                        {renderStateValue(mai?.["Topic Momentum"] || "UNAVAILABLE")}
                      </td>
                    )
                  })}
                </tr>

                <tr className="hover:bg-offwhite transition-colors bg-offwhite/10">
                  <td className="px-6 py-4 pl-10 text-slateGray text-xs uppercase tracking-wider">↳ Review / Mention</td>
                  {data.comparison.map((comp: any) => {
                    const mai = comp.metrics?.["market_activity_index"]?.components
                    return (
                      <td key={comp.id} className="px-6 py-3">
                        {renderStateValue(mai?.["Review/Mention Activity"] || "UNAVAILABLE")}
                      </td>
                    )
                  })}
                </tr>

                {/* Technical SEO Score */}
                <tr className="hover:bg-offwhite transition-colors">
                  <td className="px-6 py-4 font-medium text-slateGray">Technical SEO Score</td>
                  {data.comparison.map((comp: any) => (
                    <td key={comp.id} className="px-6 py-4">
                      {renderStateValue(getMetricValue(comp, "Technical SEO Score"))}
                    </td>
                  ))}
                </tr>

              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

    </div>
  )
}
