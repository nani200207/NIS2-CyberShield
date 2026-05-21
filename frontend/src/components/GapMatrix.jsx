import React, { useState } from 'react'
import { ShieldAlert, ShieldCheck, Check, Save } from 'lucide-react'

export default function GapMatrix({ gaps, API_BASE, fetchAllData }) {
  const [editedGaps, setEditedGaps] = useState({})
  const [savingState, setSavingState] = useState({})

  // Handle local state updates for inputs
  const handleScoreChange = (articleId, val) => {
    const score = parseInt(val)
    let status = 'Non-Compliant'
    if (score >= 80) status = 'Compliant'
    else if (score >= 40) status = 'Partial'

    setEditedGaps(prev => ({
      ...prev,
      [articleId]: {
        ...prev[articleId],
        score,
        status
      }
    }))
  }

  const handleCommentsChange = (articleId, comments) => {
    setEditedGaps(prev => ({
      ...prev,
      [articleId]: {
        ...prev[articleId],
        comments
      }
    }))
  }

  const handleStepsChange = (articleId, steps) => {
    setEditedGaps(prev => ({
      ...prev,
      [articleId]: {
        ...prev[articleId],
        remediation_steps: steps
      }
    }))
  }

  // Save specific modified card gap to database
  const saveGap = async (articleId, originalGap) => {
    const edits = editedGaps[articleId] || {}
    const updatePayload = {
      score: edits.score !== undefined ? edits.score : originalGap.score,
      comments: edits.comments !== undefined ? edits.comments : originalGap.comments,
      remediation_steps: edits.remediation_steps !== undefined ? edits.remediation_steps : originalGap.remediation_steps
    }

    setSavingState(prev => ({ ...prev, [articleId]: 'saving' }))
    try {
      const res = await fetch(`${API_BASE}/gap-analysis/${encodeURIComponent(articleId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatePayload)
      })
      if (res.ok) {
        setSavingState(prev => ({ ...prev, [articleId]: 'saved' }))
        fetchAllData()
        setTimeout(() => {
          setSavingState(prev => ({ ...prev, [articleId]: null }))
        }, 2000)
      } else {
        setSavingState(prev => ({ ...prev, [articleId]: 'error' }))
      }
    } catch (err) {
      console.error(err)
      setSavingState(prev => ({ ...prev, [articleId]: 'error' }))
    }
  }

  const getStatusBadge = (status) => {
    if (status === 'Compliant') {
      return (
        <span className="flex items-center space-x-1 text-cyber-emerald bg-emerald-950 bg-opacity-40 border border-emerald-900 px-2.5 py-0.5 rounded-full text-[10px] font-semibold font-outfit uppercase">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Compliant</span>
        </span>
      )
    }
    if (status === 'Partial') {
      return (
        <span className="flex items-center space-x-1 text-cyber-accent bg-amber-950 bg-opacity-40 border border-amber-900 px-2.5 py-0.5 rounded-full text-[10px] font-semibold font-outfit uppercase">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Partial</span>
        </span>
      )
    }
    return (
      <span className="flex items-center space-x-1 text-cyber-rose bg-red-950 bg-opacity-40 border border-red-900 px-2.5 py-0.5 rounded-full text-[10px] font-semibold font-outfit uppercase">
        <ShieldAlert className="w-3.5 h-3.5" />
        <span>Non-Compliant</span>
      </span>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-2xl font-extrabold font-outfit text-gray-100 flex items-center space-x-2">
          <span>NIS2 Article 21 Compliance Gap Matrix</span>
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Perform digital maturity alignment audits against Swedish NCSC-SE requirements. Adjust sliders and enter auditor annotations to update database scores.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {gaps && gaps.map(gap => {
          const currentEdit = editedGaps[gap.article_id] || {}
          const score = currentEdit.score !== undefined ? currentEdit.score : gap.score
          const status = currentEdit.status !== undefined ? currentEdit.status : gap.status
          const comments = currentEdit.comments !== undefined ? currentEdit.comments : (gap.comments || '')
          const steps = currentEdit.remediation_steps !== undefined ? currentEdit.remediation_steps : (gap.remediation_steps || '')
          const saving = savingState[gap.article_id]

          return (
            <div 
              key={gap.article_id} 
              className={`glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4 transition-all duration-300 border-opacity-35 hover:scale-[1.01] ${
                status === 'Compliant' ? 'border-emerald-950 focus-within:border-cyber-emerald' :
                status === 'Partial' ? 'border-amber-950 focus-within:border-cyber-accent' :
                'border-red-950 focus-within:border-cyber-rose'
              }`}
            >
              
              {/* Gap Header Info */}
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-extrabold font-mono bg-cyber-primary bg-opacity-20 border border-cyber-primary border-opacity-40 text-cyan-300 px-2 py-0.5 rounded">
                      {gap.article_id}
                    </span>
                    <span className="text-xs font-semibold text-gray-400 font-outfit uppercase tracking-wider">
                      {gap.category}
                    </span>
                  </div>
                  {getStatusBadge(status)}
                </div>

                <h3 className="text-base font-extrabold font-outfit text-gray-100 mt-3">{gap.control_name}</h3>
                <p className="text-xs text-gray-400 mt-1 leading-5">{gap.description}</p>
              </div>

              {/* Slider Controller */}
              <div className="bg-gray-900 bg-opacity-40 p-4 rounded-xl space-y-2 border border-gray-800 border-opacity-50">
                <div className="flex justify-between items-center text-xs font-medium">
                  <span className="text-gray-400">Security Control Maturity:</span>
                  <span className={`font-bold ${
                    status === 'Compliant' ? 'text-cyber-emerald' :
                    status === 'Partial' ? 'text-cyber-accent' : 'text-cyber-rose'
                  }`}>{score}%</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={score} 
                  onChange={(e) => handleScoreChange(gap.article_id, e.target.value)}
                  className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-cyber-primary"
                />
              </div>

              {/* Textarea Comments Form */}
              <div className="space-y-3.5">
                <div className="space-y-1">
                  <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Auditor Comments</label>
                  <textarea 
                    rows="2" 
                    value={comments} 
                    onChange={(e) => handleCommentsChange(gap.article_id, e.target.value)}
                    className="w-full bg-gray-900 bg-opacity-80 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all resize-none leading-5"
                    placeholder="Enter manual audit findings or compliance exemptions..."
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Priority Remediation Steps</label>
                  <textarea 
                    rows="2" 
                    value={steps} 
                    onChange={(e) => handleStepsChange(gap.article_id, e.target.value)}
                    className="w-full bg-gray-900 bg-opacity-80 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyber-primary transition-all resize-none leading-5"
                    placeholder="Describe step-by-step remediation instructions..."
                  />
                </div>
              </div>

              {/* Commit Notes Trigger */}
              <button 
                onClick={() => saveGap(gap.article_id, gap)}
                disabled={saving === 'saving'}
                className={`w-full py-2.5 rounded-xl text-xs font-semibold tracking-wider transition-all duration-300 shadow-md flex items-center justify-center space-x-2 ${
                  saving === 'saved' ? 'bg-cyber-emerald text-white' :
                  saving === 'error' ? 'bg-cyber-rose text-white' :
                  'bg-gray-800 hover:bg-cyber-primary text-gray-200 hover:text-white border border-gray-700 hover:border-transparent'
                }`}
              >
                {saving === 'saving' ? (
                  <>
                    <span className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></span>
                    <span>Saving score changes...</span>
                  </>
                ) : saving === 'saved' ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Audit Notes Successfully Saved!</span>
                  </>
                ) : saving === 'error' ? (
                  <span>Failed to save. Try again.</span>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Control Notes</span>
                  </>
                )}
              </button>

            </div>
          )
        })}
      </div>
    </div>
  )
}
