import React from 'react'
import { Server, AlertOctagon, Download, TrendingUp, ShieldAlert } from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'

export default function Dashboard({ stats, API_BASE }) {
  const score = stats.overall_compliance_score || 0
  
  // Circunference equations for circular progress wheel
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  // Dynamic alert styles matching metric status
  const getGlowColor = () => {
    if (score < 40) return 'text-cyber-rose stroke-cyber-rose'
    if (score < 80) return 'text-cyber-accent stroke-cyber-accent'
    return 'text-cyber-emerald stroke-cyber-emerald'
  }

  // Format historical datestamps nicely
  const chartData = stats.history.map(h => ({
    name: new Date(h.recorded_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    score: h.score
  }))

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Overview stats panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        
        {/* Compliance Gauge Circular Card */}
        <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-between glass-glow-primary border-indigo-900 border-opacity-30 relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-cyber-primary opacity-10 rounded-full blur-xl"></div>
          <h3 class="text-sm font-semibold tracking-wide text-gray-400 uppercase self-start">Compliance Score</h3>
          
          <div className="relative flex items-center justify-center my-4">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle cx="64" cy="64" r={radius} stroke="rgba(255,255,255,0.05)" strokeWidth="8" fill="transparent" />
              <circle 
                cx="64" 
                cy="64" 
                r={radius} 
                strokeWidth="8" 
                fill="transparent" 
                className={`${getGlowColor()} transition-all duration-1000 ease-out`}
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-2xl font-extrabold font-outfit">{score.toFixed(1)}%</span>
              <span className="text-[9px] text-gray-400 uppercase tracking-widest font-outfit">NIS2 Article 21</span>
            </div>
          </div>
          <p className="text-xs text-center text-gray-400">Average based on 10 legal requirements</p>
        </div>

        {/* Scanned Assets Card */}
        <div className="glass-card rounded-2xl p-6 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-cyber-secondary opacity-10 rounded-full blur-xl"></div>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold tracking-wide text-gray-400 uppercase">Scanned Assets</h3>
            <div className="p-2 rounded-lg bg-cyan-950 bg-opacity-40 border border-cyan-800 text-cyber-secondary">
              <Server className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-4xl font-extrabold font-outfit">{stats.scanned_assets_count}</span>
            <p className="text-xs text-gray-400 mt-1">Discovered systems in scope subnet</p>
          </div>
          <div className="mt-4 text-xs flex justify-between text-gray-400 border-t border-gray-800 pt-3">
            <span>NIS2 In Scope:</span>
            <span className="font-semibold text-cyber-secondary">{stats.in_scope_assets_count}</span>
          </div>
        </div>

        {/* Critical compliance gaps */}
        <div className="glass-card rounded-2xl p-6 flex flex-col justify-between glass-glow-rose border-rose-950 border-opacity-30 relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-cyber-rose opacity-10 rounded-full blur-xl"></div>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold tracking-wide text-gray-400 uppercase">Critical Gaps</h3>
            <div className="p-2 rounded-lg bg-rose-950 bg-opacity-40 border border-rose-800 text-cyber-rose">
              <AlertOctagon className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-4xl font-extrabold font-outfit text-cyber-rose">{stats.critical_gaps_count}</span>
            <p className="text-xs text-gray-400 mt-1">Non-Compliant legal components</p>
          </div>
          <div className="mt-4 text-xs flex justify-between text-gray-400 border-t border-gray-800 pt-3">
            <span>Action Required:</span>
            <span className="font-semibold text-cyber-rose">IMMEDIATE</span>
          </div>
        </div>

        {/* Regulator Audit PDF Compiler */}
        <div className="glass-card rounded-2xl p-6 bg-gradient-to-br from-cyber-900 via-cyber-800 to-indigo-950 border-cyber-primary border-opacity-40 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-cyber-accent opacity-10 rounded-full blur-xl"></div>
          <div>
            <div class="flex items-center justify-between">
              <h3 className="text-sm font-semibold tracking-wide text-cyber-accent uppercase font-outfit">Swedish Audit PDF</h3>
              <span className="text-[10px] bg-amber-950 border border-amber-800 text-cyber-accent px-2 py-0.5 rounded">NCSC-SE</span>
            </div>
            <p className="text-xs text-gray-300 mt-3">
              Compile compliance gap reports ready to directly hand to Swedish authorities (MSB) or enterprise cybersecurity auditors.
            </p>
          </div>
          <a 
            href={`${API_BASE}/report/pdf`} 
            download 
            className="mt-4 w-full bg-gradient-to-r from-cyber-primary to-indigo-600 hover:from-cyber-secondary hover:to-cyber-primary text-white text-center py-2.5 rounded-xl font-medium text-sm transition-all duration-300 shadow-lg flex items-center justify-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Generate Audit Report</span>
          </a>
        </div>
      </div>

      {/* Historical charts & perimeters threats layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Compliance trend area chart using Recharts */}
        <div className="glass-card rounded-2xl p-6 lg:col-span-2">
          <h3 className="text-lg font-bold font-outfit mb-4 text-gray-100 flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-cyber-primary" />
            <span>NIS2 Compliance Trend History</span>
          </h3>
          <div className="h-64">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}
                    labelStyle={{ color: '#f3f4f6', fontWeight: 'bold' }}
                  />
                  <Area type="monotone" dataKey="score" stroke="#4f46e5" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-gray-500">
                Trigger a scan to construct compliance records trendline.
              </div>
            )}
          </div>
        </div>

        {/* Critical network assets threat-vectors bar */}
        <div className="glass-card rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold font-outfit mb-4 text-gray-100 flex items-center space-x-2">
              <ShieldAlert className="w-5 h-5 text-cyber-rose" />
              <span>Critical Threat Vector Assets</span>
            </h3>
            
            <div className="space-y-4">
              {stats.critical_assets && stats.critical_assets.length > 0 ? (
                stats.critical_assets.map(asset => (
                  <div key={asset.id} className="flex items-center justify-between bg-gray-900 border border-red-950 bg-opacity-40 p-3.5 rounded-xl">
                    <div className="flex items-center space-x-3">
                      <span className="h-2.5 w-2.5 rounded-full bg-cyber-rose animate-pulse"></span>
                      <div>
                        <p className="text-sm font-bold font-outfit text-gray-100">{asset.ip}</p>
                        <p className="text-[10px] text-gray-400">{asset.hostname || 'Embedded Client'}</p>
                      </div>
                    </div>
                    <span className="text-[10px] bg-red-950 border border-red-800 text-cyber-rose px-2.5 py-0.5 rounded font-medium">
                      {asset.scope_sector || 'OT Core'}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-10 text-xs">
                  No critical vulnerability assets identified. Run scanner.
                </div>
              )}
            </div>
          </div>
          <p className="text-[10px] text-gray-500 italic mt-4 text-center">
            Continuously updated based on local ARP & Shodan threat models.
          </p>
        </div>
      </div>
    </div>
  )
}
