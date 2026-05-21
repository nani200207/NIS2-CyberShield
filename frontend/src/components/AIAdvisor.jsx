import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, AlertCircle } from 'lucide-react'

export default function AIAdvisor({ API_BASE }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `### 🛡️ NIS2 CyberShield AI Compliance Advisor Active
I am your enterprise **NCSC-SE / MSB regulatory alignment assistant**. I have read-only access to your active network discovery logs and compliance gap scorecards.

#### Ask me questions like:
*   *How do I draft a 24-hour Early Warning Incident report for certified NCSC-SE reporting under Article 21.2b?*
*   *What are the configuration steps to remediate our Article 21.2h encryption gap?*
*   *Draft a supply-chain vendor cybersecurity assessment policy under Article 21.2d.*`
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  // Auto-scroll chat history
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  // Process natural language prompts
  const sendMessage = async (textToSend) => {
    const queryText = textToSend || input
    if (!queryText.trim()) return

    // Add user message
    const userMsg = { role: 'user', content: queryText }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/advisor/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText })
      })

      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', content: data.advice }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ **Error:** Backend AI Agent encountered an execution timeout. Verify settings.' }])
      }
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ **Error:** Failed to connect to server gateway. Check connections.' }])
    } finally {
      setLoading(false)
    }
  }

  // Pre-populate quick templates
  const applyTemplate = (prompt) => {
    setInput(prompt)
  }

  // Simple custom markdown renderer supporting paragraphs, bullets, bold text, and code blocks
  const renderContent = (text) => {
    return text.split('\n').map((line, idx) => {
      // Headers
      if (line.startsWith('### ')) {
        return <h3 key={idx} className="text-lg font-bold font-outfit text-white mt-4 mb-2">{line.replace('### ', '')}</h3>
      }
      if (line.startsWith('#### ')) {
        return <h4 key={idx} className="text-sm font-bold font-outfit text-cyber-secondary mt-3 mb-1.5 uppercase tracking-wider">{line.replace('#### ', '')}</h4>
      }
      if (line.startsWith('##### ')) {
        return <h5 key={idx} className="text-xs font-bold text-gray-200 mt-2 mb-1 uppercase">{line.replace('##### ', '')}</h5>
      }
      
      // Lists
      if (line.startsWith('* ') || line.startsWith('- ')) {
        const itemText = line.substring(2)
        return (
          <ul key={idx} className="list-disc list-inside pl-4 text-xs text-gray-300 my-1 leading-5">
            <li>{parseInlineStyles(itemText)}</li>
          </ul>
        )
      }

      // Insecure Code Block markup
      if (line.startsWith('```')) {
        return null // We don't render backticks
      }

      // Paragraph fallback
      if (line.trim() === '') return <div key={idx} className="h-2"></div>
      return <p key={idx} className="text-xs text-gray-300 leading-6">{parseInlineStyles(line)}</p>
    })
  }

  // Helper parser for **bold** and `code` blocks
  const parseInlineStyles = (txt) => {
    const parts = []
    let current = txt
    
    // Simple regex parser
    const boldCodeRegex = /(\*\*.*?\*\*|`.*?`)/g
    const splits = current.split(boldCodeRegex)
    
    return splits.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="bg-black bg-opacity-60 px-1.5 py-0.5 rounded font-mono text-[10px] text-cyber-secondary">{part.slice(1, -1)}</code>
      }
      return part
    })
  }

  return (
    <div className="space-y-6 animate-fadeIn h-[calc(100vh-180px)] flex flex-col justify-between">
      
      {/* Top context bar */}
      <div className="glass-card rounded-xl p-3 flex items-center justify-between border-gray-800 text-xs text-gray-400">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-cyber-secondary animate-pulse" />
          <span>Active RAG Pipeline: Injects active gap scorecards & Shodan vectors.</span>
        </div>
        <span className="text-[10px] bg-indigo-950 border border-indigo-900 text-cyan-300 px-2 py-0.5 rounded font-mono uppercase">
          Claude / Gemini Native
        </span>
      </div>

      {/* Main chat log window */}
      <div className="flex-grow bg-cyber-900 bg-opacity-40 border border-gray-800 rounded-2xl p-6 overflow-y-auto terminal-scroll space-y-6">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex space-x-4 max-w-4xl ${m.role === 'user' ? 'ml-auto flex-row-reverse space-x-reverse' : ''}`}>
            
            {/* Avatar icon */}
            <div className={`h-8 w-8 rounded-xl flex items-center justify-center border ${
              m.role === 'user' 
                ? 'bg-gray-800 border-gray-700 text-gray-200' 
                : 'bg-indigo-950 border-indigo-900 text-cyber-secondary'
            }`}>
              {m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Chat bubble body */}
            <div className={`p-5 rounded-2xl border text-sm space-y-2 leading-relaxed ${
              m.role === 'user'
                ? 'bg-cyber-primary bg-opacity-20 border-cyber-primary border-opacity-30 rounded-tr-none text-gray-100'
                : 'bg-gray-900 bg-opacity-40 border-gray-800 rounded-tl-none text-gray-300'
            }`}>
              {renderContent(m.content)}
            </div>

          </div>
        ))}

        {loading && (
          <div className="flex space-x-4 max-w-lg">
            <div className="h-8 w-8 rounded-xl bg-indigo-950 border border-indigo-900 flex items-center justify-center text-cyber-secondary">
              <Bot className="w-4 h-4 animate-bounce" />
            </div>
            <div className="bg-gray-900 bg-opacity-40 border border-gray-800 p-5 rounded-2xl rounded-tl-none text-xs text-gray-500 italic flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-cyber-secondary animate-ping"></span>
              <span>AI Advisor is scanning compliance registers and drafting remediation roadmaps...</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Speed Query Bullet Templates */}
      <div className="flex flex-wrap gap-2 py-2">
        <button 
          onClick={() => applyTemplate('Draft a 24-hour Early Warning Incident Notification report for NCSC-SE / MSB under Article 21.2b.')}
          className="bg-gray-900 border border-gray-800 hover:border-cyber-primary text-gray-400 hover:text-white px-3 py-1.5 rounded-xl text-[10px] font-semibold transition-all"
        >
          📝 Incident Reporting early warning
        </button>
        <button 
          onClick={() => applyTemplate('How do I fix our Article 21.2h Cryptography and HTTPS encryption gap? Provide terminal commands.')}
          className="bg-gray-900 border border-gray-800 hover:border-cyber-primary text-gray-400 hover:text-white px-3 py-1.5 rounded-xl text-[10px] font-semibold transition-all"
        >
          🔒 Remediate Crypto Sliders
        </button>
        <button 
          onClick={() => applyTemplate('Draft a supply-chain vendor risk security questionnaire for Article 21.2d.')}
          className="bg-gray-900 border border-gray-800 hover:border-cyber-primary text-gray-400 hover:text-white px-3 py-1.5 rounded-xl text-[10px] font-semibold transition-all"
        >
          💼 Third-Party Risk audits
        </button>
      </div>

      {/* Chat Text Input Form */}
      <div className="flex items-center space-x-3 mt-2">
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="e.g., How do I remediate my Art 21.2j MFA non-compliance for Swedish MSB?"
          className="flex-grow bg-gray-900 border border-gray-800 rounded-xl px-5 py-3 text-xs text-gray-200 focus:outline-none focus:border-cyber-secondary transition-all"
          disabled={loading}
        />
        <button 
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          className="bg-cyber-primary hover:bg-indigo-600 disabled:opacity-40 text-white p-3 rounded-xl transition-all duration-300 shadow-md flex items-center justify-center cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

    </div>
  )
}
