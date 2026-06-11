import React, { useState, useEffect, useRef } from 'react'
import { Scan, Terminal, Trash2, ServerCrash, Shield, AlertTriangle, Cpu, Radio } from 'lucide-react'

export default function AssetScanner({ assets, logs: initialLogs, config, currentOrgId, API_BASE, fetchAllData }) {
  const [subnet, setSubnet] = useState(config.scan_target || '10.100.4.0/24')
  const [realScan, setRealScan] = useState(false)
  const [scanning, setScanning] = useState(false)
  
  // Manage logs dynamically via WebSockets
  const [logs, setLogs] = useState([])
  const terminalEndRef = useRef(null)

  // Establish live WebSocket connection
  useEffect(() => {
    // Determine WS address
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.origin.includes('5173') 
      ? 'localhost:8000' 
      : window.location.host
      
    const wsUrl = `${wsProto}//${wsHost}/api/v1/scan/ws-logs?org_id=${currentOrgId}`
    console.log("[WebSocket] Connecting to scanner channel:", wsUrl)
    
    const socket = new WebSocket(wsUrl)
    
    // Reset local logs for the selected organization
    setLogs([])

    socket.onmessage = (event) => {
      try {
        const logData = JSON.parse(event.data)
        setLogs(prev => {
          // Prevent duplicates
          if (prev.find(l => l.id === logData.id)) return prev
          return [...prev, logData]
        })
      } catch (err) {
        console.error("Failed to parse socket packet:", err)
      }
    }

    socket.onerror = (err) => {
      console.error("[WebSocket] Scanning logs stream error:", err)
    }

    return () => {
      socket.close()
    }
  }, [currentOrgId])

  // Autoscroll the terminal scrollbar as logs arrive
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  // Trigger network scanner
  const runScan = async () => {
    setScanning(true)
    try {
      const res = await fetch(`${API_BASE}/scan?target=${encodeURIComponent(subnet)}&real_scan=${realScan}&org_id=${currentOrgId}`, {
        method: 'POST'
      })
      if (res.ok) {
        // Leave visual sweep loader active for 4.5 seconds to watch console traces
        setTimeout(() => {
          setScanning(false)
          fetchAllData()
        }, 4500)
      } else {
        setScanning(false)
      }
    } catch (err) {
      console.error(err)
      setScanning(false)
    }
  }

  // Clear database scan logs
  const clearLogs = async () => {
    if (!confirm("Are you sure you want to clear the terminal logs?")) return
    try {
      await fetch(`${API_BASE}/scan/logs/clear?org_id=${currentOrgId}`, { method: 'POST' })
      setLogs([])
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Subnet Input & Console Trigger */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Scanner Panel Control Options */}
        <div className="glass-card rounded-2xl p-6 h-fit space-y-4 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyber-secondary to-indigo-600"></div>
          
          <h3 className="text-lg font-bold font-outfit text-gray-100 flex items-center space-x-2">
            <Scan className="w-5 h-5 text-cyber-secondary animate-pulse" />
            <span>IT Sweep Parameters</span>
          </h3>
          
          <div className="space-y-1">
            <label className="text-xs text-gray-400 font-medium font-outfit">Subnet / Scope CIDR</label>
            <input 
              type="text" 
              value={subnet} 
              onChange={(e) => setSubnet(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-cyber-secondary transition-all font-mono"
            />
          </div>

          <div className="flex items-center space-x-3 bg-gray-900 bg-opacity-40 p-3.5 rounded-xl border border-gray-805">
            <input 
              type="checkbox" 
              id="realScan" 
              checked={realScan} 
              onChange={(e) => setRealScan(e.target.checked)}
              className="w-4 h-4 rounded text-cyber-primary bg-gray-800 border-gray-700 focus:ring-0 cursor-pointer"
            />
            <label htmlFor="realScan" className="text-xs text-gray-300 font-medium cursor-pointer select-none">
              Execute direct RAW sockets scan
            </label>
          </div>

          <button 
            onClick={runScan}
            disabled={scanning}
            className="w-full bg-gradient-to-r from-cyber-secondary to-indigo-600 hover:opacity-90 text-white py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {scanning ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                <span>Active discovery running...</span>
              </>
            ) : (
              <>
                <Radio className="w-4 h-4 text-white" />
                <span>Execute Subnet Discovery</span>
              </>
            )}
          </button>
        </div>

        {/* Real-time Terminal Log Reader */}
        <div className="glass-card rounded-2xl p-6 lg:col-span-2 flex flex-col justify-between h-[300px] border border-gray-800">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-3">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-cyber-emerald" />
              <span className="text-xs font-semibold tracking-wider font-outfit uppercase text-cyber-emerald">Scanner Stream Output (WebSocket Connection)</span>
            </div>
            <button 
              onClick={clearLogs} 
              className="text-gray-500 hover:text-cyber-rose transition-all flex items-center space-x-1"
              title="Wipe Logs History"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="text-[10px] font-outfit">Wipe Logs</span>
            </button>
          </div>

          {/* Glowing Green Console */}
          <div className="flex-grow bg-black bg-opacity-95 p-4 rounded-xl border border-gray-900 font-mono text-[11px] text-green-400 overflow-y-auto terminal-scroll space-y-1.5 h-full relative">
            <div className="absolute top-2 right-4 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-cyber-emerald animate-ping"></span>
              <span className="text-[9px] text-gray-500 uppercase tracking-widest font-outfit">Live Channel</span>
            </div>
            
            {logs && logs.length > 0 ? (
              logs.map(l => (
                <div key={l.id} className="leading-5">
                  <span className="text-gray-600">[{new Date(l.timestamp).toLocaleTimeString()}]</span>{' '}
                  <span className={
                    l.level === 'SUCCESS' ? 'text-cyber-emerald font-semibold' :
                    l.level === 'WARNING' ? 'text-cyber-rose font-bold' :
                    l.level === 'ERROR' ? 'text-red-500 font-bold' : 'text-green-400'
                  }>
                    {l.message}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-gray-600 italic h-full flex flex-col items-center justify-center text-center">
                <Cpu className="w-6 h-6 text-gray-700 mb-2" />
                <span>Console connected. Trigger a subnet scan above to watch live port sweep traces.</span>
              </div>
            )}
            <div ref={terminalEndRef} />
          </div>
        </div>
      </div>

      {/* Discovered Perimeter Assets Table */}
      <div className="glass-card rounded-2xl p-6 overflow-hidden">
        <h3 className="text-lg font-bold font-outfit mb-4 text-gray-100 flex items-center space-x-2">
          <ServerCrash className="w-5 h-5 text-cyber-rose" />
          <span>Discovered Subnet Perimeter Inventories</span>
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 uppercase tracking-wider font-semibold">
                <th className="py-3.5 px-4">Network Node (IP)</th>
                <th className="py-3.5 px-4">Device Hostname / OS</th>
                <th className="py-3.5 px-4">NIS2 Sector Weight</th>
                <th className="py-3.5 px-4">Threat Rating</th>
                <th className="py-3.5 px-4">Active Ports</th>
                <th className="py-3.5 px-4">NIS2 Scope Status</th>
                <th className="py-3.5 px-4 text-right">Discovered CVE Exposures</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800 divide-opacity-40">
              {assets && assets.length > 0 ? (
                assets.map(asset => {
                  let shodanDetail = null
                  if (asset.shodan_data) {
                    try {
                      shodanDetail = JSON.parse(asset.shodan_data)
                    } catch(e) {}
                  }

                  const riskScore = asset.dynamic_risk_score || 1.0
                  const riskColorClass = riskScore >= 12.0 
                    ? 'text-cyber-rose bg-red-950 bg-opacity-20 border-red-900' 
                    : riskScore >= 6.0 
                      ? 'text-cyber-accent bg-amber-950 bg-opacity-20 border-amber-900' 
                      : 'text-cyber-emerald bg-emerald-950 bg-opacity-20 border-emerald-900'

                  return (
                    <tr key={asset.id} className="hover:bg-gray-900 hover:bg-opacity-20 transition-all">
                      <td className="py-4 px-4 font-bold font-mono text-gray-100">{asset.ip}</td>
                      <td className="py-4 px-4 text-gray-300 font-medium">
                        <span className="block font-outfit">{asset.hostname || 'Unknown Client'}</span>
                        <span className="text-[10px] text-gray-500 block mt-0.5">{asset.os || 'Embedded / Linux Node'}</span>
                      </td>
                      <td className="py-4 px-4 text-gray-400 font-outfit">
                        {asset.scope_sector ? (
                          <span className="text-gray-300 font-medium">{asset.scope_sector}</span>
                        ) : (
                          <span className="text-gray-600">Outside Perimeter</span>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <span className={`px-2.5 py-1 rounded-xl text-[10px] font-bold border ${riskColorClass}`}>
                          {riskScore.toFixed(1)} Risk Index
                        </span>
                      </td>
                      <td className="py-4 px-4 font-mono text-cyber-secondary font-semibold">{asset.ports || 'None'}</td>
                      <td className="py-4 px-4">
                        {asset.in_scope ? (
                          <span className="flex items-center space-x-1.5 text-cyber-emerald font-semibold font-outfit">
                            <Shield className="w-3.5 h-3.5" />
                            <span>In Scope</span>
                          </span>
                        ) : (
                          <span className="text-gray-500 font-outfit">Out of Scope</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-right">
                        {shodanDetail && shodanDetail.vulns_detail && shodanDetail.vulns_detail.length > 0 ? (
                          <div className="flex flex-wrap justify-end gap-1.5 max-w-[280px] ml-auto">
                            {shodanDetail.vulns_detail.map(v => (
                              <span 
                                key={v.cve_id} 
                                className="inline-flex items-center space-x-1 bg-red-950 bg-opacity-40 border border-red-900 border-opacity-40 text-cyber-rose px-2 py-0.5 rounded-lg text-[9px] font-bold tracking-wide font-mono"
                                title={`CVSS: ${v.cvss} - Severity: ${v.severity}`}
                              >
                                <span>{v.cve_id}</span>
                                <span className="opacity-60 bg-red-900 text-white rounded px-1 ml-1 text-[8px]">{v.cvss}</span>
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-gray-500 italic text-[10px]">Clean perimeter</span>
                        )}
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan="7" className="text-center text-gray-500 py-12 italic text-xs">
                    No active assets discovered on subnet target. Proactively run the scanner.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
