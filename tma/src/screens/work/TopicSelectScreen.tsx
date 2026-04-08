import { useCallback, useEffect, useMemo, useState } from 'react'
import { Button, Cell, List, Modal, Placeholder, Section } from '@telegram-apps/telegram-ui'
import { ChevronRight, FolderOpen, Layers3, RotateCw } from 'lucide-react'
import { api, type Topic as ApiTopic } from '../../api'
import { StatePlaceholder } from '../../components/StatePlaceholder'
import { TopicSelectScreenSkeleton } from '../../components/SkeletonScreens'
import { type NavActions } from '../../lib/navigation'
import { haptic, setBackOverride } from '../../lib/telegram'

interface Props {
  nav: NavActions
}

function sortTopics(topics: ApiTopic[]) {
  return [...topics].sort((a, b) => {
    const left = parseInt(a.name, 10)
    const right = parseInt(b.name, 10)
    return !Number.isNaN(left) && !Number.isNaN(right) ? left - right : a.name.localeCompare(b.name, 'ru')
  })
}

export function TopicSelectScreen({ nav }: Props) {
  const [topics, setTopics] = useState<ApiTopic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [volumeModalOpen, setVolumeModalOpen] = useState(false)
  const [topicModalOpen, setTopicModalOpen] = useState(false)
  const [selectedVolume, setSelectedVolume] = useState<string | null>(null)

  const loadTopics = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const nextTopics = await api.getTopics()
      setTopics(nextTopics)
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Не удалось загрузить темы.'
      setTopics([])
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadTopics()
  }, [loadTopics])

  useEffect(() => {
    if (!topicModalOpen) {
      setBackOverride(null)
      return () => setBackOverride(null)
    }

    setBackOverride(() => {
      haptic('selection')
      setTopicModalOpen(false)
      return true
    })

    return () => setBackOverride(null)
  }, [topicModalOpen])

  const volumes = useMemo(() => [...new Set(topics.map(topic => topic.volume))], [topics])
  const selectedTopics = useMemo(
    () => sortTopics(topics.filter(topic => topic.volume === selectedVolume)),
    [topics, selectedVolume],
  )

  const handleOpenSelection = () => {
    haptic('selection')
    setVolumeModalOpen(true)
    setTopicModalOpen(Boolean(selectedVolume))
  }

  const handleSelectVolume = (volume: string) => {
    haptic('selection')
    setSelectedVolume(volume)
    setTopicModalOpen(true)
  }

  const handleSelectTopic = (topic: ApiTopic) => {
    haptic('selection')
    setTopicModalOpen(false)
    setVolumeModalOpen(false)
    nav.push({
      name: 'work-confirm',
      config: { type: 'topic', topicId: topic.id, topicName: topic.name, workName: topic.name },
    })
  }

  if (loading) {
    return <TopicSelectScreenSkeleton />
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100%', padding: '24px 16px' }}>
        <StatePlaceholder
          title="Не удалось загрузить темы"
          description={error}
          action={(
            <Button size="l" before={<RotateCw size={18} />} onClick={() => void loadTopics()}>
              Повторить
            </Button>
          )}
        />
      </div>
    )
  }

  return (
    <>
      <List>
        <Section header="Персональная тренировка">
          <Cell
            multiline
            before={<Layers3 size={20} style={{ flexShrink: 0 }} />}
            after={<ChevronRight size={18} style={{ color: 'var(--tgui--hint_color)', flexShrink: 0 }} />}
            subtitle={selectedVolume ? `Раздел: ${selectedVolume}` : 'Сначала выбери раздел, затем тему'}
            onClick={handleOpenSelection}
          >
            Выбрать тему
          </Cell>
        </Section>
      </List>

      <Modal
        open={volumeModalOpen}
        onOpenChange={open => {
          setVolumeModalOpen(open)
          if (!open) {
            setTopicModalOpen(false)
          }
        }}
        snapPoints={[1]}
        modal
        header={<Modal.Header>Выбери раздел</Modal.Header>}
      >
        <div className="selection-modal__body">
          <Section>
            {volumes.map(volume => {
              const topicsCount = topics.filter(topic => topic.volume === volume).length

              return (
                <Cell
                  key={volume}
                  multiline
                  before={<FolderOpen size={20} style={{ flexShrink: 0 }} />}
                  after={<span className="selection-modal__meta">{topicsCount} тем</span>}
                  onClick={() => handleSelectVolume(volume)}
                >
                  {volume}
                </Cell>
              )
            })}
          </Section>

          <Modal
            open={topicModalOpen}
            onOpenChange={open => setTopicModalOpen(open)}
            snapPoints={[1]}
            modal
            nested
            header={<Modal.Header>{selectedVolume ?? 'Выбери тему'}</Modal.Header>}
          >
            <div className="selection-modal__body">
              {selectedTopics.length === 0 ? (
                <div style={{ padding: '24px 16px' }}>
                  <Placeholder
                    header="Тем пока нет"
                    description="Для этого раздела ещё не добавлены темы"
                  />
                </div>
              ) : (
                <Section>
                  {selectedTopics.map(topic => (
                    <Cell
                      key={topic.id}
                      multiline
                      after={<ChevronRight size={18} style={{ color: 'var(--tgui--hint_color)', flexShrink: 0 }} />}
                      onClick={() => handleSelectTopic(topic)}
                    >
                      {topic.name}
                    </Cell>
                  ))}
                </Section>
              )}
            </div>
          </Modal>
        </div>
      </Modal>
    </>
  )
}
