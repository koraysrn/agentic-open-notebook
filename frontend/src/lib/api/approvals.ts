import { apiClient } from './client'

export interface ApprovalItem {
  id: string | null
  action_type: string | null
  status: string | null
  payload: string | null
}

export const approvalsApi = {
  list: async (): Promise<ApprovalItem[]> =>
    (await apiClient.get<ApprovalItem[]>('/approvals')).data,

  approve: async (id: string): Promise<ApprovalItem> =>
    (await apiClient.post<ApprovalItem>(`/approvals/${id}/approve`)).data,
}
