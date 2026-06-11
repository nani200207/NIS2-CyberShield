import React, { useState, useEffect } from 'react'
import { 
  LayoutDashboard, 
  Scan, 
  ShieldCheck, 
  MessageSquare, 
  Settings as SettingsIcon,
  Shield,
  Download,
  Building,
  Plus,
  ClipboardList
} from 'lucide-react'

// Sub-components
import Dashboard from './components/Dashboard'
import AssetScanner from './components/AssetScanner'
import GapMatrix from './components/GapMatrix'
import AIAdvisor from './components/AIAdvisor'
import Settings from './components/Settings'
import RemediationBoard from './components/RemediationBoard'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  
  // Multi-tenant Org States
  const [organizations, setOrganizations] = useState([])
  const [currentOrgId, setCurrentOrgId] = useState(1)
  const [showAddOrg, setShowAddOrg] = useState(false)
  const [newOrgName, setNewOrgName] = useState('')

  const [stats, setStats] = useState({
    overall_compliance_score: 0.0,
    scanned_assets_count: 0,
    in_scope_assets_count: 0,
    critical_gaps_count: 0,
    gap_breakdown: {},
    history: [],
    critical_assets: []
  })
  
  const [assets, setAssets] = useState([])
  const [gaps, setGaps] = useState([])
  const [logs, setLogs] = useState([])
  
  const [config, setConfig] = useState({
    scan_target: '10.100.4.0/24',
    scan_frequency: 60,
    shodan_key: '',
    gemini_key: '',
    slack_webhook: '',
    monitoring_active: true
  })
  
  // API URL prefix loaded dynamically or defaulting to backend service
  const API_BASE = window.location.origin.includes('5173') 
    ? 'http://localhost:8000/api/v1' 
    : '/api/v1'

  // Fetch registered organizations
  const fetchOrganizations = async () => {
    try {
      const res = await fetch(`${API_BASE}/organizations`)
      if (res.ok) {
        const data = await res.json()
        setOrganizations(data)
        if (data.length > 0 && !data.find(o => o.id === currentOrgId)) {
          setCurrentOrgId(data[0].id)
        }
      }
    } catch (err) {
      console.error("Failed to load organizations:", err)
    }
  }

  // Create a new organization tenant
  const handleCreateOrg = async (e) => {
    e.preventDefault()
    if (!newOrgName.trim()) return
    try {
      const res = await fetch(`${API_BASE}/organizations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newOrgName })
      })
      if (res.ok) {
        const data = await res.json()
        setNewOrgName('')
        setShowAddOrg(false)
        await fetchOrganizations()
        setCurrentOrgId(data.id)
        setActiveTab('dashboard')
      }
    } catch (err) {
      console.error(err)
    }
  }

  // Fetch core analytics scoped by active organization ID
  const fetchAllData = async () => {
    try {
      // 1. Stats
      const resStats = await fetch(`${API_BASE}/dashboard/stats?org_id=${currentOrgId}`)
      if (resStats.ok) {
        const data = await resStats.json()
        setStats(data)
      }
      
      // 2. Assets
      const resAssets = await fetch(`${API_BASE}/assets?org_id=${currentOrgId}`)
      if (resAssets.ok) {
        const data = await resAssets.json()
        setAssets(data)
      }
      
      // 3. Gaps
      const resGaps = await fetch(`${API_BASE}/gap-analysis?org_id=${currentOrgId}`)
      if (resGaps.ok) {
        const data = await resGaps.json()
        setGaps(data)
      }
      
      // 4. Config
      const resConfig = await fetch(`${API_BASE}/settings?org_id=${currentOrgId}`)
      if (resConfig.ok) {
        const data = await resConfig.json()
        setConfig(data)
      }
    } catch (err) {
      console.error("API Connection error:", err)
    }
  }

  // Fetch scan logs (polled faster during scanning)
  const fetchLogs = async () => {
    try {
      const resLogs = await fetch(`${API_BASE}/scan/logs?org_id=${currentOrgId}`)
      if (resLogs.ok) {
        const data = await resLogs.json()
        setLogs(data)
      }
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchOrganizations()
  }, [])

  useEffect(() => {
    fetchAllData()
    fetchLogs()
    
    // Background polling loop for active charts updates
    const interval = setInterval(() => {
      fetchAllData()
    }, 8000)
    
    return () => clearInterval(interval)
  }, [currentOrgId])

  return (
    <div className="min-h-screen flex flex-col bg-cyber-950 text-gray-100 relative">
      {/* Dynamic Background Neon Glow */}
      <div className="absolute top-0 left-0 w-full h-[500px] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(79,70,229,0.18),rgba(255,255,255,0))] -z-10 pointer-events-none"></div>

      {/* Navigation Header */}
      <header className="border-b border-gray-800 bg-cyber-900 bg-opacity-70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between flex-wrap sm:flex-nowrap">
          <div className="flex items-center space-x-3 py-2 sm:py-0">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyber-primary to-cyber-secondary flex items-center justify-center text-white shadow-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold font-outfit tracking-tight flex items-center bg-gradient-to-r from-white via-gray-100 to-cyber-secondary bg-clip-text text-transparent">
                NIS2 CYBERSHIELD
              </h1>
              <p className="text-xs text-gray-400">Compliance Scanner & AI Remediation Advisor</p>
            </div>
          </div>
          
          {/* SaaS Organization Selector dropdown */}
          <div className="flex items-center space-x-2 py-2 sm:py-0">
            <div className="flex items-center space-x-1 bg-gray-950 border border-gray-800 rounded-xl px-3 py-1.5 text-xs text-gray-300">
              <Building className="w-3.5 h-3.5 text-cyber-primary" />
              <select
                value={currentOrgId}
                onChange={e => setCurrentOrgId(Number(e.target.value))}
                className="bg-transparent text-gray-200 border-none focus:outline-none cursor-pointer pr-1"
              >
                {organizations.map(o => (
                  <option key={o.id} value={o.id} className="bg-gray-950 text-gray-200">
                    {o.name}
                  </option>
                ))}
              </select>
            </div>
            
            <button
              onClick={() => setShowAddOrg(true)}
              className="p-2 border border-gray-800 hover:border-cyber-primary rounded-xl text-gray-400 hover:text-white transition-all bg-gray-950"
              title="Add Organization SaaS Tenant"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {/* Tab Button Selector */}
          <div className="flex items-center space-x-1.5 bg-gray-900 border border-gray-850 rounded-lg p-1">
            <button 
              onClick={() => setActiveTab('dashboard')} 
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'dashboard' ? 'bg-cyber-primary text-white shadow-md' : 'text-gray-400 hover:text-white'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Dashboard</span>
            </button>
            <button 
              onClick={() => setActiveTab('scanner')} 
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'scanner' ? 'bg-cyber-primary text-white shadow-md' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Scan className="w-4 h-4" />
              <span>Scanner</span>
            </button>
            <button 
              onClick={() => setActiveTab('gap')} 
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'gap' ? 'bg-cyber-primary text-white shadow-md' : 'text-gray-400 hover:text-white'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Gap Matrix</span>
            </button>
            <button 
              onClick={() => setActiveTab('remediation')} 
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'remediation' ? 'bg-cyber-primary text-white shadow-md' : 'text-gray-400 hover:text-white'
              }`}
            >
              <ClipboardList className="w-4 h-4" />
              <span>Remediation</span>
            </button>
            <button 
              onClick={() => setActiveTab('ai')} 
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'ai' ? 'bg-cyber-primary text-white shadow-md' : 'text-gray-400 hover:text-white'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>AI Advisor</span>
            </button>
            <button 
              onClick={() => setActiveTab('settings')} 
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'settings' ? 'bg-cyber-primary text-white shadow-md' : 'text-gray-400 hover:text-white'
              }`}
            >
              <SettingsIcon className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </header>

      {/* Inline Create Organization Modal dialog */}
      {showAddOrg && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-[999] backdrop-blur-sm animate-fadeIn">
          <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl max-w-sm w-full shadow-2xl relative">
            <h3 className="text-lg font-bold font-outfit text-white mb-2 flex items-center space-x-2">
              <Building className="w-5 h-5 text-cyber-primary" />
              <span>Add SaaS Organization</span>
            </h3>
            <p className="text-xs text-gray-400 mb-4">Onboard a dedicated cyber asset scope mapping environment.</p>
            
            <form onSubmit={handleCreateOrg} className="space-y-4">
              <input
                type="text"
                placeholder="e.g. Västerås Hospital Group"
                value={newOrgName}
                onChange={e => setNewOrgName(e.target.value)}
                className="w-full bg-gray-950 border border-gray-850 rounded-xl px-3.5 py-2.5 text-sm text-gray-100 focus:outline-none focus:border-cyber-primary font-outfit"
                required
                autoFocus
              />
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddOrg(false)}
                  className="px-4 py-2 border border-gray-805 rounded-xl hover:bg-gray-800 text-sm text-gray-400 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cyber-primary hover:bg-opacity-90 text-white rounded-xl text-sm font-semibold shadow-md"
                >
                  Onboard Tenant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Contents Panels */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard stats={stats} currentOrgId={currentOrgId} API_BASE={API_BASE} />
        )}
        
        {activeTab === 'scanner' && (
          <AssetScanner 
            assets={assets} 
            logs={logs} 
            config={config} 
            currentOrgId={currentOrgId}
            API_BASE={API_BASE} 
            fetchLogs={fetchLogs} 
            fetchAllData={fetchAllData} 
          />
        )}
        
        {activeTab === 'gap' && (
          <GapMatrix 
            gaps={gaps} 
            currentOrgId={currentOrgId}
            API_BASE={API_BASE} 
            fetchAllData={fetchAllData} 
          />
        )}

        {activeTab === 'remediation' && (
          <RemediationBoard 
            currentOrgId={currentOrgId} 
            gaps={gaps}
            API_BASE={API_BASE}
          />
        )}
        
        {activeTab === 'ai' && (
          <AIAdvisor currentOrgId={currentOrgId} API_BASE={API_BASE} />
        )}
        
        {activeTab === 'settings' && (
          <Settings 
            config={config} 
            currentOrgId={currentOrgId}
            API_BASE={API_BASE} 
            fetchAllData={fetchAllData} 
          />
        )}
      </main>

      {/* Footer Block */}
      <footer className="border-t border-gray-800 bg-cyber-950 py-6 text-center text-xs text-gray-500 mt-8">
        <p>© 2026 NIS2 CyberShield Compliance Platform. Strictly restricted to Authorized Important & Essential Entity Operators.</p>
      </footer>
    </div>
  )
}
