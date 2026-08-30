'use client'

import Link from 'next/link'
import { useState } from 'react'

import { ArrowRight, GraduationCap, Search, Sparkles, Zap } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useActivity, useApprovals } from '@/lib/hooks/use-extensions'
import { useNotebooks } from '@/lib/hooks/use-notebooks'
import { useTranslation } from '@/lib/hooks/use-translation'

const SUGGESTED_ACTIONS = [
  { labelKey: 'home.research', href: '/research', icon: Search },
  { labelKey: 'home.study', href: '/study', icon: GraduationCap },
  { labelKey: 'home.create', href: '/create', icon: Sparkles },
  { labelKey: 'home.actions', href: '/activity', icon: Zap },
] as const

export default function HomePage() {
  const { t } = useTranslation()
  const { data: notebooks = [] } = useNotebooks()
  const { data: activityData } = useActivity()
  const { data: approvals = [] } = useApprovals()
  const [goal, setGoal] = useState('')

  const pending = approvals.filter((approval) => approval.status === 'pending')
  const recentNotebooks = notebooks.slice(0, 4)

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-10 px-6 py-14">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          {t('home.greeting')}
        </h1>
        <p className="text-lg text-muted-foreground">{t('home.question')}</p>
      </div>

      <div className="flex items-center gap-2 rounded-xl border bg-card p-2 shadow-soft">
        <Input
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          placeholder={t('home.inputPlaceholder')}
          className="border-0 bg-transparent shadow-none focus-visible:ring-0"
        />
        <Button disabled={!goal.trim()} aria-label={t('home.go')}>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium text-muted-foreground">
          {t('home.suggested')}
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {SUGGESTED_ACTIONS.map((action) => (
            <Link key={action.labelKey} href={action.href}>
              <Card className="card-hover h-full">
                <CardContent className="flex items-center gap-2 py-4">
                  <action.icon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">
                    {t(action.labelKey)}
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {recentNotebooks.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-muted-foreground">
            {t('home.recentNotebooks')}
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {recentNotebooks.map((notebook) => (
              <Link key={notebook.id} href={`/notebooks/${notebook.id}`}>
                <Card className="card-hover">
                  <CardContent className="flex flex-col gap-1 py-4">
                    <span className="font-medium">{notebook.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {notebook.description}
                    </span>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      {pending.length > 0 && (
        <section>
          <Link href="/activity">
            <Card className="card-hover border-warn/40 bg-warn-tint">
              <CardContent className="flex items-center justify-between py-4">
                <span className="text-sm font-medium">
                  {t('home.pendingApprovals', { count: pending.length })}
                </span>
                <Badge variant="secondary">{pending.length}</Badge>
              </CardContent>
            </Card>
          </Link>
        </section>
      )}

      {activityData && activityData.items.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-muted-foreground">
            {t('home.recentActivity')}
          </h2>
          <div className="flex flex-col gap-2">
            {activityData.items.slice(0, 5).map((item, index) => (
              <div
                key={item.id ?? index}
                className="flex items-center justify-between border-b pb-2 text-sm last:border-0"
              >
                <span>{item.kind}</span>
                <Badge variant="secondary">
                  {String(item.status ?? '')}
                </Badge>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
