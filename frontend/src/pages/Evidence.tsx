import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { documentsApi } from '@/api/documents'
import { useWorkspaceEntities } from '@/hooks/useWorkspaceEntities'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, ExternalLink, FileText } from 'lucide-react'

export default function Evidence() {
  const { allEntities, selectedCompanyId: workspaceCompanyId } = useWorkspaceEntities()
  const [localCompanyId, setLocalCompanyId] = useState<number | undefined>(workspaceCompanyId || undefined)
  const [page, setPage] = useState(1)

  useEffect(() => {
    if (workspaceCompanyId && !localCompanyId) {
      setLocalCompanyId(workspaceCompanyId)
    }
  }, [workspaceCompanyId, localCompanyId])

  const { data: documentsPage, isLoading: isDocumentsLoading } = useQuery({
    queryKey: ['documents', localCompanyId, page],
    queryFn: () => documentsApi.getDocuments({ 
      company_id: localCompanyId, 
      page, 
      page_size: 15 
    })
  })

  const safeEntities = Array.isArray(allEntities) ? allEntities : []
  const safeItems = Array.isArray(documentsPage?.items) ? documentsPage.items : []
  const totalItems = documentsPage?.total || 0
  const totalPages = documentsPage?.total_pages || 1

  const getCompanyName = (companyId: number) => {
    const comp = safeEntities.find(c => c && c.id === companyId)
    return comp ? comp.name : 'Unknown Entity'
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif tracking-tight">Evidence Explorer</h2>
          <p className="text-muted-foreground mt-1">
            Raw intelligence artifacts, scraped articles, and SEC filings.
          </p>
        </div>
      </div>

      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="font-serif text-xl flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Intelligence Corpus
              </CardTitle>
              <CardDescription>
                {documentsPage ? `Showing ${safeItems.length} of ${totalItems} documents` : "Loading corpus..."}
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="relative w-full md:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  type="search" 
                  placeholder="Search documents (TBD)..." 
                  className="pl-8 bg-secondary border-none"
                />
              </div>
              <Select 
                value={localCompanyId ? localCompanyId.toString() : "all"} 
                onValueChange={(val) => {
                  setLocalCompanyId(val === "all" ? undefined : Number(val))
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Workspace Entities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Workspace Entities</SelectItem>
                  {safeEntities.map(c => {
                    if (!c || !c.id) return null;
                    return <SelectItem key={c.id} value={c.id.toString()}>{c.name || 'Unknown Entity'}</SelectItem>
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isDocumentsLoading ? (
            <div className="space-y-3 mt-4">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-16 w-full rounded-md" />
              ))}
            </div>
          ) : safeItems.length > 0 ? (
            <div className="mt-4 space-y-3">
              {safeItems.map(doc => {
                if (!doc || !doc.id) return null;
                return (
                  <div key={doc.id} className="group flex items-center justify-between rounded-lg border p-3 hover:bg-secondary/30 transition-colors">
                    <div className="flex flex-col gap-1 overflow-hidden pr-4">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-[10px] uppercase font-medium">
                          {doc.document_type || 'DOCUMENT'}
                        </Badge>
                        <span className="text-xs font-medium text-primary/80">
                          {getCompanyName(doc.company_id)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {doc.published_at ? new Date(doc.published_at).toLocaleDateString() : 'Unknown Date'}
                        </span>
                      </div>
                      <a 
                        href={doc.url || '#'} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="font-medium text-sm truncate hover:underline text-primary"
                        onClick={(e) => !doc.url && e.preventDefault()}
                      >
                        {doc.title || "Untitled Document"}
                      </a>
                    </div>
                    <div className="flex-shrink-0">
                      <Button variant="ghost" size="icon" asChild disabled={!doc.url}>
                        <a href={doc.url || '#'} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                        </a>
                      </Button>
                    </div>
                  </div>
                )
              })}
              
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 pt-4">
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                  >
                    Previous
                  </Button>
                  <span className="text-xs text-muted-foreground">
                    Page {page} of {totalPages}
                  </span>
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  >
                    Next
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed mt-4">
              <p className="text-sm text-muted-foreground">No evidence documents found.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
