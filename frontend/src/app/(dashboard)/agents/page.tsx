'use client'

import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { useAgentTools, useAgents, useRunAgent } from '@/lib/hooks/use-agents'
import { useTranslation } from '@/lib/hooks/use-translation'

export default function AgentsPage() {
  const { t } = useTranslation()
  const { data: agents = [] } = useAgents()
  const { data: tools = [] } = useAgentTools()
  const runAgent = useRunAgent()
  const [goal, setGoal] = useState('')

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 py-8">
      <div>
        <h1 className="text-2xl font-semibold">{t('agents.title')}</h1>
        <p className="text-muted-foreground">{t('agents.subtitle')}</p>
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium">{t('agents.goalLabel')}</label>
        <Textarea
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          placeholder={t('agents.goalPlaceholder')}
        />
        <Button
          onClick={() => goal.trim() && runAgent.mutate({ goal: goal.trim() })}
          disabled={!goal.trim() || runAgent.isPending}
        >
          {t('agents.run')}
        </Button>
        {runAgent.data && (
          <p className="text-sm text-muted-foreground">
            {t('agents.commandId')}: {runAgent.data.command_id}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('agents.availableAgents')}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {agents.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {t('agents.noAgents')}
              </p>
            )}
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="flex flex-col gap-1 border-b pb-2 last:border-0"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{agent.name}</span>
                  {agent.capabilities.map((capability) => (
                    <Badge key={capability} variant="secondary">
                      {capability}
                    </Badge>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  {agent.description}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('agents.availableTools')}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {tools.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {t('agents.noTools')}
              </p>
            )}
            {tools.map((tool) => (
              <div
                key={tool.name}
                className="flex flex-col border-b pb-2 last:border-0"
              >
                <span className="font-medium">{tool.name}</span>
                <p className="text-sm text-muted-foreground">
                  {tool.description}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
