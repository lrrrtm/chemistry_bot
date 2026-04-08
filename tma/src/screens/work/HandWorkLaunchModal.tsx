import { useEffect, useState } from 'react'
import { Banner, Button, Caption, Modal, Subheadline } from '@telegram-apps/telegram-ui'
import { api, type HandWorkInfo } from '../../api'
import { SectionCellsSkeleton } from '../../components/SkeletonScreens'
import { type NavActions } from '../../lib/navigation'
import { haptic } from '../../lib/telegram'

interface Props {
  open: boolean
  identificator: string | null
  nav: NavActions
  onClose: () => void
}

export function HandWorkLaunchModal({ open, identificator, nav, onClose }: Props) {
  const [handWork, setHandWork] = useState<HandWorkInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open || !identificator) return

    setLoading(true)
    setError('')

    api.getHandWork(identificator)
      .then(setHandWork)
      .catch(requestError => {
        setHandWork(null)
        setError(requestError instanceof Error ? requestError.message : 'Не удалось загрузить тренировку')
      })
      .finally(() => setLoading(false))
  }, [identificator, open])

  const closeModal = () => {
    onClose()
  }

  const startWork = () => {
    if (!identificator || !handWork) return
    haptic('selection')
    onClose()
    nav.push({
      name: 'work-confirm',
      config: {
        type: 'hand_work',
        handWorkId: identificator,
        workName: handWork.name,
      },
    })
  }

  return (
    <Modal
      open={open}
      onOpenChange={nextOpen => {
        if (!nextOpen) closeModal()
      }}
      snapPoints={[1]}
      modal
      header={<Modal.Header>Тренировка от преподавателя</Modal.Header>}
    >
      <div className="selection-modal__body">
        {loading && (
          <div className="modal-placeholder">
            <SectionCellsSkeleton rows={1} titleWidth="54%" subtitleWidth="32%" />
          </div>
        )}

        {!loading && handWork && (
          <div className="theory-document-modal__actions">
            <Banner
              type="section"
              callout="Задание от преподавателя"
              header={handWork.name}
              subheader={`Вопрос в тренировке: ${handWork.questions_count}`}
            />
            {/* <div style={{ display: 'grid', gap: 4, padding: '4px 2px 2px' }}>
              <Subheadline weight="2">Можно начать сразу</Subheadline>
              <Caption style={{ color: 'var(--tgui--hint_color)' }}>
                После старта откроется первый вопрос. Если у тебя уже есть другая незавершённая тренировка, приложение
                попросит подтвердить замену.
              </Caption>
            </div> */}
            <Button size="l" stretched onClick={startWork}>
              Начать тренировку
            </Button>
            <Button size="l" mode="gray" stretched onClick={closeModal}>
              Позже
            </Button>
          </div>
        )}

        {!loading && !handWork && (
          <div className="theory-document-modal__actions">
            <Banner
              type="section"
              header="Не удалось открыть тренировку"
              subheader={error || 'Проверь ссылку или обратись к преподавателю'}
            />
            <Button size="l" mode="gray" stretched onClick={closeModal}>
              Закрыть
            </Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
