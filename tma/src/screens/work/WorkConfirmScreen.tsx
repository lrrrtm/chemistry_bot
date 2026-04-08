import { useCallback, useMemo, useState } from 'react'
import { Banner, Blockquote, Button, Caption, Cell, List, Modal, Section, Subheadline } from '@telegram-apps/telegram-ui'
import { Brain, ClipboardList, FileText } from 'lucide-react'

import { type CachedData } from '../../App'
import { api, type StudentProfile } from '../../api'
import { SectionCellsSkeleton } from '../../components/SkeletonScreens'
import { type NavActions, type WorkConfig } from '../../lib/navigation'
import { haptic } from '../../lib/telegram'

interface Props {
  nav: NavActions
  config: WorkConfig
  cache: CachedData
  profile: StudentProfile | null
}

type PdfDelivery = 'none' | 'telegram' | 'download'

const typeLabel: Record<WorkConfig['type'], string> = {
  ege: 'КИМ ЕГЭ',
  topic: 'Персональная тренировка',
  hand_work: 'Работа от преподавателя',
}

const typeDesc: Record<WorkConfig['type'], string> = {
  ege: '34 вопроса в формате реального ЕГЭ',
  topic: '20 вопросов по выбранной теме',
  hand_work: 'Набор вопросов от преподавателя',
}

function TypeIcon({ type }: { type: WorkConfig['type'] }) {
  if (type === 'ege') return <FileText size={22} style={{ flexShrink: 0 }} />
  if (type === 'topic') return <Brain size={22} style={{ flexShrink: 0 }} />
  return <ClipboardList size={22} style={{ flexShrink: 0 }} />
}

function activeWorkLabel(type: WorkConfig['type']) {
  if (type === 'ege') return 'Незавершённый вариант ЕГЭ'
  if (type === 'topic') return 'Незавершённая тренировка по теме'
  return 'Незавершённая работа от преподавателя'
}

export function WorkConfirmScreen({ nav, config, cache, profile }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [replaceModalOpen, setReplaceModalOpen] = useState(false)
  const [pdfModalOpen, setPdfModalOpen] = useState(false)
  const [pendingPdfDelivery, setPendingPdfDelivery] = useState<PdfDelivery>('none')
  const checkingActiveWork = cache.activeWork === undefined
  const hasActiveWork = Boolean(cache.activeWork)
  const isTelegramSession = profile?.auth_mode === 'telegram'

  const startButtonLabel = useMemo(
    () => (checkingActiveWork ? 'Проверяем текущую тренировку...' : 'Начать тренировку'),
    [checkingActiveWork],
  )

  const createWork = useCallback(async (replaceActive: boolean, pdfDelivery: PdfDelivery) => {
    if (loading) return

    setLoading(true)
    setError('')
    haptic('impact')

    try {
      const { work_id } = await api.createWork({
        work_type: config.type,
        topic_id: config.topicId,
        hand_work_id: config.handWorkId,
        replace_active: replaceActive,
        pdf_delivery: pdfDelivery,
      })

      if (pdfDelivery === 'download') {
        void api.downloadWorkPdf(work_id).catch(() => {
          haptic('error')
        })
      }

      haptic('success')
      cache.refreshActive()
      setPdfModalOpen(false)
      setReplaceModalOpen(false)
      nav.replace({ name: 'question', workId: work_id })
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Не удалось создать тренировку. Попробуй ещё раз.'

      setError(message)
      haptic('error')
      setLoading(false)
    }
  }, [cache, config.handWorkId, config.topicId, config.type, loading, nav])

  const startWithDelivery = useCallback((pdfDelivery: PdfDelivery) => {
    if (loading || checkingActiveWork) return
    setPendingPdfDelivery(pdfDelivery)
    setPdfModalOpen(false)

    if (hasActiveWork) {
      haptic('selection')
      setReplaceModalOpen(true)
      return
    }

    void createWork(false, pdfDelivery)
  }, [checkingActiveWork, createWork, hasActiveWork, loading])

  const handleStart = useCallback(() => {
    if (loading || checkingActiveWork) return
    haptic('selection')
    setPdfModalOpen(true)
  }, [checkingActiveWork, loading])

  return (
    <div className="screen-layout">
      <div className="screen-layout__body">
        <List>
          <Section header="Описание тренировки">
            <Cell before={<TypeIcon type={config.type} />} subtitle={typeDesc[config.type]}>
              {config.workName || typeLabel[config.type]}
            </Cell>
            {config.topicName && config.type === 'topic' && (
              <Cell subtitle="Выбранная тема">{config.topicName}</Cell>
            )}
          </Section>

          {cache.activeWork && (
            <div style={{ padding: '0 16px 8px' }}>
              <Blockquote type="other" topRightIcon={null}>
                <div style={{ display: 'grid', gap: 4 }}>
                  <Subheadline weight="2">Потребуется подтверждение</Subheadline>
                  <Caption style={{ color: 'var(--tgui--hint_color)' }}>
                    {`${activeWorkLabel(cache.activeWork.work_type)}. Уже отвечено ${cache.activeWork.answered} из ${cache.activeWork.total} вопросов. Новая тренировка заменит текущую.`}
                  </Caption>
                </div>
              </Blockquote>
            </div>
          )}

          {error && <Banner type="section" header="Ошибка" subheader={error} />}

          {(loading || checkingActiveWork) && <SectionCellsSkeleton titleWidth="42%" subtitleWidth="34%" />}
        </List>
      </div>

      {!replaceModalOpen && !pdfModalOpen && (
        <div className="screen-footer">
          <Button
            size="l"
            stretched
            disabled={loading || checkingActiveWork}
            loading={loading || checkingActiveWork}
            onClick={() => void handleStart()}
          >
            {startButtonLabel}
          </Button>
        </div>
      )}

      <Modal
        open={pdfModalOpen}
        onOpenChange={setPdfModalOpen}
        snapPoints={[1]}
        modal
        header={<Modal.Header>Подготовить PDF с заданиями?</Modal.Header>}
      >
        <div className="selection-modal__body">
          <div className="theory-document-modal__actions">
            <div style={{ display: 'grid', gap: 4, padding: '4px 2px 2px' }}>
              <Subheadline weight="2">Файл с заданиями</Subheadline>
              <Caption style={{ color: 'var(--tgui--hint_color)' }}>
                {isTelegramSession
                  ? 'В нём будут все задания вместе с изображениями, ты сможешь распечатать его или открыть на компьютере'
                  : 'В нём будут все задания вместе с изображениями, ты сможешь распечатать его или открыть на компьютере'}
              </Caption>
            </div>
            <Button
              size="l"
              stretched
              disabled={loading}
              onClick={() => void startWithDelivery(isTelegramSession ? 'telegram' : 'download')}
            >
              Да, файл нужен
            </Button>
            <Button size="l" mode="gray" stretched disabled={loading} onClick={() => void startWithDelivery('none')}>
              Нет, файл не нужен
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        open={replaceModalOpen}
        onOpenChange={setReplaceModalOpen}
        snapPoints={[1]}
        modal
        header={<Modal.Header>Заменить текущую тренировку?</Modal.Header>}
      >
        <div className="selection-modal__body">
          <div className="theory-document-modal__actions">
            <div style={{ display: 'grid', gap: 4, padding: '4px 2px 2px' }}>
              <Subheadline weight="2">Текущая тренировка будет удалена</Subheadline>
              <Caption style={{ color: 'var(--tgui--hint_color)' }}>
                У тебя уже есть активная тренировка. Если начнёшь новую, прогресс в текущей будет потерян.
              </Caption>
            </div>
            <Button
              size="l"
              stretched
              disabled={loading}
              loading={loading}
              onClick={() => void createWork(true, pendingPdfDelivery)}
            >
              Начать новую тренировку
            </Button>
            <Button
              size="l"
              mode="gray"
              stretched
              disabled={loading}
              onClick={() => {
                setReplaceModalOpen(false)
                setPdfModalOpen(false)
              }}
            >
              Остаться в текущей
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
