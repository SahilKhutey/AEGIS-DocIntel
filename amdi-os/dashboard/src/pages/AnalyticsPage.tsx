import React, { useState, useEffect } from 'react'
import { 
  Trash2, 
  Cpu, 
  Compass, 
  GitMerge, 
  Database,
  CheckCircle,
  FileSpreadsheet
} from 'lucide-react'

interface DocumentMeta {
  doc_id: string
  filename: string
  pages: number
  tables: number
  ingested_at: number
}

const AnalyticsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentMeta[]>([])
  const [loading, setLoading] = useState(true)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/documents')
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      const data = await res.json()
      setDocuments(data)
    } catch (err: any) {
      setErrorMsg("Failed to retrieve document repository list.")
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete and un-cache "${filename}"?`)) return
    
    try {
      const res = await fetch(`/api/documents/${docId}`, {
        method: 'DELETE'
      })
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      
      setSuccessMsg(`Successfully deleted and un-cached "${filename}"`)
      setDocuments(prev => prev.filter(doc => doc.doc_id !== docId))
      
      setTimeout(() => {
        setSuccessMsg(null)
      }, 3000)
    } catch (err: any) {
      setErrorMsg(`Failed to delete "${filename}": ${err.message}`)
      setTimeout(() => {
        setErrorMsg(null)
      }, 4000)
    }
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  return (
    <div className="flex flex-col gap-6" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
          System Analytics & Document Store
        </h2>
        <p className="text-sm text-muted">
          Manage cache systems, view mathematical decomposition layers, and inspect the pre-LLM operating registry.
        </p>
      </div>

      {successMsg && (
        <div className="alert alert-success">
          <CheckCircle size={16} />
          <span className="text-xs">{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-danger">
          <Trash2 size={16} />
          <span className="text-xs">{errorMsg}</span>
        </div>
      )}

      {/* Grid: Overview and Equation */}
      <div className="grid-2">
        <div className="card flex flex-col gap-3">
          <div className="flex items-center gap-2 font-semibold" style={{ color: 'var(--color-primary)' }}>
            <Compass size={18} />
            Master Representation Formulation
          </div>
          <p className="text-xs text-muted">
            AMDI-OS processes documents by breaking them into 7 synchronized layers instead of flattening them into token streams.
          </p>
          <div className="math-block">
            <span className="math-sym">D</span> = (
            <span className="math-var">P</span>, 
            <span className="math-var">S</span>, 
            <span className="math-var">G</span>, 
            <span className="math-var">R</span>, 
            <span className="math-var">F</span>, 
            <span className="math-var">M</span>, 
            <span className="math-var">T</span>, 
            <span className="math-var">X</span>)
          </div>
          <div className="flex flex-col gap-1 text-xs" style={{ paddingLeft: '0.5rem' }}>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">P - Pages</span>
              <span>Geometric partitioning of canvas</span>
            </div>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">S - Semantic</span>
              <span>Dense embeddings + keyphrases</span>
            </div>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">G - Geometry</span>
              <span>2D bounding box spatial indexes</span>
            </div>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">R - Recurrence</span>
              <span>MinHash LSH structural duplicate clusters</span>
            </div>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">F - Frequency</span>
              <span>Entropy-weighted lexical indices</span>
            </div>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">M - Matrix</span>
              <span>Relational table data cells</span>
            </div>
            <div className="flex justify-between border-bottom py-1" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="font-mono text-muted">T - Template</span>
              <span>Structural document format clusters</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="font-mono text-muted">X - Graph</span>
              <span>PageRank linkage topology</span>
            </div>
          </div>
        </div>

        <div className="card flex flex-col gap-3">
          <div className="flex items-center gap-2 font-semibold" style={{ color: 'var(--color-primary)' }}>
            <GitMerge size={18} />
            Adaptive Fusion Routing Engine
          </div>
          <p className="text-xs text-muted">
            Incoming queries are classified using a heuristic router, assigning dynamic weights to fuse representation scores.
          </p>
          <div className="math-block">
            <span className="math-sym">R_final</span> = 
            α<span className="math-sym">S</span> + 
            β<span className="math-sym">G</span> + 
            γ<span className="math-sym">R</span> + 
            δ<span className="math-sym">F</span> + 
            ε<span className="math-sym">M</span> + 
            ζ<span className="math-sym">T</span> + 
            η<span className="math-sym">X</span>
          </div>
          <p className="text-xs text-muted">
            The weights (<span className="font-mono">α, β, γ, δ, ε, ζ, η</span>) are normalized to sum to exactly 1.0. For example:
          </p>
          <div className="flex flex-col gap-1 text-xs" style={{ paddingLeft: '0.5rem' }}>
            <div className="flex justify-between py-1" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <span className="font-semibold" style={{ color: 'var(--color-warning)' }}>Tabular Queries</span>
              <span className="font-mono">Matrix weight ε = 65%</span>
            </div>
            <div className="flex justify-between py-1" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <span className="font-semibold" style={{ color: 'var(--color-primary)' }}>Semantic Queries</span>
              <span className="font-mono">Semantic weight α = 75%</span>
            </div>
            <div className="flex justify-between py-1" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <span className="font-semibold" style={{ color: 'var(--color-success)' }}>Layout Queries</span>
              <span className="font-mono">Geometry weight β = 55%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="font-semibold" style={{ color: 'rgb(168, 85, 247)' }}>Graph Queries</span>
              <span className="font-mono">Linkage weight η = 50%</span>
            </div>
          </div>
        </div>
      </div>

      {/* System Architecture block */}
      <div className="card flex flex-col gap-3">
        <div className="flex items-center gap-2 font-semibold">
          <Cpu size={18} />
          AMDI-OS Data Flow Pipeline
        </div>
        <div className="arch-block">
          <span className="arch-node">Universal Parser</span> <span className="arch-arrow">→</span> <span className="arch-node">Layout/OCR Detector</span> <span className="arch-arrow">→</span> <span className="arch-node">Mathematical Representation Engines (x7)</span>
          <br />
          <span className="arch-label">{"                              ↓"}</span>
          <br />
          <span className="arch-node">Vector Cache (FAISS)</span> <span className="arch-arrow">←</span> <span className="arch-node">Adaptive Fusion Router</span> <span className="arch-arrow">→</span> <span className="arch-node">Hierarchical Memory (L0-L5)</span>
          <br />
          <span className="arch-label">{"                              ↓"}</span>
          <br />
          <span className="arch-node">Greedy Context Assembler</span> <span className="arch-arrow">→</span> <span className="arch-node">LLM Reasoner</span> <span className="arch-arrow">→</span> <span className="arch-node">Grounded Citation Output</span>
        </div>
      </div>

      {/* Document store management */}
      <div className="card flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2 font-semibold">
            <Database size={18} />
            Ingested Document Registry
          </div>
          <button 
            className="btn btn-ghost btn-sm flex items-center gap-1"
            onClick={fetchDocuments}
            disabled={loading}
          >
            Refresh Registry
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-6">
            <div className="spinner"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted">
            No documents currently active in memory. Use the Upload portal to ingest a file.
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Doc ID</th>
                  <th>Pages</th>
                  <th>Tables</th>
                  <th>Ingested At</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.doc_id}>
                    <td style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{doc.filename}</td>
                    <td className="font-mono text-xs text-muted" style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {doc.doc_id}
                    </td>
                    <td>{doc.pages}</td>
                    <td className="flex items-center gap-1" style={{ border: 'none' }}>
                      {doc.tables > 0 ? (
                        <span className="text-warning flex items-center gap-0.5">
                          <FileSpreadsheet size={12} />
                          {doc.tables}
                        </span>
                      ) : (
                        <span className="text-muted">0</span>
                      )}
                    </td>
                    <td className="text-xs text-muted">{formatDate(doc.ingested_at)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        className="btn btn-danger btn-sm btn-icon"
                        onClick={() => handleDelete(doc.doc_id, doc.filename)}
                        title="Delete document"
                        aria-label={`Delete ${doc.filename}`}
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default AnalyticsPage
