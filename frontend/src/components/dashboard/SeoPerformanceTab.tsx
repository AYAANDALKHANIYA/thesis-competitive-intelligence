import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Search, Zap, XCircle, AlertCircle, FileSearch } from 'lucide-react'

export function SeoPerformanceTab({ seo, performance, companies }: { seo: any, performance: any, companies: any[] }) {
  if (!seo || !performance || !companies) return <div className="p-8 text-center text-slateGray">Loading SEO & Performance...</div>

  const getCompanySeo = (id: number) => seo.find((s: any) => s.company_id === id)
  const getCompanyPerf = (id: number) => performance.find((p: any) => p.company_id === id)

  const renderStateValue = (val: any, isPercentage: boolean = false) => {
    if (val === null || val === undefined || val === "UNAVAILABLE" || val === "unavailable") {
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
          Insufficient Data
        </span>
      )
    }
    if (typeof val === 'number') {
      return (
        <span className="font-semibold text-navy">
          {val.toFixed(1)}{isPercentage ? "%" : ""}
        </span>
      )
    }
    return (
      <span className="font-medium text-navy">
        {val}
      </span>
    )
  }

  const technicalChecks = [
    { key: "title_coverage", label: "Title Coverage" },
    { key: "meta_coverage", label: "Meta Description Coverage" },
    { key: "h1_coverage", label: "H1 Coverage" },
    { key: "h2_coverage", label: "H2 Coverage" },
    { key: "canonical_coverage", label: "Canonical Tags" },
    { key: "schema_coverage", label: "Structured Data (Schema)" },
    { key: "image_alt_coverage", label: "Image Alt Text" }
  ]

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">SEO & Performance</h2>
            <p className="text-slateGray mt-1">Technical analysis and web performance metrics.</p>
        </div>
      </div>

      {/* Technical SEO Section */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-tealAccent" />
            <h3 className="text-xl font-serif text-navy">Technical SEO Health</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {companies.map((comp: any) => {
            const compSeo = getCompanySeo(comp.id)
            return (
              <Card key={`seo-${comp.id}`} className="shadow-sm border-lightBorder bg-white">
                <CardHeader className="bg-offwhite border-b border-lightBorder pb-4 pt-5 px-6">
                  <CardTitle className="text-base font-semibold text-navy">
                    {comp.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 px-6">
                  <div className="space-y-6">
                    <div>
                      <p className="text-sm font-medium text-slateGray uppercase tracking-wider mb-2">Technical SEO Score</p>
                      <div className="text-3xl">
                        {renderStateValue(compSeo?.score)}
                      </div>
                    </div>
                    {compSeo?.components?.pages_crawled !== undefined && (
                        <div>
                           <p className="text-sm text-slateGray">Pages Crawled: <span className="font-semibold text-navy">{compSeo.components.pages_crawled}</span></p>
                        </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* Performance Section */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-tealAccent" />
            <h3 className="text-xl font-serif text-navy">Web Performance</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {companies.map((comp: any) => {
            const compPerf = getCompanyPerf(comp.id)
            const status = compPerf?.components?.status
            return (
              <Card key={`perf-${comp.id}`} className="shadow-sm border-lightBorder bg-white">
                <CardHeader className="bg-offwhite border-b border-lightBorder pb-4 pt-5 px-6">
                  <CardTitle className="text-base font-semibold text-navy">
                    {comp.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 px-6">
                   <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium text-slateGray uppercase tracking-wider mb-2">PageSpeed Score</p>
                        <div className="text-xl">
                           {renderStateValue(status === "unavailable" ? "UNAVAILABLE" : compPerf?.score)}
                        </div>
                      </div>
                   </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* Technical Checks Table */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
            <FileSearch className="w-5 h-5 text-tealAccent" />
            <h3 className="text-xl font-serif text-navy">Technical Checks</h3>
        </div>
        
        <Card className="shadow-sm border-lightBorder bg-white overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                <thead className="bg-offwhite/50 text-slateGray border-b border-lightBorder">
                    <tr>
                    <th className="px-6 py-4 font-semibold w-1/4">Check</th>
                    {companies.map((comp: any) => (
                        <th key={`th-${comp.id}`} className="px-6 py-4 font-semibold text-navy text-base">
                        {comp.name}
                        </th>
                    ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-lightBorder">
                    {technicalChecks.map((check) => (
                        <tr key={check.key} className="hover:bg-offwhite transition-colors">
                            <td className="px-6 py-4 font-medium text-slateGray">{check.label}</td>
                            {companies.map((comp: any) => {
                                const compSeo = getCompanySeo(comp.id)
                                const val = compSeo?.components?.[check.key]
                                return (
                                    <td key={`${check.key}-${comp.id}`} className="px-6 py-4">
                                        {renderStateValue(val, true)}
                                    </td>
                                )
                            })}
                        </tr>
                    ))}
                </tbody>
                </table>
            </div>
        </Card>
      </section>

    </div>
  )
}
