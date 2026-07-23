import React, { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  Bot, 
  User, 
  Terminal, 
  FileCheck, 
  Clock, 
  PieChart,
  ChevronDown,
  ChevronUp,
  Table
} from 'lucide-react'
import { DocMeta } from '../App'

interface QueryPageProps {
  uploadedDoc: DocMeta | null
}

interface Citation {
  element: {
    element_id: string
    doc_id: string
    type: string
    content: string
    page: number
    bbox: any
  }
  score: number
  layer_scores: Record<string, number>
  rank: number
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    confidence: number
    confidence_label: string
    query_type: string
    weights_used: Record<string, number>
    table_direct: string[]
    grounded: boolean
    latency_ms: number
    tokens_used: number
    model: string
    citations: Citation[]
  }
}

const QueryPage: React.FC<QueryPageProps> = ({ uploadedDoc }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeCitationIndex, setActiveCitationIndex] = useState<number | null>(null)
  const [showMetadataMap, setShowMetadataMap] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Add initial greeting when document changes
    if (uploadedDoc) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `I've successfully loaded and analyzed **${uploadedDoc.filename}**. Ask me any analytical, structural, layout-specific, or semantic questions about this document!`,
          timestamp: new Date()
        }
      ])
    } else {
      setMessages([
        {
          id: 'no-doc',
          role: 'assistant',
          content: "Welcome! To start querying, please upload a document first. This allows me to decompose the file into its spatial, template, and semantic representations.",
          timestamp: new Date()
        }
      ])
    }
  }, [uploadedDoc])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || loading) return

    const userText = inputText.trim()
    setInputText('')

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: userText,
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userText,
          doc_id: uploadedDoc?.doc_id || null,
          top_k: 12,
          stream: false
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`)
      }

      const data = await response.json()

      const aiMessage: ChatMessage = {
        id: `msg-${Date.now()}-ai`,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        metadata: {
          confidence: data.confidence,
          confidence_label: data.confidence_label,
          query_type: data.query_type,
          weights_used: data.weights_used,
          table_direct: data.table_direct,
          grounded: data.grounded,
          latency_ms: data.latency_ms,
          tokens_used: data.tokens_used,
          model: data.model,
          citations: data.citations
        }
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: `❌ **Failed to retrieve answer:** ${err.message || 'The backend orchestrator could not compile a response. Ensure the API server is active.'}`,
        timestamp: new Date()
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const toggleMetadata = (msgId: string) => {
    setShowMetadataMap(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }))
  }

  const formatWeights = (weights: Record<string, number>) => {
    const keyMap: Record<string, string> = {
      w_s: 'Semantic (S)',
      w_g: 'Geometric (G)',
      w_r: 'Recurrence (R)',
      w_f: 'Frequency (F)',
      w_m: 'Matrix (M)',
      w_t: 'Template (T)',
      w_x: 'Graph Structure (X)'
    }
    return Object.entries(weights)
      .map(([k, v]) => ({ name: keyMap[k] || k, val: v }))
      .sort((a, b) => b.val - a.val)
  }

  return (
    <div className="chat-container">
      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg) => {
          const isAI = msg.role === 'assistant'
          const showMeta = showMetadataMap[msg.id] || false
          
          return (
            <div key={msg.id} className={`chat-bubble ${isAI ? 'chat-bubble-ai' : 'chat-bubble-user'}`}>
              <div className={`chat-avatar ${isAI ? 'chat-avatar-ai' : 'chat-avatar-user'}`}>
                {isAI ? <Bot size={16} /> : <User size={16} />}
              </div>
              <div className="chat-message-content" style={{ maxWidth: 'calc(100% - 46px)' }}>
                {/* Bubble */}
                <div className={`chat-message-bubble ${isAI ? 'chat-message-bubble-ai' : 'chat-message-bubble-user'}`}>
                  {/* Handle basic markdown formatting like bold, code, and line breaks */}
                  <div className="markdown-body">
                    {msg.content.split('\n').map((line, idx) => (
                      <p key={idx} dangerouslySetInnerHTML={{
                        __html: line
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/`(.*?)`/g, '<code>$1</code>')
                      }} />
                    ))}
                  </div>
                </div>

                {/* Table Direct answers */}
                {isAI && msg.metadata && msg.metadata.table_direct && msg.metadata.table_direct.length > 0 && (
                  <div className="table-answer mt-2">
                    <div className="table-answer-label flex items-center gap-1">
                      <Table size={12} />
                      Direct Table Matrix Extraction
                    </div>
                    <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                      {msg.metadata.table_direct.map((ans, idx) => (
                        <li key={idx} style={{ fontWeight: 600 }}>{ans}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Meta details bar */}
                {isAI && msg.metadata && (
                  <div className="chat-meta mt-2 flex flex-wrap gap-2 text-xs">
                    <span className={`badge ${
                      msg.metadata.confidence_label === 'HIGH' ? 'badge-success' : 
                      msg.metadata.confidence_label === 'MEDIUM' ? 'badge-warning' : 'badge-danger'
                    }`}>
                      Confidence: {msg.metadata.confidence_label}
                    </span>
                    <span className="badge badge-primary">
                      Route: {msg.metadata.query_type}
                    </span>
                    {msg.metadata.grounded && (
                      <span className="badge badge-success flex items-center gap-0.5" style={{ textTransform: 'none' }}>
                        <FileCheck size={10} />
                        Grounded
                      </span>
                    )}
                    <span className="badge badge-neutral flex items-center gap-0.5">
                      <Clock size={10} />
                      {msg.metadata.latency_ms} ms
                    </span>
                    
                    <button 
                      className="btn btn-ghost btn-sm flex items-center gap-1"
                      style={{ padding: '0.1rem 0.4rem', fontSize: '0.65rem', border: '1px solid var(--color-border)' }}
                      onClick={() => toggleMetadata(msg.id)}
                    >
                      {showMeta ? 'Hide Routing Matrix' : 'Explain Math Routing'}
                      {showMeta ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                    </button>
                  </div>
                )}

                {/* Rich Math routing details */}
                {isAI && msg.metadata && showMeta && (
                  <div className="card mt-2 p-4 flex flex-col gap-3 animate-fade-in" style={{ background: 'var(--color-bg)', borderColor: 'var(--color-border)' }}>
                    <div className="flex flex-col gap-2">
                      <div className="font-semibold text-xs text-muted flex items-center gap-1">
                        <PieChart size={12} />
                        Adaptive Fusion Layer Weights (ΣW = 1.0)
                      </div>
                      <div className="flex flex-col gap-1.5 mt-1">
                        {formatWeights(msg.metadata.weights_used).map(({ name, val }) => (
                          <div key={name} className="flex items-center gap-2 text-xs">
                            <span style={{ width: '130px', color: 'var(--color-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {name}
                            </span>
                            <div className="progress-bar" style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.03)' }}>
                              <div 
                                className="progress-fill" 
                                style={{ 
                                  width: `${val * 100}%`, 
                                  animation: 'none', 
                                  background: 'var(--color-primary)' 
                                }}
                              />
                            </div>
                            <span className="font-mono text-right" style={{ width: '40px' }}>
                              {(val * 100).toFixed(0)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {msg.metadata.citations && msg.metadata.citations.length > 0 && (
                      <div className="flex flex-col gap-2 mt-2">
                        <div className="font-semibold text-xs text-muted flex items-center gap-1">
                          <Terminal size={12} />
                          Retrieved Reference Elements ({msg.metadata.citations.length})
                        </div>
                        <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1">
                          {msg.metadata.citations.map((cit, idx) => {
                            const isElementActive = activeCitationIndex === idx
                            const hasSnippet = cit.element && cit.element.content
                            
                            return (
                              <div 
                                key={cit.element?.element_id || idx} 
                                className="card p-2 text-xs flex flex-col gap-1.5" 
                                style={{ 
                                  background: 'var(--color-elevated)', 
                                  borderColor: isElementActive ? 'var(--color-primary)' : 'var(--color-border)',
                                  cursor: 'pointer'
                                }}
                                onClick={() => setActiveCitationIndex(isElementActive ? null : idx)}
                              >
                                <div className="flex justify-between items-center">
                                  <div className="flex items-center gap-2">
                                    <span className="badge badge-neutral" style={{ padding: '0.1rem 0.35rem', fontSize: '0.6rem' }}>
                                      Rank {cit.rank}
                                    </span>
                                    <span className="badge badge-primary" style={{ padding: '0.1rem 0.35rem', fontSize: '0.6rem' }}>
                                      {(cit.element?.type || 'TEXT').toUpperCase()}
                                    </span>
                                    <span className="text-muted">Page {cit.element?.page || 1}</span>
                                  </div>
                                  <span className="font-mono text-primary font-semibold">
                                    Score: {cit.score.toFixed(4)}
                                  </span>
                                </div>
                                
                                {hasSnippet && (
                                  <div 
                                    className="font-mono p-2 mt-1" 
                                    style={{ 
                                      background: 'var(--color-bg)', 
                                      borderRadius: 'var(--radius-sm)', 
                                      color: 'var(--color-text)', 
                                      whiteSpace: isElementActive ? 'pre-wrap' : 'nowrap',
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      fontSize: '0.75rem',
                                      lineHeight: 1.4
                                    }}
                                  >
                                    {cit.element.content}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="chat-bubble chat-bubble-ai">
            <div className="chat-avatar chat-avatar-ai">
              <Bot size={16} />
            </div>
            <div className="chat-message-content">
              <div className="chat-message-bubble chat-message-bubble-ai flex items-center justify-center p-3">
                <div className="typing-indicator">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} className="chat-input-bar">
        <input
          type="text"
          className="input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={uploadedDoc ? `Ask about "${uploadedDoc.filename}"...` : "Select a document first to activate queries..."}
          disabled={!uploadedDoc || loading}
          style={{ flex: 1 }}
        />
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={!uploadedDoc || !inputText.trim() || loading}
          style={{ padding: '0.625rem' }}
          aria-label="Send query"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  )
}

export default QueryPage
