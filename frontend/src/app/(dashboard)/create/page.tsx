'use client'

import Link from 'next/link'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useTranslation } from '@/lib/hooks/use-translation'

const ITEMS: {
  labelKey: string
  descKey: string
  href: string
}[] = [
  { labelKey: 'create.summary', descKey: 'create.summaryDesc', href: '/transformations' },
  { labelKey: 'create.report', descKey: 'create.reportDesc', href: '/research' },
  { labelKey: 'create.presentation', descKey: 'create.presentationDesc', href: '/transformations' },
  { labelKey: 'create.quiz', descKey: 'create.quizDesc', href: '/study' },
  { labelKey: 'create.flashcards', descKey: 'create.flashcardsDesc', href: '/study' },
  { labelKey: 'create.podcast', descKey: 'create.podcastDesc', href: '/podcasts' },
]

export default function CreatePage() {
  const { t } = useTranslation()

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 py-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{t('create.title')}</h1>
        <p className="text-muted-foreground">{t('create.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ITEMS.map((item) => (
          <Link key={item.labelKey} href={item.href}>
            <Card className="card-hover h-full">
              <CardHeader>
                <CardTitle className="text-base">{t(item.labelKey)}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{t(item.descKey)}</CardDescription>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
