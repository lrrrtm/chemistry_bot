import { useEffect, useState, type ComponentType } from 'react'
import { chemistryPlaceholderAnimation } from '../assets/chemistryPlaceholderAnimation'

interface Props {
  title: string
  description: string
  animationData?: object
}

type LottieComponent = ComponentType<{
  animationData: object
  loop?: boolean
  autoplay?: boolean
}>

export function AnimatedPlaceholder({ title, description, animationData = chemistryPlaceholderAnimation }: Props) {
  const [Lottie, setLottie] = useState<LottieComponent | null>(null)

  useEffect(() => {
    let mounted = true

    import('lottie-react')
      .then(module => {
        if (mounted) setLottie(() => module.default)
      })
      .catch(() => {
        if (mounted) setLottie(null)
      })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="state-placeholder">
      <div className="state-placeholder__animation" aria-hidden="true">
        {Lottie ? (
          <Lottie animationData={animationData} loop autoplay />
        ) : (
          <div className="app-skeleton-block" style={{ width: '100%', height: '100%', borderRadius: 24 }} />
        )}
      </div>
      <h2 className="state-placeholder__title">{title}</h2>
      <p className="state-placeholder__description">{description}</p>
    </div>
  )
}
