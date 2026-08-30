import { apiClient } from './client'

export interface AgentInfo {
  name: string
  description: string
  capabilities: string[]
  tools: string[]
}

export interface ToolInfo {
  name: string
  description: string
}

export interface AgentRunResponse {
  command_id: string
}

export const agentsApi = {
  list: async (): Promise<AgentInfo[]> =>
    (await apiClient.get<AgentInfo[]>('/agents')).data,

  listTools: async (): Promise<ToolInfo[]> =>
    (await apiClient.get<ToolInfo[]>('/agents/tools')).data,

  run: async (goal: string, notebookId?: string): Promise<AgentRunResponse> =>
    (await apiClient.post<AgentRunResponse>('/agents/run', {
      goal,
      notebook_id: notebookId,
    })).data,
}
