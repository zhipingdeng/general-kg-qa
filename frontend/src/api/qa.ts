import api from './index'
import type { QARequest, QAResponse, KnowledgeGraph } from '@/types'

export const qaApi = {
  ask: async (data: QARequest): Promise<QAResponse> => {
    const resp = await api.post('/api/v1/qa', data)
    return resp.data
  }
}

export const knowledgeApi = {
  getGraph: async (limit: number = 100): Promise<KnowledgeGraph> => {
    const resp = await api.get('/api/v1/knowledge/graph', { params: { limit } })
    return resp.data
  }
}
