import React, { useState, useEffect, useRef } from 'react'
import { Scan, Terminal, Trash2, ServerCrash, Shield, AlertTriangle } from 'lucide-react'

export default function AssetScanner({ assets, logs, config, API_BASE, fetchLogs, fetchAllData }) {
  const [subnet, setSubnet] = useState(config.scan_target || '192.168.1.0/24')
  const [realScan, setRealScan] = useState(false)
  const [scanning, setScanning] = useState(false)
  const terminalEndRef = useRef(null)

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
      const res = await fetch(`${API_BASE}/scan?target=${encodeURIComponent(subnet)}&real_scan=${realScan}`, {
        method: 'POST'
      })
      if (res.ok) {
        // Poll for 5 seconds for visual feedback
        let count = 0
        const interval = setInterval(() => {
          fetchLogs()
          fetchAllData()
          count++
          if (count > 6) {
            clearInterval(interval)
            setScanning(false)
          }
        }, 1000)
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
    try {
      await fetch(`${API_BASE}/scan/logs/clear`, { method: 'POST' })
      fetchLogs()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* Subnet Input & Console Trigger */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Scanner Panel Control Options */}
        <div className="glass-card rounded-2xl p-6 h-fit space-y-4">
          <h3 className="text-lg font-bold font-outfit text-gray-100 flex items-center space-x-2">
            <Scan className="w-5 h-5 text-cyber-secondary" />
            <span>Subnet Scan Parameters</span>
          </h3>
          
          <div className="space-y-1">
            <label className="text-xs text-gray-400 font-medium">Target IP Subnet</label>
            <input 
              type="text" 
              value={subnet} 
              onChange={(e) => setSubnet(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-cyber-secondary transition-all"
            />
          </div>

          <div className="flex items-center space-x-3 bg-gray-900 bg-opacity-40 p-3.5 rounded-xl border border-gray-800">
            <input 
              type="checkbox" 
              id="realScan" 
              checked={realScan} 
              onChange={(e) => setRealScan(e.target.checked)}
              className="w-4 h-4 rounded text-cyber-primary bg-gray-800 border-gray-700 focus:ring-0 cursor-pointer"
            />
            <label htmlFor="realScan" className="text-xs text-gray-300 font-medium cursor-pointer select-none">
              Execute low-level RAW sockets scan
            </label>
          </div>

          <button 
            onClick={runScan}
            disabled={scanning}
            className="w-full bg-gradient-to-r from-cyber-secondary to-indigo-600 hover:from-cyan-400 hover:to-cyber-primary text-white py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {scanning ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                <span>Sweeping Subnet Perimeters...</span>
              </>
            ) : (
              <>
                <Scan className="w-4 h-4" />
                <span>Execute Subnet Scan</span>
              </>
            )}
          </button>
        </div>

        {/* Real-time Terminal Log Reader */}
        <div className="glass-card rounded-2xl p-6 lg:col-span-2 flex flex-col justify-between h-[300px]">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-3">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-cyber-emerald" />
              <span className="text-xs font-semibold tracking-wider font-outfit uppercase text-cyber-emerald">Scanner Daemon Console Output</span>
            </div>
            <button 
              onClick={clearLogs} 
              className="text-gray-500 hover:text-cyber-rose transition-all flex items-center space-x-1"
              title="Wipe Logs History"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="text-[10px]">Wipe logs</span>
            </button>
          </div>

          {/* Glowing Green Console */}
          <div className="flex-grow bg-black bg-opacity-95 p-4 rounded-xl border border-gray-800 font-mono text-[11px] text-green-400 overflow-y-auto terminal-scroll space-y-1.5 h-full">
            {logs && logs.length > 0 ? (
              logs.slice().reverse().map(l => (
                <div key={l.id} className="leading-5">
                  <span className="text-gray-500">[{new Date(l.timestamp).toLocaleTimeString()}]</span>{' '}
                  <span className={
                    l.log_line.includes('VULNERABILITY') || l.log_line.includes('SHODAN ALERT') ? 'text-cyber-rose font-bold' : 
                    l.log_line.includes('IN SCOPE') ? 'text-cyber-emerald' : 
                    l.log_line.includes('CRITICAL') ? 'text-cyber-accent font-semibold' : 'text-green-400'
                  }>
                    {l.log_line}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-gray-600 italic h-full flex items-center justify-center">
                Console idle. Initiate a sweep to watch cyber discovery operations trace.
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
                <th className="py-3.5 px-4">Device Hostname</th>
                <th className="py-3.5 px-4">NIS2 Scope Sector</th>
                <th className="py-3.5 px-4">Criticality</th>
                <th className="py-3.5 px-4">Active Ports</th>
                <th className="py-3.5 px-4">NIS2 Status</th>
                <th className="py-3.5 px-4 text-right">Threat Footprint</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800 divide-opacity-40">
              {assets && assets.length > 0 ? (
                assets.map(asset => (
                  <tr key={asset.id} className="hover:bg-gray-900 hover:bg-opacity-20 transition-all">
                    <td className="py-4 px-4 font-bold font-mono text-gray-100">{asset.ip}</td>
                    <td className="py-4 px-4 text-gray-300 font-medium">{asset.hostname || 'None (IP Client)'}</td>
                    <td className="py-4 px-4 text-gray-400">{asset.scope_sector || 'Outside Perimeter'}</td>
                    <td className="py-4 px-4">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold border ${
                        asset.criticality === 'Critical' ? 'bg-red-950 border-red-800 text-cyber-rose' :
                        asset.criticality === 'High' ? 'bg-amber-950 border-amber-800 text-cyber-accent' :
                        'bg-gray-800 border-gray-700 text-gray-400'
                      }`}>
                        {asset.criticality}
                      </span>
                    </td>
                    <td className="py-4 px-4 font-mono text-cyber-secondary font-semibold">{asset.ports || 'None'}</td>
                    <td className="py-4 px-4">
                      {asset.in_scope ? (
                        <span className="flex items-center space-x-1.5 text-cyber-emerald font-semibold">
                          <Shield className="w-3.5 h-3.5" />
                          <span>In Scope</span>
                        </span>
                      ) : (
                        <span className="text-gray-500">Out of Scope</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      {asset.shodan_data ? (
                        <span className="inline-flex items-center space-x-1 bg-red-950 bg-opacity-60 border border-red-900 text-cyber-rose px-2.5 py-1 rounded-xl text-[10px] font-bold uppercase animate-pulse">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Shodan Vulnerabilities Exposed</span>
                        </span>
                      ) : (
                        <span className="text-gray-500 italic">None exposed</span>
                      )}
                    </td>
                  </tr>
                ))
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
