import { apiClient } from './client'

export interface Workflow {
  id: string | null
  name: string | null
  definition: string | null
  schedule: string | null
  enabled: boolean | null
  last_run_at: string | null
}

export interface ConnectorInfo {
  kind: string
  name: string
}

export interface SyncConnectionInfo {
  id: string | null
  provider: string | null
  status: string | null
  last_sync_at: string | null
}

export interface Integration {
  connectors: ConnectorInfo[]
  connections: SyncConnectionInfo[]
}

export interface ActivityItem {
  kind: string
  id: string | null
  [key: string]: unknown
}

export const extensionsApi = {
  listWorkflows: async (): Promise<Workflow[]> =>
    (await apiClient.get<Workflow[]>('/workflows')).data,

  runWorkflow: async (id: string): Promise<{ command_id: string }> =>
    (await apiClient.post<{ command_id: string }>(`/workflows/${id}/run`)).data,

  listIntegrations: async (): Promise<Integration> =>
    (await apiClient.get<Integration>('/integrations')).data,

  listActivity: async (): Promise<{ items: ActivityItem[] }> =>
    (await apiClient.get<{ items: ActivityItem[] }>('/activity')).data,
}
