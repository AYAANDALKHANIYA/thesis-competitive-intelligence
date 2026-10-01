import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '@/api/client'
import { useConfiguration } from '@/context/ConfigurationContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Building2, Globe, Network, ArrowRight, AlertCircle, Loader2 } from 'lucide-react'

// Helper to normalize domains purely for frontend validation
function normalizeDomain(url: string): string | null {
  try {
    let rawUrl = url.trim().toLowerCase()
    if (!/^https?:\/\//i.test(rawUrl)) {
      rawUrl = 'http://' + rawUrl
    }
    const urlObj = new URL(rawUrl)
    let hostname = urlObj.hostname
    if (hostname.startsWith('www.')) {
      hostname = hostname.substring(4)
    }
    return hostname
  } catch (e) {
    return null
  }
}

export default function Setup() {
  const navigate = useNavigate()
  const { refetch } = useConfiguration()

  // Setup Form State
  const [companyName, setCompanyName] = useState('')
  const [website, setWebsite] = useState('')
  const [industry, setIndustry] = useState('')
  
  // Custom Competitors List State
  const [competitors, setCompetitors] = useState<{ localId: number, name: string, website: string }[]>([])
  const [newCompetitorName, setNewCompetitorName] = useState('')
  const [newCompetitorWebsite, setNewCompetitorWebsite] = useState('')
  const [competitorError, setCompetitorError] = useState<string | null>(null)
  
  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const handleAddCompetitor = () => {
    setCompetitorError(null)
    const name = newCompetitorName.trim()
    const url = newCompetitorWebsite.trim()

    if (!name || !url) {
      setCompetitorError("Both name and website are required.")
      return
    }

    const normalizedUrl = normalizeDomain(url)
    if (!normalizedUrl) {
      setCompetitorError("Please enter a valid URL.")
      return
    }

    // Ensure it's not the primary company
    const primaryNormalized = normalizeDomain(website)
    if (primaryNormalized && normalizedUrl === primaryNormalized) {
      setCompetitorError("You cannot add your own organization as a competitor.")
      return
    }

    // Ensure no duplicates in local list
    const isDuplicate = competitors.some(c => normalizeDomain(c.website) === normalizedUrl)
    if (isDuplicate) {
      setCompetitorError("This competitor is already in your list.")
      return
    }

    setCompetitors(prev => [...prev, { localId: Date.now(), name, website: url }])
    setNewCompetitorName('')
    setNewCompetitorWebsite('')
  }

  const handleRemoveCompetitor = (localId: number) => {
    setCompetitors(prev => prev.filter(c => c.localId !== localId))
  }

  const isFormValid = companyName.trim() && website.trim() && normalizeDomain(website) && competitors.length > 0

  const handleStartIntelligence = async () => {
    if (!isFormValid) return
    setIsSubmitting(true)
    setSubmitError(null)

    try {
      await apiClient.post('/api/v1/system/setup', {
        company_name: companyName.trim(),
        company_domain: normalizeDomain(website) || website.trim(),
        industry: industry.trim() || undefined,
        competitors: competitors.map(c => ({
          name: c.name,
          domain: normalizeDomain(c.website) || c.website
        }))
      })

      // Refetch the global configuration context so the app re-evaluates routing
      await refetch()
      
      // Navigate to overview
      navigate('/overview')
    } catch (error: any) {
      console.error("Setup error:", error)
      setSubmitError(error?.response?.data?.detail || "An unexpected error occurred while saving your configuration. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-secondary/30 flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-4xl">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-serif tracking-tight text-primary mb-3">
            Build your competitive intelligence profile
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto">
            Configure your organization and define your market. The engine will automatically collect and analyze intelligence on a daily schedule.
          </p>
        </div>

        <Card className="shadow-lg border-t-4 border-t-primary relative">
          <CardHeader>
            <CardTitle className="font-serif text-2xl">Configuration</CardTitle>
            <CardDescription>Setup is a one-time process.</CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-8">
            {submitError && (
              <div className="p-4 bg-destructive/10 text-destructive border-l-4 border-destructive rounded-r-md flex items-start gap-3">
                <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <p className="text-sm font-medium">{submitError}</p>
              </div>
            )}
            
            {/* Section 1: Your Company */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b pb-2">
                <Building2 className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-sm tracking-widest uppercase">1. Your Organization</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="companyName">Organization Name *</Label>
                  <Input 
                    id="companyName" 
                    placeholder="e.g. Notion" 
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    disabled={isSubmitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="industry">Industry</Label>
                  <Input 
                    id="industry" 
                    placeholder="e.g. Project management software for small teams" 
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    disabled={isSubmitting}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="website">Primary Website *</Label>
                  <Input 
                    id="website" 
                    placeholder="https://www.notion.so" 
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    disabled={isSubmitting}
                  />
                </div>
              </div>
            </div>

            {/* Section 2: Competitors */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b pb-2">
                <Network className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-sm tracking-widest uppercase">2. Competitor Tracking</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Add the companies you want to monitor against your organization.
              </p>

              {/* Display Added Competitors */}
              {competitors.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-6 border border-dashed rounded-lg bg-secondary/20">
                  <p className="text-sm font-medium text-muted-foreground mb-1">No competitors added yet.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Competitors to Monitor</h4>
                  {competitors.map((comp) => (
                    <div key={comp.localId} className="flex items-center justify-between p-3 border rounded-md bg-background">
                      <div>
                        <p className="font-medium text-sm text-foreground">{comp.name}</p>
                        <p className="text-xs text-muted-foreground">{comp.website}</p>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleRemoveCompetitor(comp.localId)}
                        disabled={isSubmitting}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add Competitor Form */}
              <div className="mt-4 p-4 border rounded-lg bg-secondary/10 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="compName">Competitor Name *</Label>
                    <Input 
                      id="compName" 
                      placeholder="e.g. Asana, Trello" 
                      value={newCompetitorName}
                      onChange={(e) => setNewCompetitorName(e.target.value)}
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="compWeb">Competitor Website *</Label>
                    <Input 
                      id="compWeb" 
                      placeholder="https://www.asana.com" 
                      value={newCompetitorWebsite}
                      onChange={(e) => setNewCompetitorWebsite(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddCompetitor();
                        }
                      }}
                      disabled={isSubmitting}
                    />
                  </div>
                </div>
                {competitorError && (
                  <p className="text-sm text-destructive">{competitorError}</p>
                )}
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={handleAddCompetitor}
                  disabled={isSubmitting}
                  className="w-full sm:w-auto"
                >
                  + Add Competitor
                </Button>
              </div>
            </div>

            {/* Section 3: Data Sources */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b pb-2">
                <Globe className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-sm tracking-widest uppercase">3. Automated Collection Sources</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">Company Websites</Badge>
                <Badge variant="secondary">Public News & PR</Badge>
              </div>
            </div>

          </CardContent>
          <CardFooter className="bg-secondary/50 p-6 flex justify-end rounded-b-lg border-t">
            <Button 
              size="lg" 
              className="font-semibold px-8" 
              onClick={handleStartIntelligence}
              disabled={!isFormValid || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Configuring Intelligence Profile...
                </>
              ) : (
                <>
                  Start Intelligence
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
