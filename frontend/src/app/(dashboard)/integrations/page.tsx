'use client'

import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useIntegrations } from '@/lib/hooks/use-extensions'
import { useTranslation } from '@/lib/hooks/use-translation'

export default function IntegrationsPage() {
  const { t } = useTranslation()
  const { data } = useIntegrations()

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 py-8">
      <h1 className="text-2xl font-semibold">{t('integrations.title')}</h1>

      <div className="flex flex-col gap-3">
        {data?.connectors.map((connector) => (
          <Card key={connector.name}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>{connector.name}</span>
                <Badge variant="secondary">{connector.kind}</Badge>
              </CardTitle>
            </CardHeader>
          </Card>
        ))}

        {(!data || data.connections.length === 0) && (
          <p className="text-muted-foreground">{t('integrations.empty')}</p>
        )}

        {data?.connections.map((connection) => (
          <Card key={connection.id}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>{connection.provider}</span>
                <Badge variant="secondary">{connection.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-sm text-muted-foreground">
                {connection.last_sync_at}
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
