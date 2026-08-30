import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { approvalsApi, ApprovalItem } from '@/lib/api/approvals'
import {
  ActivityItem,
  extensionsApi,
  Integration,
  Workflow,
} from '@/lib/api/extensions'

export function useWorkflows() {
  return useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: () => extensionsApi.listWorkflows(),
  })
}

export function useIntegrations() {
  return useQuery<Integration>({
    queryKey: ['integrations'],
    queryFn: () => extensionsApi.listIntegrations(),
  })
}

export function useActivity() {
  return useQuery<{ items: ActivityItem[] }>({
    queryKey: ['activity'],
    queryFn: () => extensionsApi.listActivity(),
  })
}

export function useRunWorkflow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => extensionsApi.runWorkflow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
    },
  })
}

export function useApprovals() {
  return useQuery<ApprovalItem[]>({
    queryKey: ['approvals'],
    queryFn: () => approvalsApi.list(),
  })
}

export function useApproveApproval() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => approvalsApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['activity'] })
    },
  })
}
