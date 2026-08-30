'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { EducationResult, researchApi } from '@/lib/api/research'
import { useTranslation } from '@/lib/hooks/use-translation'

export default function StudyPage() {
  const { t } = useTranslation()
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<EducationResult | null>(null)

  const generate = async () => {
    if (!content.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await researchApi.study(content.trim()))
    } catch {
      setError(t('study.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 py-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{t('study.title')}</h1>
        <p className="text-muted-foreground">{t('study.subtitle')}</p>
      </div>

      <div className="flex flex-col gap-3">
        <label className="text-sm font-medium">{t('study.sourceLabel')}</label>
        <Textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder={t('study.sourcePlaceholder')}
          rows={6}
        />
        <Button onClick={generate} disabled={!content.trim() || loading}>
          {loading ? t('study.generating') : t('study.generate')}
        </Button>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {result && (
        <>
          {result.explanation && (
            <Card>
              <CardHeader>
                <CardTitle>{t('study.explanation')}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {result.explanation}
                </p>
              </CardContent>
            </Card>
          )}

          {result.plan.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{t('study.plan')}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {result.plan.map((step, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between border-b pb-2 last:border-0"
                  >
                    <span className="text-sm">{step.topic}</span>
                    <span className="text-sm text-muted-foreground">
                      {step.minutes}m
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {result.quiz.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{t('study.quiz')}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {result.quiz.map((question, index) => (
                  <div key={index} className="flex flex-col gap-1 text-sm">
                    <p className="font-medium">
                      {t('study.question')}: {question.text}
                    </p>
                    <p className="text-muted-foreground">
                      {t('study.answer')}: {question.answer}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {result.flashcards.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{t('study.flashcards')}</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {result.flashcards.map((card, index) => (
                  <div key={index} className="rounded-lg border p-3 text-sm">
                    <p className="font-medium">
                      {t('study.front')}: {card.front}
                    </p>
                    <p className="mt-1 text-muted-foreground">
                      {t('study.back')}: {card.back}
                    </p>
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
