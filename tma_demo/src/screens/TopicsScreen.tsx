import { List, Section, Cell, Badge, Progress, Banner, Chip } from '@telegram-apps/telegram-ui'
import { TOPICS, type Topic } from '../data/mockData'

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

const levelColor: Record<Topic['level'], string> = {
  'Лёгкий': '#31b545',
  'Средний': '#f5a623',
  'Сложный': '#e8361e',
}

interface Props {
  onTopicSelect: (topicId: number) => void
}

export function TopicsScreen({ onTopicSelect }: Props) {
  return (
    <List>
      <Banner
        type="section"
        header="🔥 Серия 3 дня"
        subheader="Продолжайте — занятие сегодня до 23:59"
        callout="Не прерывайте!"
      />

      <Section header="Темы для подготовки">
        {TOPICS.map((topic) => {
          const percent = Math.round((topic.completed / topic.total) * 100)
          const remaining = topic.total - topic.completed
          return (
            <div key={topic.id} onClick={() => onTopicSelect(topic.id)} style={{ cursor: 'pointer' }}>
              <Cell
                before={<EmojiAvatar emoji={topic.emoji} />}
                after={
                  remaining > 0 ? (
                    <Badge type="number" mode="primary">{remaining}</Badge>
                  ) : (
                    <span style={{ fontSize: 18 }}>✅</span>
                  )
                }
                subtitle={
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                    {`${topic.completed} из ${topic.total} вопросов`}
                    <Chip
                      mode="outline"
                      style={{
                        fontSize: 11,
                        color: levelColor[topic.level],
                        padding: '1px 6px',
                        height: 18,
                        borderColor: levelColor[topic.level],
                      }}
                    >
                      {topic.level}
                    </Chip>
                  </span>
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

      <Section header="Последние занятия" footer="За последние 7 дней">
        <Cell
          before={<EmojiAvatar emoji="🕐" size={36} />}
          subtitle="Вчера в 19:32 · 8 из 10 правильных"
          after={<span style={{ fontSize: 13, fontWeight: 600, color: '#31b545' }}>+8 б.</span>}
        >
          Неорганическая химия
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="🕑" size={36} />}
          subtitle="2 дня назад · 5 из 8 правильных"
          after={<span style={{ fontSize: 13, fontWeight: 600, color: '#31b545' }}>+5 б.</span>}
        >
          Расчётные задачи
        </Cell>
        <Cell
          before={<EmojiAvatar emoji="🕒" size={36} />}
          subtitle="4 дня назад · 6 из 8 правильных"
          after={<span style={{ fontSize: 13, fontWeight: 600, color: '#31b545' }}>+6 б.</span>}
        >
          ОВР
        </Cell>
      </Section>
    </List>
  )
}
