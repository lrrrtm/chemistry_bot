import { List, Section, Cell, Progress, Badge, Caption, Title, Subheadline } from '@telegram-apps/telegram-ui'
import { TOPICS } from '../data/mockData'

const EmojiAvatar = ({ emoji, size = 40 }: { emoji: string; size?: number }) => (
  <div
    style={{
      width: size,
      height: size,
      fontSize: size * 0.5,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '50%',
      background: 'var(--tgui--secondary_fill, #f1f1f1)',
      flexShrink: 0,
    }}
  >
    {emoji}
  </div>
)

export function StatsScreen() {
  const totalCompleted = TOPICS.reduce((s, t) => s + t.completed, 0)
  const totalQuestions = TOPICS.reduce((s, t) => s + t.total, 0)
  const overallPercent = Math.round((totalCompleted / totalQuestions) * 100)

  // Mocked EGE prediction
  const rawScore = 28
  const egeScore = 72

  return (
    <List>
      {/* EGE score card */}
      <div style={{ padding: '16px 16px 8px' }}>
        <div
          style={{
            borderRadius: 16,
            background: 'linear-gradient(135deg, #2481cc 0%, #1a6aab 100%)',
            padding: '20px 24px',
            color: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <Caption style={{ color: 'rgba(255,255,255,0.75)', display: 'block', marginBottom: 4 }}>
              Прогнозируемый балл ЕГЭ
            </Caption>
            <Title style={{ color: '#fff', fontSize: 48, lineHeight: 1 }}>{egeScore}</Title>
            <Caption style={{ color: 'rgba(255,255,255,0.75)', marginTop: 4, display: 'block' }}>
              Первичный: {rawScore} / 64
            </Caption>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 48 }}>📊</div>
            <Caption style={{ color: 'rgba(255,255,255,0.75)' }}>из 100</Caption>
          </div>
        </div>
      </div>

      {/* Overall progress */}
      <Section header="Общий прогресс" footer={`Решено ${totalCompleted} из ${totalQuestions} задач`}>
        <Cell
          before={<EmojiAvatar emoji="📈" />}
          after={<Badge type="number" mode="primary">{overallPercent}%</Badge>}
          subtitle="По всем темам"
        >
          Прогресс подготовки
        </Cell>
        <div style={{ padding: '2px 16px 12px' }}>
          <Progress value={overallPercent} />
        </div>
      </Section>

      {/* Per-topic breakdown */}
      <Section header="По темам">
        {TOPICS.map((topic) => {
          const percent = Math.round((topic.completed / topic.total) * 100)
          const color = percent >= 70 ? '#31b545' : percent >= 40 ? '#f5a623' : '#e8361e'
          return (
            <div key={topic.id}>
              <Cell
                before={<EmojiAvatar emoji={topic.emoji} size={36} />}
                subtitle={`${topic.completed} / ${topic.total} задач`}
                after={
                  <Subheadline weight="2" style={{ color }}>
                    {percent}%
                  </Subheadline>
                }
              >
                {topic.name}
              </Cell>
              <div style={{ padding: '2px 16px 10px' }}>
                <Progress value={percent} />
              </div>
            </div>
          )
        })}
      </Section>

      {/* Achievements */}
      <Section header="Достижения" footer="Выполни все задания темы, чтобы получить значок">
        <Cell
          before={<EmojiAvatar emoji="🥇" />}
          subtitle="Решено 25 задач по неорганической химии"
        >
          Мастер неорганики
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="🔥" />}
          subtitle="3 дня занятий подряд"
        >
          Серия 3 дня
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="⭐" />}
          subtitle="5 правильных ответов подряд — не выполнено"
          style={{ opacity: 0.45 }}
        >
          Снайпер
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="🎯" />}
          subtitle="Решить 100 задач — не выполнено"
          style={{ opacity: 0.45 }}
        >
          Сотня
        </Cell>
      </Section>

      {/* Recent sessions */}
      <Section header="История занятий">
        <Cell
          before={<EmojiAvatar emoji="✅" size={32} />}
          subtitle="Вчера · 8/10 правильных · 12 мин"
          after={<Badge type="number" mode="primary">+8</Badge>}
        >
          Неорганическая химия
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="✅" size={32} />}
          subtitle="2 дня назад · 5/8 правильных · 9 мин"
          after={<Badge type="number" mode="primary">+5</Badge>}
        >
          Расчётные задачи
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="✅" size={32} />}
          subtitle="4 дня назад · 6/8 правильных · 7 мин"
          after={<Badge type="number" mode="primary">+6</Badge>}
        >
          ОВР
        </Cell>
      </Section>
    </List>
  )
}
