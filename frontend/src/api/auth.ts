import api from './index'
import type { UserLogin, UserRegister, TokenResponse, UserResponse } from '@/types'

export const authApi = {
  login: async (data: UserLogin): Promise<TokenResponse> => {
    const resp = await api.post('/api/v1/auth/login', data)
    return resp.data
  },
  register: async (data: UserRegister): Promise<TokenResponse> => {
    const resp = await api.post('/api/v1/auth/register', data)
    return resp.data
  },
  getMe: async (): Promise<UserResponse> => {
    const resp = await api.get('/api/v1/auth/me')
    return resp.data
  }
}
