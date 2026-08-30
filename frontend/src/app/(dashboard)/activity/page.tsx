'use client'

import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useActivity } from '@/lib/hooks/use-extensions'
import { useTranslation } from '@/lib/hooks/use-translation'

export default function ActivityPage() {
  const { t } = useTranslation()
  const { data } = useActivity()

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 py-8">
      <h1 className="text-2xl font-semibold">{t('activity.title')}</h1>

      {(!data || data.items.length === 0) && (
        <p className="text-muted-foreground">{t('activity.empty')}</p>
      )}

      <div className="flex flex-col gap-3">
        {data?.items.map((item, index) => (
          <Card key={item.id ?? index}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>{item.kind}</span>
                <Badge variant="secondary">
                  {String(item.status ?? '')}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-sm text-muted-foreground">
                {String(item.goal ?? item.action_type ?? item.id ?? '')}
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
