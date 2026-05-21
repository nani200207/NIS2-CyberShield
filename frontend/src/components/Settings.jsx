import React, { useState } from 'react'
import { Settings as SettingsIcon, Save, Key, Bell, ShieldCheck, Check } from 'lucide-react'

export default function Settings({ config, API_BASE, fetchAllData }) {
  const [geminiKey, setGeminiKey] = useState(config.gemini_key || '')
  const [shodanKey, setShodanKey] = useState(config.shodan_key || '')
  const [slackWebhook, setSlackWebhook] = useState(config.slack_webhook || '')
  const [scanTarget, setScanTarget] = useState(config.scan_target || '192.168.1.0/24')
  const [scanFrequency, setScanFrequency] = useState(config.scan_frequency || 60)
  const [monitoringActive, setMonitoringActive] = useState(config.monitoring_active)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Send settings update to backend
  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gemini_key: geminiKey,
          shodan_key: shodanKey,
          slack_webhook: slackWebhook,
          scan_target: scanTarget,
          scan_frequency: parseInt(scanFrequency),
          monitoring_active: monitoringActive
        })
      })

      if (res.ok) {
        setSaved(true)
        fetchAllData()
        setTimeout(() => setSaved(false), 2500)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      
      <div>
        <h2 className="text-2xl font-extrabold font-outfit text-gray-100 flex items-center space-x-2">
          <SettingsIcon className="w-6 h-6 text-cyber-primary" />
          <span>Platform Configurations & Integrations</span>
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Store global credentials, configure active monitoring channels, and tune background subnet sweep frequencies.
        </p>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-6 border-indigo-950 border-opacity-35">
        
        {/* Section 1: AI & Threat API Keys */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold font-outfit text-cyber-secondary flex items-center space-x-2 uppercase tracking-wider">
            <Key className="w-4 h-4" />
            <span>Third-Party API Integrations</span>
          </h3>
          <hr className="border-gray-800 border-opacity-40" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Google Gemini API Key</label>
              <input 
                type="password" 
                value={geminiKey} 
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="AI reasoning authorization key..."
                className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all font-mono"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Shodan Intelligence API Key</label>
              <input 
                type="password" 
                value={shodanKey} 
                onChange={(e) => setShodanKey(e.target.value)}
                placeholder="External OSINT threat scanner key..."
                className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all font-mono"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Alert webhooks */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold font-outfit text-cyber-secondary flex items-center space-x-2 uppercase tracking-wider">
            <Bell className="w-4 h-4" />
            <span>Incident Alert Webhooks</span>
          </h3>
          <hr className="border-gray-800 border-opacity-40" />

          <div className="space-y-1">
            <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Slack Notification Webhook URL</label>
            <input 
              type="text" 
              value={slackWebhook} 
              onChange={(e) => setSlackWebhook(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all font-mono"
            />
          </div>
        </div>

        {/* Section 3: Scanning Scheduling defaults */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold font-outfit text-cyber-secondary flex items-center space-x-2 uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            <span>Active Continuous Scanning</span>
          </h3>
          <hr className="border-gray-800 border-opacity-40" />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Default Sweep Target</label>
              <input 
                type="text" 
                value={scanTarget} 
                onChange={(e) => setScanTarget(e.target.value)}
                placeholder="192.168.1.0/24"
                className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all font-mono"
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Cron Audit Interval</label>
              <select 
                value={scanFrequency} 
                onChange={(e) => setScanFrequency(e.target.value)}
                className="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all"
              >
                <option value="5">Every 5 minutes (Dev Test)</option>
                <option value="30">Every 30 minutes</option>
                <option value="60">Every hour</option>
                <option value="1440">Daily</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-gray-900 bg-opacity-40 p-4 rounded-xl border border-gray-800">
            <input 
              type="checkbox" 
              id="monitorActive" 
              checked={monitoringActive} 
              onChange={(e) => setMonitoringActive(e.target.checked)}
              className="w-4 h-4 rounded text-cyber-primary bg-gray-800 border-gray-700 focus:ring-0 cursor-pointer"
            />
            <div className="cursor-pointer select-none">
              <label htmlFor="monitorActive" className="text-xs text-gray-300 font-bold cursor-pointer">
                Enable Active Daemon Monitor Agent
              </label>
              <p className="text-[10px] text-gray-500 mt-0.5">
                Automatically schedules background subnet sweeps and logs Compliance history trends.
              </p>
            </div>
          </div>
        </div>

        {/* Action Save Button */}
        <button 
          onClick={handleSave}
          disabled={saving}
          className={`w-full py-3 rounded-xl text-xs font-semibold tracking-wider transition-all duration-300 shadow-md flex items-center justify-center space-x-2 ${
            saved ? 'bg-cyber-emerald text-white' : 'bg-cyber-primary hover:bg-indigo-600 text-white'
          }`}
        >
          {saving ? (
            <>
              <span className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></span>
              <span>Saving Configurations...</span>
            </>
          ) : saved ? (
            <>
              <Check className="w-4 h-4" />
              <span>Configurations Successfully Saved!</span>
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5" />
              <span>Save Configurations</span>
            </>
          )}
        </button>

      </div>
    </div>
  )
}
