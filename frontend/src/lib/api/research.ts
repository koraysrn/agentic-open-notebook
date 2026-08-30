import { apiClient } from './client'

export interface Claim {
  text: string
  label: string
  confidence: number
}

export interface Evidence {
  id: string | null
  title: string | null
  content: string
}

export interface ResearchResult {
  draft: string
  claims: Claim[]
  evidence: Evidence[]
}

export interface Question {
  text: string
  answer: string
}

export interface Flashcard {
  front: string
  back: string
}

export interface StudyPlanStep {
  topic: string
  minutes: number
}

export interface EducationResult {
  explanation: string
  plan: StudyPlanStep[]
  quiz: Question[]
  flashcards: Flashcard[]
}

export const researchApi = {
  run: async (question: string): Promise<ResearchResult> =>
    (await apiClient.post<ResearchResult>('/research', { question })).data,

  study: async (sourceContent: string): Promise<EducationResult> =>
    (await apiClient.post<EducationResult>('/education/material', {
      source_content: sourceContent,
    })).data,
}
