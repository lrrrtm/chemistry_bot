import { useCallback } from 'react'
import { Button } from '@telegram-apps/telegram-ui'

import boomsphereAnimation from '../../assets/boomsphere.json'
import { AnimatedPlaceholder } from '../../components/AnimatedPlaceholder'
import { type NavActions } from '../../lib/navigation'
import { haptic } from '../../lib/telegram'

interface Props {
  nav: NavActions
  workId: number
  onDone: () => void
}

export function WorkCompleteScreen({ nav, workId, onDone }: Props) {
  const handleResults = useCallback(() => {
    haptic('selection')
    onDone()
    nav.replace({ name: 'work-results', workId })
  }, [nav, onDone, workId])

  return (
    <div className="screen-layout">
      <div
        className="screen-layout__body"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}
      >
        <AnimatedPlaceholder
          animationData={boomsphereAnimation}
          title="Тренировка завершена"
          description="Скорее переходи к результатам"
        />
      </div>

      <div className="screen-footer">
        <Button size="l" stretched onClick={() => void handleResults()}>
          Посмотреть результаты
        </Button>
      </div>
    </div>
  )
}
