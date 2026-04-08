import type { CSSProperties, ReactNode } from 'react'
import { Card, List, Section } from '@telegram-apps/telegram-ui'

function blockStyle(height: number, width: CSSProperties['width'], radius = 12): CSSProperties {
  return {
    display: 'block',
    height,
    width,
    maxWidth: '100%',
    minWidth: 0,
    borderRadius: radius,
  }
}

function SkeletonBlock({
  height,
  width = '100%',
  radius = 12,
  style,
}: {
  height: number
  width?: CSSProperties['width']
  radius?: number
  style?: CSSProperties
}) {
  return <div className="app-skeleton-block" style={{ ...blockStyle(height, width, radius), ...style }} />
}

function SkeletonCircle({ size = 40 }: { size?: number }) {
  return <SkeletonBlock height={size} width={size} radius={size / 2} />
}

function SkeletonCell({
  before,
  after,
  titleWidth = '58%',
  subtitleWidth = '42%',
}: {
  before?: ReactNode
  after?: ReactNode
  titleWidth?: CSSProperties['width']
  subtitleWidth?: CSSProperties['width'] | null
}) {
  return (
    <div className="app-skeleton-cell">
      {before && <div className="app-skeleton-cell__before">{before}</div>}
      <div className="app-skeleton-cell__content">
        <SkeletonBlock height={20} width={titleWidth} radius={10} />
        {subtitleWidth != null && <SkeletonBlock height={14} width={subtitleWidth} radius={8} />}
      </div>
      {after && <div className="app-skeleton-cell__after">{after}</div>}
    </div>
  )
}

function SectionHeaderSkeleton({ width = 132 }: { width?: number }) {
  return (
    <div style={{ padding: '16px 16px 8px' }}>
      <SkeletonBlock height={18} width={width} radius={9} />
    </div>
  )
}

function ScoreBadgeSkeleton() {
  return <SkeletonBlock height={32} width={88} radius={18} />
}

export function HomeScreenSkeleton() {
  return (
    <List>
      <div style={{ padding: '0 16px 8px' }}>
        <SkeletonBlock height={88} radius={16} />
      </div>
      <div style={{ padding: '4px 16px 8px' }}>
        <SkeletonBlock height={42} radius={18} />
      </div>

      <SectionHeaderSkeleton width={168} />
      <Section>
        <SkeletonCell before={<SkeletonCircle size={22} />} titleWidth="72%" subtitleWidth="40%" />
        <SkeletonCell before={<SkeletonCircle size={22} />} titleWidth="64%" subtitleWidth="34%" />
      </Section>
    </List>
  )
}

export function ProfileScreenSkeleton() {
  return (
    <List>
      <Section>
        <SkeletonCell before={<SkeletonCircle size={44} />} titleWidth={140} subtitleWidth={92} />
      </Section>

      <SectionHeaderSkeleton width={188} />
      <Section>
        {Array.from({ length: 3 }, (_, index) => (
          <div key={index}>
            <SkeletonCell
              before={<SkeletonCircle size={20} />}
              after={<ScoreBadgeSkeleton />}
              titleWidth={index === 1 ? '52%' : '38%'}
              subtitleWidth="44%"
            />
            <div style={{ padding: '2px 16px 8px' }}>
              <SkeletonBlock height={4} radius={2} />
            </div>
          </div>
        ))}
      </Section>
    </List>
  )
}

export function TopicSelectScreenSkeleton() {
  return (
    <List>
      <SectionHeaderSkeleton width={154} />
      <Section>
        {Array.from({ length: 6 }, (_, index) => (
          <SkeletonCell
            key={index}
            titleWidth={index % 2 === 0 ? '48%' : '58%'}
            subtitleWidth={null}
            after={<SkeletonBlock height={14} width={52} radius={8} />}
          />
        ))}
      </Section>
    </List>
  )
}

export function WorkResultsScreenSkeleton() {
  return (
    <List>
      <Section>
        <SkeletonCell titleWidth="44%" subtitleWidth={92} />
      </Section>

      <SectionHeaderSkeleton width={76} />
      <Section>
        <div style={{ padding: '12px 16px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <SkeletonBlock height={44} width={94} radius={16} />
              <SkeletonBlock height={14} width={126} radius={8} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <SkeletonBlock height={18} width={28} radius={10} />
              <SkeletonBlock height={18} width={28} radius={10} />
              <SkeletonBlock height={18} width={28} radius={10} />
            </div>
          </div>
          <SkeletonBlock height={8} radius={6} />
        </div>
        <SkeletonCell before={<SkeletonCircle size={18} />} titleWidth="36%" subtitleWidth="18%" />
        <SkeletonCell before={<SkeletonCircle size={18} />} titleWidth="42%" subtitleWidth="22%" />
      </Section>

      <SectionHeaderSkeleton width={184} />
      <Section>
        {Array.from({ length: 2 }, (_, index) => (
          <div key={index} style={{ padding: '0 16px 12px' }}>
            <Card style={{ width: '100%', boxSizing: 'border-box', padding: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <SkeletonCircle size={16} />
                <SkeletonBlock height={14} width={76} radius={8} style={{ flex: 1 }} />
                <SkeletonBlock height={14} width={44} radius={8} />
              </div>
              <SkeletonBlock height={18} width="92%" radius={10} style={{ marginBottom: 10 }} />
              <SkeletonBlock height={18} width={index === 0 ? '72%' : '64%'} radius={10} style={{ marginBottom: 12 }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px', padding: '8px 10px', borderRadius: 14, background: 'var(--tgui--tertiary_bg_color)' }}>
                <SkeletonBlock height={12} width="54%" radius={7} />
                <SkeletonBlock height={12} width="58%" radius={7} />
                <SkeletonBlock height={16} width="78%" radius={8} />
                <SkeletonBlock height={16} width="74%" radius={8} />
              </div>
            </Card>
          </div>
        ))}
      </Section>
    </List>
  )
}

export function QuestionScreenSkeleton() {
  return (
    <div className="question-layout">
      <div className="question-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <SkeletonBlock height={4} radius={6} style={{ flex: 1 }} />
          <SkeletonBlock height={18} width={52} radius={8} />
        </div>
      </div>

      <div className="question-body">
        <Card style={{ width: '100%', boxSizing: 'border-box', padding: 16, marginBottom: 12 }}>
          <SkeletonBlock height={26} width="90%" radius={12} style={{ marginBottom: 14 }} />
          <SkeletonBlock height={18} width="96%" radius={10} style={{ marginBottom: 10 }} />
          <SkeletonBlock height={18} width="92%" radius={10} style={{ marginBottom: 10 }} />
          <SkeletonBlock height={18} width="86%" radius={10} style={{ marginBottom: 10 }} />
          <SkeletonBlock height={18} width="78%" radius={10} />
        </Card>
      </div>

      <div className="question-footer">
        <SkeletonBlock height={50} radius={14} />
        <div className="question-actions">
          <SkeletonBlock height={50} radius={14} style={{ flex: 1 }} />
          <SkeletonBlock height={50} width={52} radius={14} />
        </div>
      </div>
    </div>
  )
}

export function HandWorkSkeletonCell() {
  return <SkeletonCell before={<SkeletonCircle size={22} />} titleWidth="48%" subtitleWidth="24%" />
}

export function SectionCellsSkeleton({
  rows = 1,
  titleWidth = '48%',
  subtitleWidth = '28%',
}: {
  rows?: number
  titleWidth?: CSSProperties['width']
  subtitleWidth?: CSSProperties['width'] | null
}) {
  return (
    <Section>
      {Array.from({ length: rows }, (_, index) => (
        <SkeletonCell key={index} titleWidth={titleWidth} subtitleWidth={subtitleWidth} />
      ))}
    </Section>
  )
}
