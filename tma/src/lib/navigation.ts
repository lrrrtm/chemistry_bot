export type TabName = 'home' | 'theory' | 'profile'

export type WorkType = 'ege' | 'topic' | 'hand_work'

export interface WorkConfig {
  type: WorkType
  topicId?: number
  handWorkId?: string   // hand_work identificator string
  topicName?: string
  workName?: string
}

export type Screen =
  | { name: 'onboarding' }
  | { name: 'home' }
  | { name: 'theory' }
  | { name: 'profile' }
  | { name: 'work-type'; handWorkId?: string }
  | { name: 'topic-select' }
  | { name: 'work-confirm'; config: WorkConfig }
  | { name: 'question'; workId: number }
  | { name: 'skipped'; workId: number; count: number }
  | { name: 'work-complete'; workId: number }
  | { name: 'work-results'; workId: number }

export const TAB_SCREENS: string[] = ['home', 'theory', 'profile']

export interface NavActions {
  push: (screen: Screen) => void
  pop: () => void
  replace: (screen: Screen) => void
  goToTab: (tab: TabName) => void
}
