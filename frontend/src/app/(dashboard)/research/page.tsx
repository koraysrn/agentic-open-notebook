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
import { researchApi, ResearchResult } from '@/lib/api/research'
import { useTranslation } from '@/lib/hooks/use-translation'

const LABEL_VARIANT: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  verified: 'default',
  external: 'secondary',
  inferred: 'outline',
  unverified: 'destructive',
}

const CLAIM_LABELS: Record<string, string> = {
  verified: 'research.verified',
  external: 'research.external',
  inferred: 'research.inferred',
  unverified: 'research.unverified',
}

export default function ResearchPage() {
  const { t } = useTranslation()
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ResearchResult | null>(null)

  const run = async () => {
    if (!question.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await researchApi.run(question.trim()))
    } catch {
      setError(t('research.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 py-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{t('research.title')}</h1>
        <p className="text-muted-foreground">{t('research.subtitle')}</p>
      </div>

      <div className="flex flex-col gap-3">
        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={t('research.placeholder')}
          rows={3}
        />
        <Button onClick={run} disabled={!question.trim() || loading}>
          {loading ? t('research.generating') : t('research.start')}
        </Button>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>{t('research.draft')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {result.draft}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('research.claims')}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {result.claims.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  {t('research.none')}
                </p>
              )}
              {result.claims.map((claim, index) => (
                <div
                  key={index}
                  className="flex flex-col gap-1 border-b pb-2 last:border-0"
                >
                  <p className="text-sm">{claim.text}</p>
                  <Badge
                    variant={LABEL_VARIANT[claim.label] ?? 'secondary'}
                    className="w-fit"
                  >
                    {t(CLAIM_LABELS[claim.label] ?? 'research.unverified')}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          {result.evidence.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{t('research.evidence')}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {result.evidence.map((item, index) => (
                  <div key={index} className="text-sm">
                    <span className="font-medium">
                      {item.title || item.id || `#${index + 1}`}
                    </span>
                    <p className="text-muted-foreground">{item.content}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
