import type { ReactNode } from 'react'

interface Props {
  title?: string
  description?: string
  action?: ReactNode
}

export function StatePlaceholder({ title, description, action }: Props) {
  return (
    <div className="state-placeholder">
      {title && <h2 className="state-placeholder__title">{title}</h2>}
      {description && <p className="state-placeholder__description">{description}</p>}
      {action && <div className="state-placeholder__actions">{action}</div>}
    </div>
  )
}
