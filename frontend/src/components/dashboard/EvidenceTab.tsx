import { Database, FileText, Link as LinkIcon, ExternalLink, Globe } from 'lucide-react'
import { Card, CardContent } from '../ui/card'

export function EvidenceTab({ evidence, companies }: { evidence: any[], companies: any[] }) {
  if (!evidence || !companies) return <div className="p-8 text-center text-slateGray">Loading evidence...</div>

  // Handle empty or unavailable states
  if (evidence.length === 0) {
      return (
        <div className="space-y-10 animate-in fade-in duration-500">
          <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
            <div>
                <h2 className="text-3xl font-serif text-navy">Source Evidence</h2>
                <p className="text-slateGray mt-1">Traceability and underlying source material for analytical outputs.</p>
            </div>
          </div>
          <Card className="border border-lightBorder bg-white shadow-sm overflow-hidden">
               <CardContent className="p-16 flex flex-col items-center justify-center text-center">
                  <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-6 border border-slate-200">
                     <Database className="w-8 h-8 text-slate-400" />
                  </div>
                  <h3 className="text-2xl font-serif text-navy mb-3">No Evidence Found</h3>
                  <p className="text-slateGray max-w-lg mx-auto leading-relaxed">
                    No source documents were returned for this analysis.
                  </p>
               </CardContent>
          </Card>
        </div>
      )
  }

  // Calculate Overview Metrics
  const totalEvidence = evidence.length;
  
  // Calculate unique URLs
  const uniqueUrls = new Set(evidence.map(e => e.url).filter(Boolean)).size;

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      <div className="flex items-end justify-between pb-4 border-b border-lightBorder">
        <div>
            <h2 className="text-3xl font-serif text-navy">Source Evidence</h2>
            <p className="text-slateGray mt-1">Traceability and underlying source material for analytical outputs.</p>
        </div>
      </div>

      {/* Evidence Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border border-lightBorder bg-white shadow-sm">
              <CardContent className="p-6 flex items-center gap-4">
                  <div className="p-3 bg-tealAccent/10 rounded-lg text-tealAccent">
                      <FileText className="w-6 h-6" />
                  </div>
                  <div>
                      <p className="text-sm font-medium text-slateGray uppercase tracking-wider mb-1">Total Evidence Records</p>
                      <p className="text-3xl font-serif text-navy">{totalEvidence}</p>
                  </div>
              </CardContent>
          </Card>
          
          <Card className="border border-lightBorder bg-white shadow-sm">
              <CardContent className="p-6 flex items-center gap-4">
                  <div className="p-3 bg-tealAccent/10 rounded-lg text-tealAccent">
                      <Globe className="w-6 h-6" />
                  </div>
                  <div>
                      <p className="text-sm font-medium text-slateGray uppercase tracking-wider mb-1">Unique URLs Analyzed</p>
                      <p className="text-3xl font-serif text-navy">{uniqueUrls}</p>
                  </div>
              </CardContent>
          </Card>
      </div>

      {/* Grouped Evidence Records */}
      <div className="space-y-12">
          {companies.map(company => {
              const companyEvidence = evidence.filter(e => e.company_id === company.id)
              
              if (companyEvidence.length === 0) return null;

              return (
                  <div key={company.id} className="space-y-5">
                      <h3 className="text-xl font-serif text-navy flex items-center gap-2 border-b border-lightBorder pb-2">
                          <span className="w-2 h-2 rounded-full bg-tealAccent"></span>
                          {company.name} Sources ({companyEvidence.length})
                      </h3>
                      <div className="grid grid-cols-1 gap-4">
                          {companyEvidence.map((item, idx) => (
                              <Card key={idx} className="bg-white border-lightBorder shadow-sm hover:shadow-md transition-shadow">
                                  <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                      <div className="space-y-2 flex-grow">
                                          <div className="flex items-center gap-2">
                                              <span className="text-[10px] font-bold tracking-widest uppercase px-2 py-0.5 rounded bg-slate-100 text-slateGray border border-slate-200">
                                                  {item.source_type || "UNKNOWN"}
                                              </span>
                                          </div>
                                          <h4 className="text-navy font-medium leading-snug">
                                              {item.title || "Untitled Document"}
                                          </h4>
                                          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                                              <LinkIcon className="w-3.5 h-3.5" />
                                              <span className="truncate max-w-md">{item.url ? item.url.replace(/^https?:\/\//, '') : "URL Unavailable"}</span>
                                          </div>
                                      </div>
                                      
                                      <div className="shrink-0 flex items-center">
                                          {item.url ? (
                                              <a 
                                                  href={item.url} 
                                                  target="_blank" 
                                                  rel="noopener noreferrer"
                                                  className="inline-flex items-center gap-2 text-sm font-medium text-tealAccent hover:text-tealAccent-light transition-colors px-4 py-2 border border-tealAccent/30 rounded-md hover:bg-tealAccent/5"
                                              >
                                                  View Source
                                                  <ExternalLink className="w-4 h-4" />
                                              </a>
                                          ) : (
                                              <span className="text-sm font-medium text-slate-400 italic px-4 py-2">
                                                  Source URL unavailable
                                              </span>
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
    </div>
  )
}
