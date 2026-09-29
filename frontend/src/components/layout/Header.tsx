import { useNavigate } from "react-router-dom"
import { useWorkspace } from "@/context/ConfigurationContext"
import { Button } from "@/components/ui/button"
import { CalendarIcon, Bell, Settings } from "lucide-react"

export default function Header() {
  const navigate = useNavigate()
  const { selectedCompanyName } = useWorkspace()

  const handleSwitchWorkspace = () => {
    navigate('/setup')
  }

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-background px-6">
      <div className="flex flex-1 items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex flex-col">
            <h1 className="text-xl font-serif font-semibold tracking-tight text-primary">
              {selectedCompanyName || "Intelligence Profile"}
            </h1>
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-widest">
              Competitive Intelligence
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" onClick={handleSwitchWorkspace}>
            Reconfigure Profile
          </Button>
          <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground border rounded-md px-3 py-1.5 bg-secondary/30">
            <CalendarIcon className="h-4 w-4" />
            <span>Last 30 Days</span>
          </div>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-primary">
            <Bell className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-primary">
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  )
}
