'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useRunWorkflow, useWorkflows } from '@/lib/hooks/use-extensions'
import { useTranslation } from '@/lib/hooks/use-translation'

export default function WorkflowsPage() {
  const { t } = useTranslation()
  const { data: workflows = [] } = useWorkflows()
  const runWorkflow = useRunWorkflow()

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 py-8">
      <h1 className="text-2xl font-semibold">{t('workflows.title')}</h1>

      {workflows.length === 0 && (
        <p className="text-muted-foreground">{t('workflows.empty')}</p>
      )}

      <div className="flex flex-col gap-3">
        {workflows.map((workflow) => (
          <Card key={workflow.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{workflow.name}</span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={runWorkflow.isPending}
                  onClick={() => workflow.id && runWorkflow.mutate(workflow.id)}
                >
                  {t('workflows.run')}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {workflow.schedule && (
                <Badge variant="secondary">{workflow.schedule}</Badge>
              )}
              {workflow.enabled === false && (
                <Badge variant="secondary">disabled</Badge>
              )}
              {workflow.last_run_at && (
                <span className="text-sm text-muted-foreground">
                  {workflow.last_run_at}
                </span>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
