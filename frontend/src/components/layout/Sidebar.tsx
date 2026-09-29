import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"
import { 
  BarChart3, 
  Building2, 
  
  
  MessageSquareText,
  LineChart,
  BrainCircuit,
 
  Database,
  Activity,
  FileText
} from "lucide-react"

const navGroups = [
  {
    title: 'OVERVIEW',
    items: [
      {
        title: 'Executive Overview',
        path: '/overview',
        icon: <BarChart3 className="h-4 w-4" />,
      }
    ]
  },
  {
    title: 'INTELLIGENCE',
    items: [
      {
        title: 'Competitors',
        path: '/competitors',
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        title: 'Market Trends',
        path: '/trends',
        icon: <LineChart className="h-4 w-4" />,
      },
      {
        title: 'Sentiment & Topics',
        path: '/sentiment-topics',
        icon: <MessageSquareText className="h-4 w-4" />,
      },
      {
        title: 'Predictions',
        path: '/predictions',
        icon: <LineChart className="h-4 w-4" />,
      },
    ],
  },
  {
    title: 'INSIGHTS',
    items: [
      {
        title: 'AI Intelligence',
        path: '/intelligence',
        icon: <BrainCircuit className="h-4 w-4" />,
      },
      {
        title: 'Evidence Explorer',
        path: '/evidence',
        icon: <FileText className="h-4 w-4" />,
      }
    ]
  },
  {
    title: 'DATA',
    items: [
      {
        title: 'Data Sources',
        path: '/sources',
        icon: <Database className="h-4 w-4" />,
      },
      {
        title: 'Collection Runs',
        path: '/collection',
        icon: <Activity className="h-4 w-4" />,
      },
    ],
  },
]

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-10 hidden w-64 flex-col border-r bg-card sm:flex">
      <div className="flex flex-col h-16 shrink-0 justify-center px-6 border-b">
        <span className="font-serif text-lg font-semibold tracking-tight text-primary">MARKET INTELLIGENCE</span>
        <span className="text-[10px] uppercase font-medium tracking-widest text-muted-foreground mt-0.5">AI-POWERED COMPETITIVE INTELLIGENCE</span>
      </div>
      <nav className="flex-1 overflow-auto py-4">
        {navGroups.map((group, i) => (
          <div key={i} className="mb-6 px-4">
            {group.title && (
              <h4 className="mb-2 px-3 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                {group.title}
              </h4>
            )}
            <ul className="grid gap-1">
              {group.items.map((item, j) => (
                <li key={j}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary/50 hover:text-foreground",
                        isActive ? "bg-secondary text-primary" : "text-muted-foreground"
                      )
                    }
                  >
                    {item.icon}
                    {item.title}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  )
}
