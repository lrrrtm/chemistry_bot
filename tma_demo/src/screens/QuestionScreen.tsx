import { useState } from 'react'
import { List, Section, Cell, Input, Button, Card, Text, Subheadline, Caption } from '@telegram-apps/telegram-ui'
import { getTopicById, getQuestionsByTopic } from '../data/mockData'

type State = 'answering' | 'correct' | 'incorrect'

interface Props {
  topicId: number
  onBack: () => void
}

export function QuestionScreen({ topicId, onBack }: Props) {
  const topic = getTopicById(topicId)
  const questions = getQuestionsByTopic(topicId)

  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [state, setState] = useState<State>('answering')
  const [score, setScore] = useState(0)

  if (!topic || questions.length === 0) {
    return (
      <List>
        <Section>
          <Cell onClick={onBack} style={{ cursor: 'pointer' }}>← Назад</Cell>
        </Section>
        <Section><Cell>Вопросы не найдены</Cell></Section>
      </List>
    )
  }

  const current = questions[index]
  const isLast = index === questions.length - 1

  const checkAnswer = () => {
    const correct = answer.trim().toLowerCase() === current.answer.toLowerCase()
    setState(correct ? 'correct' : 'incorrect')
    if (correct) setScore((s) => s + 1)
  }

  const goNext = () => {
    if (isLast) {
      onBack()
    } else {
      setIndex((i) => i + 1)
      setAnswer('')
      setState('answering')
    }
  }

  const progressDots = questions.map((_, i) => {
    let color = '#ddd'
    if (i < index) color = '#31b545'
    if (i === index) color = '#2481cc'
    return (
      <div
        key={i}
        style={{
          width: i === index ? 20 : 8,
          height: 8,
          borderRadius: 4,
          background: color,
          transition: 'all 0.2s',
          flexShrink: 0,
        }}
      />
    )
  })

  return (
    <List>
      {/* Header nav */}
      <Section>
        <Cell
          before={<span style={{ fontSize: 18 }}>←</span>}
          after={
            <Caption style={{ color: '#888' }}>
              {score} / {index} правильных
            </Caption>
          }
          onClick={onBack}
          style={{ cursor: 'pointer' }}
        >
          {topic.emoji} {topic.name}
        </Cell>
      </Section>

      {/* Dot progress */}
      <div
        style={{
          display: 'flex',
          gap: 4,
          alignItems: 'center',
          padding: '4px 16px 12px',
          flexWrap: 'wrap',
        }}
      >
        {progressDots}
        <Caption style={{ marginLeft: 8, color: '#888' }}>
          {index + 1} из {questions.length}
        </Caption>
      </div>

      {/* Question card */}
      <div style={{ padding: '0 16px 8px' }}>
        <Card style={{ padding: 16 }}>
          <Caption
            style={{ color: '#888', display: 'block', marginBottom: 8 }}
          >
            Задание {index + 1}
          </Caption>
          <Subheadline weight="2" style={{ lineHeight: 1.5 }}>
            {current.text}
          </Subheadline>
        </Card>
      </div>

      {/* Answer input */}
      {state === 'answering' && (
        <Section header="Ваш ответ">
          <Input
            placeholder="Введите ответ и нажмите Enter..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && answer.trim()) checkAnswer()
            }}
            autoComplete="off"
            autoCorrect="off"
            spellCheck={false}
          />
        </Section>
      )}

      {/* Feedback after answer */}
      {state !== 'answering' && (
        <div style={{ padding: '0 16px 8px' }}>
          <Card
            style={{
              padding: 16,
              background: state === 'correct'
                ? 'rgba(49,181,69,0.12)'
                : 'rgba(232,54,30,0.10)',
              border: `1px solid ${state === 'correct' ? '#31b545' : '#e8361e'}`,
            }}
          >
            <Text weight="2" style={{ color: state === 'correct' ? '#31b545' : '#e8361e', display: 'block', marginBottom: 6 }}>
              {state === 'correct' ? '✅ Правильно!' : `❌ Неправильно. Ответ: ${current.answer}`}
            </Text>
            <Caption style={{ color: 'var(--tgui--text_secondary, #888)', lineHeight: 1.5 }}>
              {current.explanation}
            </Caption>
          </Card>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {state === 'answering' ? (
          <>
            <Button size="l" stretched disabled={!answer.trim()} onClick={checkAnswer}>
              Проверить
            </Button>
            <Button size="l" mode="gray" stretched onClick={goNext}>
              Пропустить
            </Button>
          </>
        ) : (
          <Button size="l" stretched onClick={goNext}>
            {isLast ? '🎉 Завершить тренировку' : 'Следующий вопрос →'}
          </Button>
        )}
      </div>
    </List>
  )
}
