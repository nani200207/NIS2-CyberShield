import React, { useState, useEffect } from 'react'
import { 
  LayoutDashboard, 
  Scan, 
  ShieldCheck, 
  MessageSquare, 
  Settings as SettingsIcon,
  Shield,
  Download
} from 'lucide-react'

// Sub-components
import Dashboard from './components/Dashboard'
import AssetScanner from './components/AssetScanner'
import GapMatrix from './components/GapMatrix'
import AIAdvisor from './components/AIAdvisor'
import Settings from './components/Settings'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
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
    scan_target: '192.168.1.0/24',
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

  // Fetch core analytics
  const fetchAllData = async () => {
    try {
      // 1. Stats
      const resStats = await fetch(`${API_BASE}/dashboard/stats`)
      if (resStats.ok) {
        const data = await resStats.json()
        setStats(data)
      }
      
      // 2. Assets
      const resAssets = await fetch(`${API_BASE}/assets`)
      if (resAssets.ok) {
        const data = await resAssets.json()
        setAssets(data)
      }
      
      // 3. Gaps
      const resGaps = await fetch(`${API_BASE}/gap-analysis`)
      if (resGaps.ok) {
        const data = await resGaps.json()
        setGaps(data)
      }
      
      // 4. Config
      const resConfig = await fetch(`${API_BASE}/settings`)
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
      const resLogs = await fetch(`${API_BASE}/scan/logs`)
      if (resLogs.ok) {
        const data = await resLogs.json()
        setLogs(data)
      }
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchAllData()
    fetchLogs()
    
    // Background polling loop
    const interval = setInterval(() => {
      fetchAllData()
      fetchLogs()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen flex flex-col bg-cyber-950 text-gray-100 relative">
      {/* Dynamic Background Neon Glow */}
      <div className="absolute top-0 left-0 w-full h-[500px] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(79,70,229,0.18),rgba(255,255,255,0))] -z-10 pointer-events-none"></div>

      {/* Navigation Header */}
      <header className="border-b border-gray-800 bg-cyber-900 bg-opacity-70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
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
          
          {/* Tab Button Selector */}
          <div className="flex items-center space-x-2 bg-gray-900 border border-gray-800 rounded-lg p-1">
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
              <span>Asset Scanner</span>
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

      {/* Main Contents Panel */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard stats={stats} API_BASE={API_BASE} />
        )}
        
        {activeTab === 'scanner' && (
          <AssetScanner 
            assets={assets} 
            logs={logs} 
            config={config} 
            API_BASE={API_BASE} 
            fetchLogs={fetchLogs} 
            fetchAllData={fetchAllData} 
          />
        )}
        
        {activeTab === 'gap' && (
          <GapMatrix 
            gaps={gaps} 
            API_BASE={API_BASE} 
            fetchAllData={fetchAllData} 
          />
        )}
        
        {activeTab === 'ai' && (
          <AIAdvisor API_BASE={API_BASE} />
        )}
        
        {activeTab === 'settings' && (
          <Settings 
            config={config} 
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
