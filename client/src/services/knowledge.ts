import api from './api'
import type { KnowledgeDocument, KnowledgeDocumentDetail, KnowledgeSearchResponse } from '../types/knowledge'

export async function listDocuments() {
  const { data } = await api.get<KnowledgeDocument[]>('/knowledge/documents')
  return data
}

export async function getDocument(id: number) {
  const { data } = await api.get<KnowledgeDocumentDetail>(`/knowledge/documents/${id}`)
  return data
}

export async function uploadDocument(file: File, title?: string) {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)
  const { data } = await api.post<KnowledgeDocument>('/knowledge/documents', form)
  return data
}

export async function createArticle(title: string, content: string) {
  const form = new FormData()
  form.append('title', title)
  form.append('content', content)
  const { data } = await api.post<KnowledgeDocument>('/knowledge/documents', form)
  return data
}

export async function regenerateEmbeddings(id: number) {
  const { data } = await api.post<KnowledgeDocument>(`/knowledge/documents/${id}/embed`)
  return data
}

export async function deleteDocument(id: number) {
  await api.delete(`/knowledge/documents/${id}`)
}

export async function searchKnowledge(query: string, limit = 5) {
  const { data } = await api.get<KnowledgeSearchResponse>('/knowledge/search', { params: { q: query, limit } })
  return data
}
