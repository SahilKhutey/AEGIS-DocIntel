import React, { useState } from 'react'
import UploadPage from './pages/UploadPage'
import QueryPage from './pages/QueryPage'
import AnalyticsPage from './pages/AnalyticsPage'
import {
  Upload,
  MessageSquare,
  BarChart3,
} from 'lucide-react'

type Tab = 'upload' | 'query' | 'analytics'

export interface DocMeta {
  doc_id: string
  filename: string
  pages: number
  tables: number
  elements: number
  compression_pct: number
  ingestion_ms?: number
  templates?: number
}

const HexLogo: React.FC = () => (
  <svg
    width="34"
    height="38"
    viewBox="0 0 34 38"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-label="AEGIS Logo"
  >
    <path
      d="M17 1L33 10V28L17 37L1 28V10L17 1Z"
      fill="hsl(220 90% 60% / 0.15)"
      stroke="hsl(220 90% 60%)"
      strokeWidth="1.5"
    />
    <path
      d="M17 8L27 13.5V24.5L17 30L7 24.5V13.5L17 8Z"
      fill="hsl(220 90% 60% / 0.1)"
      stroke="hsl(220 90% 60% / 0.6)"
      strokeWidth="1"
    />
    <circle cx="17" cy="19" r="4" fill="hsl(220 90% 60%)" />
    <line x1="17" y1="11" x2="17" y2="15" stroke="hsl(220 90% 60%)" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="17" y1="23" x2="17" y2="27" stroke="hsl(220 90% 60%)" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="11.5" y1="14" x2="15" y2="17" stroke="hsl(220 90% 60%)" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="19" y1="21" x2="22.5" y2="24" stroke="hsl(220 90% 60%)" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="22.5" y1="14" x2="19" y2="17" stroke="hsl(220 90% 60%)" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="15" y1="21" x2="11.5" y2="24" stroke="hsl(220 90% 60%)" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
)

const TAB_CONFIG: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'upload',    label: 'Upload',    icon: <Upload size={15} /> },
  { id: 'query',     label: 'Query',     icon: <MessageSquare size={15} /> },
  { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={15} /> },
]

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('upload')
  const [uploadedDoc, setUploadedDoc] = useState<DocMeta | null>(null)

  const handleDocIngested = (meta: DocMeta) => {
    setUploadedDoc(meta)
    setActiveTab('query')
  }

  return (
    <div className="app-shell">
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="app-header">
        <div className="flex items-center gap-3">
          <HexLogo />
          <div>
            <div
              className="flex items-center gap-2"
              style={{ lineHeight: 1.2 }}
            >
              <span
                style={{
                  fontWeight: 800,
                  fontSize: '1rem',
                  letterSpacing: '-0.02em',
                  color: 'var(--color-text)',
                }}
              >
                AEGIS-AMDI
              </span>
              <span
                style={{
                  fontWeight: 300,
                  fontSize: '0.875rem',
                  color: 'var(--color-text-muted)',
                }}
              >
                OS
              </span>
              <span className="badge badge-primary">v1.0</span>
            </div>
            <div
              className="text-xs"
              style={{ color: 'var(--color-text-muted)', marginTop: '1px' }}
            >
              Adaptive Mathematical Document Intelligence
            </div>
          </div>
        </div>

        {/* Right: doc status pill */}
        <div className="flex items-center gap-3">
          {uploadedDoc ? (
            <div
              className="flex items-center gap-2"
              style={{
                background: 'var(--color-success-dim)',
                border: '1px solid hsl(142 71% 45% / 0.3)',
                borderRadius: 'var(--radius-md)',
                padding: '0.35rem 0.875rem',
                fontSize: '0.78rem',
              }}
            >
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: 'var(--color-success)',
                  display: 'inline-block',
                  animation: 'pulse-glow 2s ease infinite',
                }}
              />
              <span className="text-success font-medium">
                {uploadedDoc.filename}
              </span>
              <span className="text-muted">active</span>
            </div>
          ) : (
            <span className="text-xs text-muted">No document loaded</span>
          )}
        </div>
      </header>

      {/* ── Tab Bar ─────────────────────────────────────────── */}
      <nav className="tabs">
        {TAB_CONFIG.map(({ id, label, icon }) => (
          <button
            key={id}
            className={`tab${activeTab === id ? ' active' : ''}`}
            onClick={() => setActiveTab(id)}
            aria-selected={activeTab === id}
          >
            {icon}
            {label}
          </button>
        ))}
      </nav>

      {/* ── Page Content ────────────────────────────────────── */}
      <main className="app-content">
        {activeTab === 'upload' && (
          <UploadPage onDocIngested={handleDocIngested} />
        )}
        {activeTab === 'query' && (
          <QueryPage uploadedDoc={uploadedDoc} />
        )}
        {activeTab === 'analytics' && <AnalyticsPage />}
      </main>
    </div>
  )
}

export default App
