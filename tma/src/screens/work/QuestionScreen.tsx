import { useCallback, useEffect, useState, type CSSProperties } from 'react'
import { Button, Caption, Card, IconButton, Input, Placeholder, Progress, Subheadline } from '@telegram-apps/telegram-ui'
import { SkipForward } from 'lucide-react'
import { api, type AdvanceResult, type CurrentQuestion } from '../../api'
import { QuestionScreenSkeleton } from '../../components/SkeletonScreens'
import { ZoomableImage } from '../../components/ZoomableImage'
import { type NavActions } from '../../lib/navigation'
import { haptic } from '../../lib/telegram'

interface Props {
  nav: NavActions
  workId: number
}

type Phase = 'answering' | 'revealing' | 'scoring'

function ProgressBar({ position, total }: { position: number; total: number }) {
  const percent = total > 0 ? Math.round((position / total) * 100) : 0

  return (
    <div className="question-progress">
      <Progress value={percent} style={{ flex: 1 }} />
      <Caption style={{ color: 'var(--tgui--hint_color)', flexShrink: 0 }}>
        {position} / {total}
      </Caption>
    </div>
  )
}

function phaseForQuestion(question: CurrentQuestion): Phase {
  return question.is_selfcheck ? 'revealing' : 'answering'
}

export function QuestionScreen({ nav, workId }: Props) {
  const [question, setQuestion] = useState<CurrentQuestion | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [answer, setAnswer] = useState('')
  const [phase, setPhase] = useState<Phase>('answering')
  const [loadError, setLoadError] = useState('')
  const [actionError, setActionError] = useState('')

  const loadQuestion = useCallback(async () => {
    setLoading(true)
    setLoadError('')
    setActionError('')

    try {
      const currentQuestion = await api.getCurrentQuestion(workId)
      setQuestion(currentQuestion)
      setAnswer('')
      setPhase(phaseForQuestion(currentQuestion))
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Не удалось загрузить вопрос.'
      setLoadError(message)
      setQuestion(null)
    } finally {
      setLoading(false)
    }
  }, [workId])

  useEffect(() => {
    void loadQuestion()
  }, [loadQuestion])

  const handleAdvance = useCallback((result: AdvanceResult) => {
    setSubmitting(false)
    setActionError('')

    if (result.type === 'question') {
      setQuestion(result.question)
      setAnswer('')
      setPhase(phaseForQuestion(result.question))
      return
    }

    if (result.type === 'skipped') {
      nav.replace({ name: 'skipped', workId, count: result.count })
      return
    }

    nav.replace({ name: 'work-complete', workId })
  }, [nav, workId])

  const handleRequestError = useCallback((requestError: unknown, fallback: string) => {
    const message = requestError instanceof Error ? requestError.message : fallback
    haptic('error')
    setActionError(message)
    setSubmitting(false)
  }, [])

  const handleSubmitAnswer = async () => {
    if (!question || !answer.trim() || submitting) return

    setSubmitting(true)
    setActionError('')
    haptic('impact')

    try {
      const result = await api.submitAnswer(workId, question.work_question_id, answer.trim())
      handleAdvance(result)
    } catch (requestError) {
      handleRequestError(requestError, 'Не удалось отправить ответ.')
    }
  }

  const handleReveal = () => {
    haptic('selection')
    setActionError('')
    setPhase('scoring')
  }

  const handleSelfCheck = async (mark: number) => {
    if (!question || submitting) return

    setSubmitting(true)
    setActionError('')
    haptic('impact')

    try {
      const result = await api.submitSelfCheck(workId, question.work_question_id, mark)
      handleAdvance(result)
    } catch (requestError) {
      handleRequestError(requestError, 'Не удалось сохранить балл.')
    }
  }

  const handleSkip = async () => {
    if (!question || submitting) return

    setSubmitting(true)
    setActionError('')
    haptic('selection')

    try {
      const result = await api.skipQuestion(workId, question.work_question_id)
      handleAdvance(result)
    } catch (requestError) {
      handleRequestError(requestError, 'Не удалось пропустить вопрос.')
    }
  }

  if (loading) {
    return <QuestionScreenSkeleton />
  }

  if (loadError || !question) {
    return (
      <div className="screen-layout">
        <div className="screen-layout__body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
          <Placeholder
            header="Не удалось открыть вопрос"
            description={loadError || 'Попробуй обновить экран ещё раз.'}
          />
        </div>
        <div className="screen-footer">
          <Button size="l" stretched onClick={() => void loadQuestion()}>
            Попробовать снова
          </Button>
          <Button size="l" mode="gray" stretched onClick={nav.pop}>
            Назад
          </Button>
        </div>
      </div>
    )
  }

  const scoreButtons = Array.from({ length: question.full_mark + 1 }, (_, index) => index)

  return (
    <div className="question-layout">
      <div className="question-header">
        <ProgressBar position={question.position} total={question.total} />
        {question.is_selfcheck && (
          <Caption style={{ color: 'var(--tgui--hint_color)', display: 'block', marginTop: 4 }}>
            Самопроверка
          </Caption>
        )}
      </div>

      <div className="question-body">
        <Card style={{ padding: 14, marginBottom: 12 }}>
          {question.question_image && (
            <ZoomableImage
              src={api.imageUrl.question(question.question_id)}
              alt="Вопрос"
              placeholderHeight={220}
              marginBottom={12}
            />
          )}
          {question.text && (
            <Subheadline weight="2" style={{ lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
              {question.text}
            </Subheadline>
          )}
        </Card>

        {phase === 'scoring' && (
          <Card style={{ padding: 14 }}>
            <Caption style={{ color: 'var(--tgui--hint_color)', display: 'block', marginBottom: 6 }}>
              Ответ
            </Caption>
            {question.answer_image && (
              <ZoomableImage
                src={api.imageUrl.answer(question.question_id)}
                alt="Ответ"
                placeholderHeight={220}
                marginBottom={12}
              />
            )}
            {question.answer && (
              <Subheadline weight="2" style={{ lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
                {question.answer}
              </Subheadline>
            )}
          </Card>
        )}
      </div>

      <div className="question-footer">
        {phase === 'answering' && (
          <>
            <div className="app-input-shell">
              <Input
                placeholder="Введи ответ..."
                value={answer}
                className="app-wide-input"
                onChange={event => setAnswer(event.target.value)}
                onKeyDown={event => event.key === 'Enter' && void handleSubmitAnswer()}
                autoComplete="off"
                autoCorrect="off"
                spellCheck={false}
                disabled={submitting}
              />
            </div>
            <div className="question-actions">
              <Button size="l" stretched disabled={!answer.trim() || submitting} loading={submitting} onClick={() => void handleSubmitAnswer()}>
                Ответить
              </Button>
              <IconButton
                aria-label="Пропустить вопрос"
                size="l"
                mode="gray"
                className="question-skip-button"
                disabled={submitting}
                onClick={() => void handleSkip()}
              >
                <SkipForward size={20} className="question-skip-button__icon" />
              </IconButton>
            </div>
          </>
        )}

        {phase === 'revealing' && (
          <div className="question-actions">
            <Button size="l" stretched disabled={submitting} onClick={handleReveal}>
              Показать ответ
            </Button>
            <IconButton
              aria-label="Пропустить вопрос"
              size="l"
              mode="gray"
              className="question-skip-button"
              disabled={submitting}
              onClick={() => void handleSkip()}
            >
              <SkipForward size={20} className="question-skip-button__icon" />
            </IconButton>
          </div>
        )}

        {phase === 'scoring' && (
          <>
            <Caption style={{ color: 'var(--tgui--hint_color)', textAlign: 'center' }}>
              Выбери нужный балл
            </Caption>
            <div
              className="score-buttons"
              style={{ '--score-buttons-columns': Math.min(scoreButtons.length, 5) } as CSSProperties}
            >
              {scoreButtons.map(score => (
                <Button
                  key={score}
                  size="l"
                  mode="gray"
                  stretched
                  className="score-buttons__item"
                  disabled={submitting}
                  onClick={() => void handleSelfCheck(score)}
                >
                  {score}
                </Button>
              ))}
            </div>
          </>
        )}

        {actionError && (
          <Caption className="inline-error">
            {actionError}
          </Caption>
        )}
      </div>
    </div>
  )
}
