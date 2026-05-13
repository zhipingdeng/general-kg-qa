import type * as d3 from 'd3'

export interface UserLogin {
  username: string
  password: string
}

export interface UserRegister {
  username: string
  email: string
  password: string
}

export interface UserResponse {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface QARequest {
  question: string
}

export interface QAResponse {
  question: string
  entities: string[]
  answer: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  entities?: string[]
  timestamp?: number
}

export interface KnowledgeNode extends d3.SimulationNodeDatum {
  id: string
  name: string
  desc: string
  tag: string
}

export interface KnowledgeEdge {
  source: string
  target: string
  type: string
}

export interface KnowledgeGraph {
  nodes: KnowledgeNode[]
  edges: KnowledgeEdge[]
}
