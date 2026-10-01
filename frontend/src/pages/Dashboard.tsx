import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Plus, X, Globe, Activity, LayoutDashboard, Users, Search, TrendingUp, Zap, FileText, Target } from 'lucide-react'
import { apiClient } from '../api/client'

import { OverviewTab } from '../components/dashboard/OverviewTab'
import { CompetitorsTab } from '../components/dashboard/CompetitorsTab'
import { SeoPerformanceTab } from '../components/dashboard/SeoPerformanceTab'
import { TrendsTab } from '../components/dashboard/TrendsTab'
import { GrowthSignalsTab } from '../components/dashboard/GrowthSignalsTab'
import { EvidenceTab } from '../components/dashboard/EvidenceTab'
import { PredictionsTab } from '../components/dashboard/PredictionsTab'

interface CompanyInput {
  name: string
  website: string
}

type TabType = 'overview' | 'competitors' | 'seo' | 'trends' | 'growth' | 'evidence' | 'predictions'

export default function Dashboard() {
  const [company, setCompany] = useState<CompanyInput>({ name: '', website: '' })
  const [competitors, setCompetitors] = useState<CompanyInput[]>([{ name: '', website: '' }])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('overview')

  // Data states
  const [overviewData, setOverviewData] = useState<any>(null)
  const [competitorsData, setCompetitorsData] = useState<any>(null)
  const [seoData, setSeoData] = useState<any>(null)
  const [performanceData, setPerformanceData] = useState<any>(null)
  const [trendsData, setTrendsData] = useState<any>(null)
  const [growthData, setGrowthData] = useState<any>(null)
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [predictionsData, setPredictionsData] = useState<any>(null)

  const handleAddCompetitor = () => {
    if (competitors.length < 10) {
      setCompetitors([...competitors, { name: '', website: '' }])
    }
  }

  const handleRemoveCompetitor = (index: number) => {
    const newCompetitors = [...competitors]
    newCompetitors.splice(index, 1)
    setCompetitors(newCompetitors)
  }

  const handleCompetitorChange = (index: number, field: keyof CompanyInput, value: string) => {
    const newCompetitors = [...competitors]
    newCompetitors[index][field] = value
    setCompetitors(newCompetitors)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsAnalyzing(true)
    setAnalysisId(null)
    setStatus(null)
    setActiveTab('overview')
    
    try {
      const res = await apiClient.post('/api/v1/analysis/api/v1/analysis', {
        company,
        competitors: competitors.filter(c => c.name && c.website)
      })
      setAnalysisId(res.data.analysis_id)
      setStatus(res.data.status)
    } catch (err) {
      console.error(err)
      setIsAnalyzing(false)
      alert("Failed to start analysis")
    }
  }

  const fetchAllData = async (id: string) => {
    try {
        const [ov, comp, seo, perf, trends, growth, ev, pred] = await Promise.all([
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/overview`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/competitors`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/seo`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/performance`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/trends`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/growth-signals`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/evidence`),
            apiClient.get(`/api/v1/analysis/api/v1/analysis/${id}/predictions`)
        ])
        setOverviewData(ov.data)
        setCompetitorsData(comp.data)
        setSeoData(seo.data)
        setPerformanceData(perf.data)
        setTrendsData(trends.data)
        setGrowthData(growth.data)
        setEvidenceData(ev.data)
        setPredictionsData(pred.data)
    } catch (error) {
        console.error("Failed to fetch dashboard data:", error)
    }
  }

  useEffect(() => {
    if (analysisId && (status === "COMPLETED" || status === "PARTIAL" || status === "FAILED") && !overviewData) {
        fetchAllData(analysisId)
    }
  }, [analysisId, status])

  useEffect(() => {
    if (!analysisId) return;

    let isMounted = true;
    let interval: ReturnType<typeof setInterval> | null = null;

    const checkStatus = async () => {
      try {
        const res = await apiClient.get(`/api/v1/analysis/api/v1/analysis/${analysisId}`)
        if (!isMounted) return;
        
        const currentStatus = res.data.status;
        setStatus(currentStatus);
        
        if (currentStatus === "COMPLETED" || currentStatus === "PARTIAL" || currentStatus === "FAILED") {
          setIsAnalyzing(false);
          if (interval) {
              clearInterval(interval);
              interval = null;
          }
        }
      } catch (err) {
        console.error(err)
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 2000);

    return () => {
      isMounted = false;
      if (interval) clearInterval(interval);
    };
  }, [analysisId])

  if (analysisId && (status === "COMPLETED" || status === "PARTIAL" || status === "FAILED")) {
    const tabs = [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'competitors', label: 'Competitors', icon: Users },
        { id: 'seo', label: 'SEO & Performance', icon: Search },
        { id: 'trends', label: 'Trends', icon: TrendingUp },
        { id: 'growth', label: 'Growth Signals', icon: Zap },
        { id: 'evidence', label: 'Evidence', icon: FileText },
        { id: 'predictions', label: 'Predictions', icon: Target },
    ]

    return (
      <div className="min-h-screen bg-offwhite font-sans">
        <header className="bg-navy border-b border-navy-light sticky top-0 z-10 px-8 py-4 flex justify-between items-center shadow-md">
            <div>
                <h1 className="text-2xl font-serif text-white tracking-tight">Market Intelligence</h1>
                <p className="text-slate-300 text-sm mt-1">
                    Analysis ID: {analysisId} <span className="mx-2">•</span> Status: <span className={status === "PARTIAL" ? "text-amber-400 font-semibold" : status === "FAILED" ? "text-red-500 font-semibold" : "text-tealAccent-light font-semibold"}>{status}</span>
                </p>
            </div>
            <Button variant="outline" className="text-navy bg-white hover:bg-slate-100 border-transparent" onClick={() => { setAnalysisId(null); setIsAnalyzing(false); setStatus(null); }}>New Analysis</Button>
        </header>

        <div className="flex max-w-[1400px] mx-auto pt-8">
            <aside className="w-64 pr-8">
                <nav className="space-y-2">
                    {tabs.map(t => {
                        const Icon = t.icon
                        return (
                            <button 
                                key={t.id}
                                onClick={() => setActiveTab(t.id as TabType)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-all ${
                                    activeTab === t.id 
                                        ? "bg-white text-navy shadow-sm border border-lightBorder" 
                                        : "text-slateGray hover:bg-white/60 hover:text-navy border border-transparent"
                                }`}
                            >
                                <Icon className={`w-5 h-5 ${activeTab === t.id ? "text-tealAccent" : "text-slate-400"}`} />
                                {t.label}
                            </button>
                        )
                    })}
                </nav>
            </aside>
            <main className="flex-1 pb-12">
                {status === 'FAILED' && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
                    <h3 className="text-lg font-semibold mb-1">Analysis Failed</h3>
                    <p className="text-sm">The pipeline encountered a fatal error. Some partial results might be visible below.</p>
                  </div>
                )}
                {activeTab === 'overview' && <OverviewTab overview={overviewData} primaryCompanyId={overviewData?.companies[0]?.id} />}
                {activeTab === 'competitors' && <CompetitorsTab data={competitorsData} />}
                {activeTab === 'seo' && <SeoPerformanceTab seo={seoData} performance={performanceData} companies={overviewData?.companies} />}
                {activeTab === 'trends' && <TrendsTab trends={trendsData} />}
                {activeTab === 'growth' && <GrowthSignalsTab signals={growthData} companies={overviewData?.companies} />}
                {activeTab === 'evidence' && <EvidenceTab evidence={evidenceData} companies={overviewData?.companies} />}
                {activeTab === 'predictions' && <PredictionsTab predictions={predictionsData} />}
            </main>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-offwhite font-sans flex flex-col items-center py-16 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-4xl space-y-10">
        <div className="text-center">
          <h1 className="text-5xl font-serif text-navy tracking-tight mb-4">Market Intelligence</h1>
          <p className="text-xl text-slateGray font-light">AI-Powered Competitive Intelligence & Strategy</p>
        </div>

        <Card className="shadow-sm border border-lightBorder bg-white rounded-xl overflow-hidden">
          <form onSubmit={handleSubmit}>
            <CardHeader className="bg-navy text-white pb-6 pt-8 px-8">
              <CardTitle className="text-2xl font-serif font-normal">Define Market</CardTitle>
              <CardDescription className="text-slate-300 text-base mt-2">Enter your organization and the competitors you want to analyze.</CardDescription>
            </CardHeader>
            <CardContent className="pt-10 px-8 pb-8 space-y-10">
              
              <div className="space-y-5">
                <h3 className="text-sm font-semibold tracking-widest text-slateGray uppercase flex items-center gap-2 border-b border-lightBorder pb-3">
                  <Globe className="w-4 h-4 text-tealAccent" />
                  Your Organization
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-navy">Company Name</label>
                    <Input 
                      placeholder="e.g. Notion" 
                      value={company.name}
                      onChange={(e) => setCompany({ ...company, name: e.target.value })}
                      required 
                      disabled={isAnalyzing}
                      className="bg-offwhite border-lightBorder focus:border-tealAccent h-11"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-navy">Primary Website</label>
                    <Input 
                      placeholder="e.g. notion.so" 
                      value={company.website}
                      onChange={(e) => setCompany({ ...company, website: e.target.value })}
                      required 
                      disabled={isAnalyzing}
                      className="bg-offwhite border-lightBorder focus:border-tealAccent h-11"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-5">
                <div className="flex justify-between items-center border-b border-lightBorder pb-3">
                  <h3 className="text-sm font-semibold tracking-widest text-slateGray uppercase flex items-center gap-2">
                    <Activity className="w-4 h-4 text-tealAccent" />
                    Competitors
                  </h3>
                </div>
                
                <div className="space-y-4">
                  {competitors.map((comp, idx) => (
                    <div key={idx} className="flex gap-4 items-start p-4 bg-offwhite/50 border border-lightBorder rounded-lg">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-grow">
                        <div className="space-y-2">
                          <label className="text-xs font-medium text-slateGray uppercase">Competitor Name</label>
                          <Input 
                            placeholder="e.g. Asana, Trello" 
                            value={comp.name}
                            onChange={(e) => handleCompetitorChange(idx, 'name', e.target.value)}
                            required 
                            disabled={isAnalyzing}
                            className="bg-white border-lightBorder focus:border-tealAccent h-10"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-xs font-medium text-slateGray uppercase">Website</label>
                          <Input 
                            placeholder="e.g. asana.com" 
                            value={comp.website}
                            onChange={(e) => handleCompetitorChange(idx, 'website', e.target.value)}
                            required 
                            disabled={isAnalyzing}
                            className="bg-white border-lightBorder focus:border-tealAccent h-10"
                          />
                        </div>
                      </div>
                      {competitors.length > 1 && (
                        <Button 
                          type="button" 
                          variant="ghost" 
                          size="icon" 
                          onClick={() => handleRemoveCompetitor(idx)}
                          disabled={isAnalyzing}
                          className="text-slate-400 hover:text-red-600 hover:bg-red-50 mt-6"
                        >
                          <X className="w-5 h-5" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
                
                {competitors.length < 10 && (
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={handleAddCompetitor} 
                    disabled={isAnalyzing}
                    className="w-full border-dashed border-2 border-lightBorder text-slateGray hover:text-navy hover:bg-offwhite h-12"
                  >
                    <Plus className="w-4 h-4 mr-2 text-tealAccent" />
                    Add Competitor
                  </Button>
                )}
              </div>

            </CardContent>
            <div className="p-8 bg-offwhite border-t border-lightBorder flex justify-end">
              <Button 
                type="submit" 
                size="lg" 
                disabled={isAnalyzing}
                className="bg-tealAccent hover:bg-tealAccent-light text-white font-medium px-10 h-12 rounded-md shadow-sm transition-colors"
              >
                {isAnalyzing ? "Starting Analysis..." : "Analyze Market"}
              </Button>
            </div>
          </form>
        </Card>

        {isAnalyzing && status !== "COMPLETED" && status !== "PARTIAL" && (
          <Card className="border border-lightBorder bg-white shadow-sm overflow-hidden">
             <CardContent className="p-10 flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 border-4 border-slate-200 border-t-tealAccent rounded-full animate-spin mb-6"></div>
                <h3 className="text-2xl font-serif text-navy mb-2">Analyzing Market Dynamics</h3>
                <p className="text-slateGray max-w-md mx-auto leading-relaxed">
                  The intelligence engine is securely collecting documents, extracting NLP patterns, assessing web performance, and synthesizing AI insights.
                </p>
                {status && (
                  <div className="mt-6 px-4 py-2 bg-offwhite rounded-md border border-lightBorder">
                    <p className="text-sm font-medium text-navy tracking-wide uppercase">
                      Status: <span className="text-tealAccent ml-2">{status}</span>
                    </p>
                  </div>
                )}
             </CardContent>
          </Card>
        )}

      </div>
    </div>
  )
}
