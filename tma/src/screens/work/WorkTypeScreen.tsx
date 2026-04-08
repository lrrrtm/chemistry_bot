import { Cell, List, Section } from '@telegram-apps/telegram-ui'
import { Brain, FileText } from 'lucide-react'
import { type NavActions } from '../../lib/navigation'
import { haptic } from '../../lib/telegram'

interface Props {
  nav: NavActions
}

export function WorkTypeScreen({ nav }: Props) {
  return (
    <List>
      <Section header="Форматы тренировок">
        <Cell
          before={<FileText size={22} style={{ flexShrink: 0 }} />}
          subtitle="34 вопроса · Автопроверка и самопроверка"
          onClick={() => {
            haptic('selection')
            nav.push({ name: 'work-confirm', config: { type: 'ege', workName: 'КИМ ЕГЭ' } })
          }}
        >
          Тренировка в формате ЕГЭ
        </Cell>
        <Cell
          before={<Brain size={22} style={{ flexShrink: 0 }} />}
          subtitle="20 вопросов · Выбор темы"
          onClick={() => {
            haptic('selection')
            nav.push({ name: 'topic-select' })
          }}
        >
          Персональная тренировка
        </Cell>
      </Section>
    </List>
  )
}
