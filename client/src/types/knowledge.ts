import type { UserBrief } from './user'

export type DocumentStatus = 'PROCESSING' | 'READY' | 'FAILED'
export type DocumentFileType = 'TXT' | 'MARKDOWN' | 'PDF'

export interface KnowledgeDocument {
  id: number
  title: string
  filename: string | null
  file_type: DocumentFileType
  status: DocumentStatus
  error_message: string | null
  chunk_count: number
  embedded_chunk_count: number
  uploaded_by: UserBrief | null
  created_at: string
  updated_at: string
}

export interface KnowledgeDocumentDetail extends KnowledgeDocument {
  content: string
}

export interface KnowledgeSearchResult {
  chunk_id: number
  document_id: number
  document_title: string
  section: string | null
  chunk_text: string
  score: number
}

export interface KnowledgeSearchResponse {
  mode: 'semantic' | 'keyword'
  results: KnowledgeSearchResult[]
}
