import { useCallback, useState } from 'react'
import { Banner, Button, List } from '@telegram-apps/telegram-ui'
import { api } from '../../api'
import { SectionCellsSkeleton } from '../../components/SkeletonScreens'
import { type NavActions } from '../../lib/navigation'
import { haptic } from '../../lib/telegram'

interface Props {
  nav: NavActions
  workId: number
  count: number
}

export function SkippedScreen({ nav, workId, count }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRedo = useCallback(async () => {
    if (loading) return

    setLoading(true)
    setError('')
    haptic('impact')

    try {
      await api.requeueSkipped(workId)
      nav.replace({ name: 'question', workId })
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Не удалось вернуть пропущенные вопросы.'
      setError(message)
      haptic('error')
      setLoading(false)
    }
  }, [loading, nav, workId])

  const handleFinish = useCallback(async () => {
    if (loading) return

    setLoading(true)
    setError('')
    haptic('selection')

    try {
      await api.finishWork(workId)
      nav.replace({ name: 'work-complete', workId })
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Не удалось завершить тренировку.'
      setError(message)
      haptic('error')
      setLoading(false)
    }
  }, [loading, nav, workId])

  return (
    <div className="screen-layout">
      <div className="screen-layout__body">
        <List>
          <Banner
            type="section"
            header={`Пропущено вопросов: ${count}`}
            subheader="Можно вернуться к ним сейчас или завершить тренировку на текущем результате."
            callout="Почти готово"
          />

          {error && (
            <div style={{ padding: '0 16px 8px' }}>
              <Banner type="section" header="Не получилось выполнить действие" subheader={error} />
            </div>
          )}

          {loading && <SectionCellsSkeleton titleWidth="34%" subtitleWidth="22%" />}
        </List>
      </div>

      <div className="screen-footer">
        <Button size="l" stretched disabled={loading} loading={loading} onClick={() => void handleRedo()}>
          Вернуться к пропущенным
        </Button>
        <Button size="l" mode="gray" stretched disabled={loading} onClick={() => void handleFinish()}>
          Завершить тренировку
        </Button>
      </div>
    </div>
  )
}
