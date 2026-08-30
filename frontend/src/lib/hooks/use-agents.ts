import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { agentsApi, AgentInfo, ToolInfo } from '@/lib/api/agents'
import { QUERY_KEYS } from '@/lib/api/query-client'

export function useAgents() {
  return useQuery<AgentInfo[]>({
    queryKey: QUERY_KEYS.agents,
    queryFn: () => agentsApi.list(),
  })
}

export function useAgentTools() {
  return useQuery<ToolInfo[]>({
    queryKey: QUERY_KEYS.agentTools,
    queryFn: () => agentsApi.listTools(),
  })
}

export function useRunAgent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ goal, notebookId }: { goal: string; notebookId?: string }) =>
      agentsApi.run(goal, notebookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.agents })
    },
  })
}
