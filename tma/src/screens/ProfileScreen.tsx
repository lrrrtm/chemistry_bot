import { useEffect, useState, type CSSProperties } from 'react'
import { Avatar, Badge, Button, Cell, List, Placeholder, Progress, Section } from '@telegram-apps/telegram-ui'
import { Brain, ClipboardList, FileText, Link as LinkIcon, User } from 'lucide-react'

import { type CachedData } from '../App'
import { api, type StudentProfile, type WorkListItem } from '../api'
import { ProfileScreenSkeleton } from '../components/SkeletonScreens'
import { formatLocalDate } from '../lib/datetime'
import { type NavActions } from '../lib/navigation'
import { getTgUser, haptic, openExternalUrl, openTelegramUrl } from '../lib/telegram'

interface Props {
  nav: NavActions
  cache: CachedData
  profile: StudentProfile | null
  onProfileRefresh: (profile: StudentProfile) => void
}

function WorkTypeIcon({ t }: { t: WorkListItem['work_type'] }) {
  if (t === 'ege') return <FileText size={20} style={{ flexShrink: 0 }} />
  if (t === 'topic') return <Brain size={20} style={{ flexShrink: 0 }} />
  return <ClipboardList size={20} style={{ flexShrink: 0 }} />
}

function workTypeName(t: WorkListItem['work_type']) {
  if (t === 'ege') return 'КИМ ЕГЭ'
  if (t === 'topic') return 'Персональная'
  return 'От преподавателя'
}

function formatDate(iso: string) {
  return formatLocalDate(iso, {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}

export function ProfileScreen({ nav, cache, profile, onProfileRefresh }: Props) {
  const { works, refreshWorks } = cache
  const tgUser = getTgUser()
  const [linkLoading, setLinkLoading] = useState(false)
  const [webAccessLoading, setWebAccessLoading] = useState(false)
  const [webRevokeLoading, setWebRevokeLoading] = useState(false)
  const [linkError, setLinkError] = useState('')
  const [webAccessError, setWebAccessError] = useState('')
  const [confirmWebRevoke, setConfirmWebRevoke] = useState(false)

  useEffect(() => {
    if (works === undefined) refreshWorks()
  }, [refreshWorks, works])

  if (works === undefined) {
    return <ProfileScreenSkeleton />
  }

  const displayName = tgUser ? `${tgUser.first_name}${tgUser.last_name ? ` ${tgUser.last_name}` : ''}` : profile?.name ?? 'Профиль'
  const subtitle = tgUser?.username ? `@${tgUser.username}` : profile?.username ? `@${profile.username}` : undefined
  const avatarSrc = tgUser?.photo_url || (profile?.telegram_id ? api.imageUrl.user(profile.telegram_id) : undefined)

  return (
    <List>
      <Section>
        <Cell
          before={(
            <Avatar
              size={40}
              src={avatarSrc}
              alt={displayName}
              acronym={(tgUser?.first_name ?? profile?.name ?? 'U').slice(0, 1)}
              fallbackIcon={<User size={22} />}
            />
          )}
          subtitle={subtitle}
        >
          {displayName}
        </Cell>
      </Section>

      {profile?.auth_mode === 'web' && (
        <Section header="Telegram">
          {profile.telegram_linked ? (
            <Cell before={<LinkIcon size={20} style={{ flexShrink: 0 }} />}>
              Профиль привязан к Telegram
            </Cell>
          ) : (
            <div style={{ padding: '0 16px 12px' }}>
              <Button
                size="m"
                stretched
                loading={linkLoading}
                onClick={() => {
                  setLinkLoading(true)
                  setLinkError('')
                  api.startTelegramLink()
                    .then(result => {
                      if (result.linked) {
                        onProfileRefresh({ ...profile, telegram_linked: true })
                        return
                      }
                      if (result.bot_url) {
                        openTelegramUrl(result.bot_url)
                      }
                    })
                    .catch((error: Error) => {
                      setLinkError(error.message || 'Не удалось начать привязку Telegram')
                      haptic('error')
                    })
                    .finally(() => setLinkLoading(false))
                }}
              >
                Привязать Telegram
              </Button>
              <div style={{ color: 'var(--tgui--hint_color)', fontSize: 13, marginTop: 8 }}>
                Нажми кнопку, открой бота и подтверди привязку. После этого этим же профилем можно будет пользоваться в Telegram.
              </div>
              {linkError && (
                <div style={{ color: 'var(--tgui--destructive_text_color, #e8361e)', fontSize: 13, marginTop: 8 }}>
                  {linkError}
                </div>
              )}
            </div>
          )}
        </Section>
      )}

      {profile?.auth_mode === 'telegram' && (
        <Section header="Веб-доступ">
          {profile.has_web_credentials ? (
            <div style={{ padding: '0 16px 12px' }}>
              <Cell before={<LinkIcon size={20} style={{ flexShrink: 0 }} />}>
                Вход в веб уже настроен
              </Cell>
              <div style={{ color: 'var(--tgui--hint_color)', fontSize: 13, marginTop: 8, padding: '0 4px' }}>
                Если отключить веб-доступ, тебе придётся заново задавать логин и пароль
              </div>
              {confirmWebRevoke ? (
                <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
                  <Button
                    size="m"
                    stretched
                    loading={webRevokeLoading}
                    onClick={() => {
                      setWebRevokeLoading(true)
                      setWebAccessError('')
                      api.revokeWebAccess()
                        .then(result => {
                          onProfileRefresh(result)
                          setConfirmWebRevoke(false)
                          haptic('success')
                        })
                        .catch((error: Error) => {
                          setWebAccessError(error.message || 'Не удалось отключить веб-доступ')
                          haptic('error')
                        })
                        .finally(() => setWebRevokeLoading(false))
                    }}
                  >
                    Подтвердить отключение
                  </Button>
                  <Button
                    size="m"
                    stretched
                    disabled={webRevokeLoading}
                    onClick={() => {
                      setConfirmWebRevoke(false)
                      setWebAccessError('')
                    }}
                  >
                    Отмена
                  </Button>
                </div>
              ) : (
                <div style={{ marginTop: 12 }}>
                  <Button
                    size="m"
                    stretched
                    onClick={() => {
                      setConfirmWebRevoke(true)
                      setWebAccessError('')
                    }}
                  >
                    Отключить веб-доступ
                  </Button>
                </div>
              )}
              {webAccessError && (
                <div style={{ color: 'var(--tgui--destructive_text_color, #e8361e)', fontSize: 13, marginTop: 8 }}>
                  {webAccessError}
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: '0 16px 12px' }}>
              <Button
                size="m"
                stretched
                loading={webAccessLoading}
                onClick={() => {
                  setWebAccessLoading(true)
                  setWebAccessError('')
                  api.startWebAccess()
                    .then(result => {
                      openExternalUrl(result.url)
                    })
                    .catch((error: Error) => {
                      setWebAccessError(error.message || 'Не удалось открыть веб-доступ')
                      haptic('error')
                    })
                    .finally(() => setWebAccessLoading(false))
                }}
              >
                Настроить вход в веб
              </Button>
              <div style={{ color: 'var(--tgui--hint_color)', fontSize: 13, marginTop: 8 }}>
                Откроем веб-версию приложения, которой можно пользоваться, если Telegram работает нестабильно
              </div>
              {webAccessError && (
                <div style={{ color: 'var(--tgui--destructive_text_color, #e8361e)', fontSize: 13, marginTop: 8 }}>
                  {webAccessError}
                </div>
              )}
            </div>
          )}
        </Section>
      )}

      <Section header="История тренировок">
        {works.length === 0 && (
          <div style={{ padding: '16px 0' }}>
            <Placeholder description="Ты ещё не завершил ни одной тренировки" />
          </div>
        )}

        {works.map(work => {
          const percent = work.max_mark > 0 ? Math.round((work.final_mark / work.max_mark) * 100) : 0
          const scoreColor = percent >= 70 ? '#31b545' : percent >= 40 ? '#f5a623' : '#e8361e'

          return (
            <div key={work.id}>
              <Cell
                before={<WorkTypeIcon t={work.work_type} />}
                subtitle={`${formatDate(work.end_datetime)}`}
                after={<Badge type="number" mode="primary">{work.final_mark}/{work.max_mark}</Badge>}
                onClick={() => {
                  haptic('selection')
                  nav.push({ name: 'work-results', workId: work.id })
                }}
              >
                {work.name || workTypeName(work.work_type)}
              </Cell>
              <div style={{ padding: '2px 16px 8px' }}>
                <Progress value={percent} style={{ '--tgui--progress_bar_fill_color': scoreColor } as CSSProperties} />
              </div>
            </div>
          )
        })}
      </Section>
    </List>
  )
}
