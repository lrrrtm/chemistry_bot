import { useEffect, useMemo, useState } from 'react'
import { Button, Caption, Cell, Input, List, Modal, Placeholder, Section, Subheadline } from '@telegram-apps/telegram-ui'
import { BookOpenText, ExternalLink, FileText, RotateCw } from 'lucide-react'
import { api, type TheoryDocument } from '../api'
import { SectionCellsSkeleton } from '../components/SkeletonScreens'
import { StatePlaceholder } from '../components/StatePlaceholder'
import { closeMiniApp, haptic, openTelegramUrl } from '../lib/telegram'

export function TheoryScreen() {
  const [query, setQuery] = useState('')
  const [documents, setDocuments] = useState<TheoryDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sendingId, setSendingId] = useState<number | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<TheoryDocument | null>(null)
  const [sendError, setSendError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => {
      setLoading(true)
      setError('')

      api.getTheoryDocuments(query, { signal: controller.signal })
        .then(setDocuments)
        .catch(requestError => {
          if (controller.signal.aborted) return
          const message = requestError instanceof Error ? requestError.message : 'Не удалось загрузить документы.'
          setDocuments([])
          setError(message)
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, 250)

    return () => {
      controller.abort()
      window.clearTimeout(timeoutId)
    }
  }, [query, reloadKey])

  const selectedMeta = useMemo(() => {
    if (!selectedDocument) return []
    return selectedDocument.tags_list?.filter(Boolean) ?? []
  }, [selectedDocument])

  const sendDocumentToChat = async (documentId: number) => {
    if (sendingId !== null) return

    setSendingId(documentId)
    haptic('impact')

    try {
      const result = await api.sendTheoryDocument(documentId)
      haptic('success')
      setSelectedDocument(null)
      openTelegramUrl(result.chat_url)
      window.setTimeout(() => closeMiniApp(), 120)
    } catch (requestError) {
      haptic('error')
      const message = requestError instanceof Error ? requestError.message : 'Не удалось отправить документ в чат.'
      setSendError(message)
    } finally {
      setSendingId(null)
    }
  }

  return (
    <List>
      <div style={{ padding: '12px 16px 8px' }}>
        <div className="app-input-shell">
          <Input
            value={query}
            className="app-wide-input"
            onChange={event => setQuery(event.target.value)}
            placeholder="Поиск по названию или тегу"
            before={<BookOpenText size={18} />}
          />
        </div>
      </div>

      {loading ? (
        <SectionCellsSkeleton rows={4} titleWidth="62%" subtitleWidth="44%" />
      ) : error ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
          <StatePlaceholder
            title="Не удалось загрузить документы"
            description={error}
            action={(
              <Button size="l" before={<RotateCw size={18} />} onClick={() => setReloadKey(previous => previous + 1)}>
                Повторить
              </Button>
            )}
          />
        </div>
      ) : documents.length === 0 ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
          <Placeholder
            header={query.trim() ? 'Ничего не найдено' : 'Документов пока нет'}
            description={
              query.trim()
                ? 'Попробуй изменить запрос поиска'
                : 'Когда преподаватель добавит материалы, они появятся здесь'
            }
          />
        </div>
      ) : (
        <Section header="Документы">
          {documents.map(document => {
            const tags = document.tags_list?.filter(Boolean).join(', ')

            return (
              <Cell
                key={document.id}
                multiline
                before={<FileText size={20} style={{ flexShrink: 0 }} />}
                subtitle={tags || undefined}
                onClick={() => {
                  haptic('selection')
                  setSelectedDocument(document)
                }}
              >
                <span className="theory-document__title">{document.title}</span>
              </Cell>
            )
          })}
        </Section>
      )}

      <Modal
        open={selectedDocument !== null}
        onOpenChange={open => {
          if (!open) setSelectedDocument(null)
        }}
        header={<Modal.Header>{selectedDocument?.title ?? 'Документ'}</Modal.Header>}
      >
        <div className="selection-modal__body">
          <div style={{ padding: '12px 16px 4px', display: 'grid', gap: 10 }}>
            <div style={{ display: 'grid', gap: 4 }}>
              <Caption style={{ color: 'var(--tgui--hint_color)' }}>Название документа</Caption>
              <Subheadline weight="2" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
                {selectedDocument?.title ?? '-'}
              </Subheadline>
            </div>

            <div style={{ display: 'grid', gap: 4 }}>
              <Caption style={{ color: 'var(--tgui--hint_color)' }}>Теги</Caption>
              <Subheadline weight="2" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
                {selectedMeta.length > 0 ? selectedMeta.join(', ') : 'Теги не указаны'}
              </Subheadline>
            </div>
          </div>

          <div className="theory-document-modal__actions">
            <Button
              size="l"
              stretched
              loading={selectedDocument !== null && sendingId === selectedDocument.id}
              disabled={!selectedDocument || sendingId !== null}
              onClick={() => selectedDocument && void sendDocumentToChat(selectedDocument.id)}
            >
              <span className="theory-document-modal__button">
                <ExternalLink size={18} />
                Открыть документ
              </span>
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        open={sendError !== null}
        onOpenChange={open => {
          if (!open) setSendError(null)
        }}
        header={<Modal.Header>Не удалось отправить</Modal.Header>}
      >
        <div className="selection-modal__body">
          <div className="modal-placeholder">
            <StatePlaceholder
              title="Документ не отправлен"
              description={sendError ?? undefined}
              action={(
                <Button size="l" onClick={() => setSendError(null)}>
                  Понятно
                </Button>
              )}
            />
          </div>
        </div>
      </Modal>
    </List>
  )
}
