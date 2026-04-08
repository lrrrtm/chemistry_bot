import { useEffect, useState, type CSSProperties } from 'react'
import { Caption, Card, Cell, List, Placeholder, Progress, Section, Subheadline } from '@telegram-apps/telegram-ui'
import { Calendar, CheckCircle, Clock, MinusCircle, XCircle } from 'lucide-react'
import { api, type WorkResult } from '../../api'
import { WorkResultsScreenSkeleton } from '../../components/SkeletonScreens'
import { ZoomableImage } from '../../components/ZoomableImage'
import { formatLocalDate, parseServerDate } from '../../lib/datetime'
import { type NavActions } from '../../lib/navigation'

interface Props {
  nav: NavActions
  workId: number
}

function parseDate(value: string | null) {
  return parseServerDate(value)
}

function formatDate(iso: string | null) {
  return formatLocalDate(iso, {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDuration(start: string | null, end: string | null) {
  const startDate = parseDate(start)
  const endDate = parseDate(end)
  if (!startDate || !endDate || Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return '-'

  const ms = Math.max(0, endDate.getTime() - startDate.getTime())
  const hours = Math.floor(ms / 3_600_000)
  const minutes = Math.floor((ms % 3_600_000) / 60_000)
  const seconds = Math.floor((ms % 60_000) / 1_000)

  if (hours > 0) return `${hours}ч ${minutes}м ${seconds}с`
  if (minutes > 0) return `${minutes}м ${seconds}с`
  return `${seconds}с`
}

function resultColor(mark: number, full: number) {
  if (mark === full) return '#31b545'
  if (mark > 0) return '#f5a623'
  return '#e8361e'
}

export function WorkResultsScreen({ nav: _nav, workId }: Props) {
  const [result, setResult] = useState<WorkResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getWorkResults(workId)
      .then(setResult)
      .catch(requestError => {
        const message = requestError instanceof Error ? requestError.message : 'Не удалось загрузить результаты.'
        setError(message)
      })
      .finally(() => setLoading(false))
  }, [workId])

  if (loading) {
    return <WorkResultsScreenSkeleton />
  }

  if (error || !result) {
    return (
      <List>
        <Section>
          <Placeholder
            header="Не удалось загрузить результаты"
            description={error || 'Попробуй открыть этот экран чуть позже'}
          />
        </Section>
      </List>
    )
  }

  const general = result.general
  const total = general.fully + general.semi + general.zero
  const markPercent = general.max_mark > 0 ? Math.round((general.final_mark / general.max_mark) * 100) : 0

  return (
    <List>
      <Section header="Обзор тренировки">
        <Cell subtitle="Название">{general.name}</Cell>
        <Cell before={<Calendar size={18} style={{ flexShrink: 0, color: 'var(--tgui--hint_color)' }} />} subtitle="Дата">
          {formatDate(general.start)}
        </Cell>
        <Cell before={<Clock size={18} style={{ flexShrink: 0, color: 'var(--tgui--hint_color)' }} />} subtitle="Время тренировки">
          {formatDuration(general.start, general.end)}
        </Cell>
      </Section>

      <Section header="Баллы">
        <div style={{ padding: '12px 16px 16px' }}>
          <Card style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12, marginBottom: 12 }}>
              <div>
                <span style={{ fontSize: 40, fontWeight: 700, lineHeight: 1 }}>{general.final_mark}</span>
                <span style={{ fontSize: 18, color: 'var(--tgui--hint_color)', marginLeft: 4 }}>/ {general.max_mark}</span>
                <Caption style={{ color: 'var(--tgui--hint_color)', display: 'block', marginTop: 4 }}>
                  итоговый балл
                </Caption>
              </div>

              <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <CheckCircle size={14} color="#31b545" />
                  <Caption style={{ fontWeight: 600, color: '#31b545' }}>{general.fully}</Caption>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <MinusCircle size={14} color="#f5a623" />
                  <Caption style={{ fontWeight: 600, color: '#f5a623' }}>{general.semi}</Caption>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <XCircle size={14} color="#e8361e" />
                  <Caption style={{ fontWeight: 600, color: '#e8361e' }}>{general.zero}</Caption>
                </div>
              </div>
            </div>

            {total > 0 && (
              <Progress
                value={markPercent}
                style={{ '--tgui--progress_bar_fill_color': 'var(--tgui--accent_text_color)' } as CSSProperties}
              />
            )}
          </Card>
        </div>
      </Section>

      <Section header="Разбор по вопросам">
        {result.questions.map(question => {
          const color = resultColor(question.user_mark, question.full_mark)
          const skipped = question.user_answer === 'вопрос пропущен'

          return (
            <div key={question.index} style={{ padding: '0 16px 12px' }}>
              <Card style={{ display: 'block', width: '100%', boxSizing: 'border-box', padding: 14 }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 12,
                    alignSelf: 'stretch',
                    width: '100%',
                    boxSizing: 'border-box',
                    padding: '10px 12px',
                    marginBottom: 12,
                    borderRadius: 12,
                    background: 'var(--tgui--tertiary_bg_color)',
                  }}
                >
                  <Subheadline weight="2" style={{ minWidth: 0, whiteSpace: 'normal', wordBreak: 'break-word' }}>
                    {`Вопрос №${question.index} (id${question.question_id})`}
                  </Subheadline>
                  <Caption style={{ color, fontWeight: 600, flexShrink: 0 }}>
                    {question.user_mark}/{question.full_mark}
                  </Caption>
                </div>

                {question.question_image && (
                  <ZoomableImage
                    src={api.imageUrl.question(question.question_id)}
                    alt={`Вопрос ${question.index}`}
                    placeholderHeight={180}
                    marginBottom={10}
                  />
                )}

                {question.text && (
                  <Subheadline weight="2" style={{ display: 'block', lineHeight: 1.5, whiteSpace: 'pre-wrap', marginBottom: 10 }}>
                    {question.text}
                  </Subheadline>
                )}

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '4px 12px',
                    padding: '10px 12px',
                    borderRadius: 12,
                    background: 'var(--tgui--tertiary_bg_color)',
                    marginTop: 10,
                  }}
                >
                  <Caption style={{ color: 'var(--tgui--hint_color)' }}>Твой ответ</Caption>
                  <Caption style={{ color: 'var(--tgui--hint_color)' }}>Верный ответ</Caption>
                  <Caption style={{ fontWeight: 600, color, wordBreak: 'break-word' }}>
                    {skipped ? '-' : (question.user_answer || '-')}
                  </Caption>
                  <Caption style={{ fontWeight: 600, color: '#31b545', wordBreak: 'break-word' }}>
                    {question.answer}
                  </Caption>
                </div>

                {question.answer_image && (
                  <ZoomableImage
                    src={api.imageUrl.answer(question.question_id)}
                    alt={`Ответ ${question.index}`}
                    placeholderHeight={180}
                    marginTop={10}
                    marginBottom={0}
                  />
                )}
              </Card>
            </div>
          )
        })}
      </Section>
    </List>
  )
}
