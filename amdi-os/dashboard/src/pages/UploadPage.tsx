import React, { useState, useRef } from 'react'
import { 
  Upload, 
  FileText, 
  Layers, 
  Table, 
  Cpu, 
  Zap, 
  Sparkles, 
  ArrowRight,
  CheckCircle,
  AlertTriangle
} from 'lucide-react'
import { DocMeta } from '../App'

interface UploadPageProps {
  onDocIngested: (meta: DocMeta) => void
}

const UploadPage: React.FC<UploadPageProps> = ({ onDocIngested }) => {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<DocMeta | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0])
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  const uploadFile = async (file: File) => {
    setUploading(true)
    setError(null)
    setProgress(15)
    setStats(null)

    const formData = new FormData()
    formData.append("file", file)

    // Simulate progress while calling backend
    const progressInterval = setInterval(() => {
      setProgress((prev) => (prev < 90 ? prev + 10 : prev))
    }, 150)

    try {
      const response = await fetch("/api/ingest", {
        method: "POST",
        body: formData,
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || `HTTP error ${response.status}`)
      }

      const data = await response.json()
      
      // Delay slightly to let the user see the 100% completion state
      setTimeout(() => {
        setStats({
          doc_id: data.doc_id,
          filename: data.filename,
          pages: data.pages,
          elements: data.elements,
          tables: data.tables,
          compression_pct: data.compression_pct,
          ingestion_ms: data.ingestion_ms,
          templates: data.templates,
        })
        setUploading(false)
      }, 500)

    } catch (err: any) {
      clearInterval(progressInterval)
      setUploading(false)
      setError(err.message || "An unexpected error occurred during ingestion.")
    }
  }

  return (
    <div className="flex flex-col gap-6" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
          Document Ingestion Portal
        </h2>
        <p className="text-sm text-muted">
          Upload any document to mathematically partition and cache it inside the pre-LLM AMDI-OS intelligence layer.
        </p>
      </div>

      {/* Upload Zone */}
      {!uploading && !stats && (
        <div 
          className={`dropzone ${dragActive ? 'dropzone-active' : ''}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileInput}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') triggerFileInput() }}
        >
          <input 
            ref={fileInputRef}
            type="file" 
            style={{ display: 'none' }} 
            onChange={handleFileChange}
            accept=".pdf,.docx,.xlsx,.pptx,.txt,.md,.html,.png,.jpg,.jpeg"
          />
          <div className="dropzone-icon">
            <Upload size={24} />
          </div>
          <div style={{ fontWeight: 600, fontSize: '1rem' }}>
            Drag & drop document here or click to browse
          </div>
          <div className="text-xs text-muted">
            Supports PDF, DOCX, XLSX, PPTX, Images, Markdown, HTML, and Text (up to 100 MB)
          </div>
        </div>
      )}

      {/* Ingress Progress */}
      {uploading && (
        <div className="card flex flex-col gap-4 p-6 text-center items-center justify-center">
          <div className="spinner spinner-lg"></div>
          <div className="flex flex-col gap-1 w-full" style={{ maxWidth: '400px', margin: '1rem 0' }}>
            <div className="flex justify-between text-xs text-muted">
              <span>Mathematical Ingestion & Extraction Pipeline Running...</span>
              <span className="font-semibold">{progress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
          <p className="text-xs text-muted" style={{ fontStyle: 'italic' }}>
            Extracting layouts, tokenizing matrix layers, building sequence templates, and running graph node embedding...
          </p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="alert alert-danger">
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <div className="flex flex-col gap-1">
            <span className="font-semibold">Ingestion Failure</span>
            <span className="text-xs">{error}</span>
          </div>
        </div>
      )}

      {/* Success & Ingestion Stats */}
      {stats && (
        <div className="flex flex-col gap-6 animate-fade-in">
          <div className="alert alert-success">
            <CheckCircle size={18} style={{ flexShrink: 0 }} />
            <div className="flex flex-col gap-1">
              <span className="font-semibold">Successfully Ingested "{stats.filename}"</span>
              <span className="text-xs">Document converted into 7 mathematical representations. Spatial indices and database caches built.</span>
            </div>
          </div>

          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
            Ingestion & Analysis Pipeline Metrics
          </h3>

          <div className="grid-4">
            <div className="stat-card">
              <div className="stat-card-icon" style={{ background: 'var(--color-primary-dim)', color: 'var(--color-primary)' }}>
                <FileText size={18} />
              </div>
              <div className="stat-card-value">{stats.pages}</div>
              <div className="stat-card-label">Total Pages</div>
            </div>

            <div className="stat-card">
              <div className="stat-card-icon" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'rgb(239, 68, 68)' }}>
                <Layers size={18} />
              </div>
              <div className="stat-card-value">{stats.elements}</div>
              <div className="stat-card-label">Geometric Elements</div>
            </div>

            <div className="stat-card">
              <div className="stat-card-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'rgb(245, 158, 11)' }}>
                <Table size={18} />
              </div>
              <div className="stat-card-value">{stats.tables}</div>
              <div className="stat-card-label">Table Elements</div>
            </div>

            <div className="stat-card">
              <div className="stat-card-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'rgb(16, 185, 129)' }}>
                <Cpu size={18} />
              </div>
              <div className="stat-card-value">{stats.templates ?? 0}</div>
              <div className="stat-card-label">Template Clusters</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card flex items-center gap-4">
              <div className="p-3" style={{ background: 'var(--color-primary-dim)', borderRadius: 'var(--radius-md)', color: 'var(--color-primary)' }}>
                <Zap size={20} />
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Ingestion Speed
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                  {stats.ingestion_ms ? `${stats.ingestion_ms} ms` : 'N/A'}
                </div>
              </div>
            </div>

            <div className="card flex items-center gap-4">
              <div className="p-3" style={{ background: 'rgba(168, 85, 247, 0.1)', borderRadius: 'var(--radius-md)', color: 'rgb(168, 85, 247)' }}>
                <Sparkles size={20} style={{ color: 'rgb(168, 85, 247)' }} />
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Token Reduction
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-success)' }}>
                  {stats.compression_pct}%
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end mt-4">
            <button 
              className="btn btn-primary btn-sm flex items-center gap-2"
              onClick={() => onDocIngested(stats)}
            >
              Proceed to Chat & Querying
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default UploadPage
