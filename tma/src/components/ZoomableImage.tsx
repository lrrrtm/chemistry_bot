import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Caption } from '@telegram-apps/telegram-ui'
import { ImageOff, ZoomIn } from 'lucide-react'
import { haptic, setBackOverride } from '../lib/telegram'

interface Props {
  src: string
  alt?: string
  placeholderHeight?: number
  marginTop?: number
  marginBottom?: number
  errorText?: string
}

type ZoomPanModule = typeof import('react-zoom-pan-pinch')

export function ZoomableImage({
  src,
  alt = '',
  placeholderHeight = 180,
  marginTop = 0,
  marginBottom = 10,
  errorText = 'Не удалось загрузить изображение',
}: Props) {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [open, setOpen] = useState(false)
  const [zoomPanModule, setZoomPanModule] = useState<ZoomPanModule | null>(null)
  const hasHistoryEntryRef = useRef(false)

  useEffect(() => {
    setStatus('loading')
  }, [src])

  useEffect(() => {
    if (!open || zoomPanModule) return

    let mounted = true
    import('react-zoom-pan-pinch')
      .then(module => {
        if (mounted) setZoomPanModule(module)
      })
      .catch(() => {
        if (mounted) setZoomPanModule(null)
      })

    return () => {
      mounted = false
    }
  }, [open, zoomPanModule])

  useEffect(() => {
    if (!open) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeViewer(false)
    }

    const handlePopState = () => {
      hasHistoryEntryRef.current = false
      setOpen(false)
      setBackOverride(null)
    }

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.history.pushState({ imageLightbox: true }, '')
    hasHistoryEntryRef.current = true
    setBackOverride(() => {
      closeViewer(true)
      return true
    })
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('popstate', handlePopState)

    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('popstate', handlePopState)
      setBackOverride(null)
    }
  }, [open])

  const openViewer = () => {
    if (status !== 'ready') return
    haptic('selection')
    setOpen(true)
  }

  const closeViewer = (viaBack = false) => {
    haptic('selection')
    if (!open) return

    if (hasHistoryEntryRef.current && !viaBack) {
      hasHistoryEntryRef.current = false
      window.history.back()
      return
    }

    hasHistoryEntryRef.current = false
    setOpen(false)
    setBackOverride(null)
  }

  const imageNode = (
    <button
      type="button"
      className="zoomable-image"
      style={{
        marginTop,
        marginBottom,
        minHeight: status === 'ready' ? undefined : placeholderHeight,
      }}
      onClick={openViewer}
      disabled={status !== 'ready'}
    >
      {status !== 'ready' && (
        <div className="zoomable-image__placeholder">
          {status === 'loading' ? (
            <div className="app-skeleton-block" style={{ width: '100%', height: placeholderHeight, borderRadius: 12 }} />
          ) : (
            <div className="zoomable-image__error">
              <ImageOff size={22} />
              <Caption>{errorText}</Caption>
            </div>
          )}
        </div>
      )}

      <img
        key={src}
        src={src}
        alt={alt}
        className="zoomable-image__img"
        style={{ display: status === 'ready' ? 'block' : 'none' }}
        onLoad={() => setStatus('ready')}
        onError={() => setStatus('error')}
      />

      {status === 'ready' && (
        <span className="zoomable-image__badge">
          <ZoomIn size={16} />
        </span>
      )}
    </button>
  )

  if (!open || typeof document === 'undefined') {
    return imageNode
  }

  const TransformWrapper = zoomPanModule?.TransformWrapper
  const TransformComponent = zoomPanModule?.TransformComponent

  return (
    <>
      {imageNode}
      {createPortal(
        <div className="image-lightbox" onClick={() => closeViewer()}>
          <div className="image-lightbox__surface" onClick={event => event.stopPropagation()}>
            {TransformWrapper && TransformComponent ? (
              <TransformWrapper
                initialScale={1}
                minScale={1}
                maxScale={6}
                centerOnInit
                centerZoomedOut
                limitToBounds={false}
                alignmentAnimation={{ disabled: true }}
                smooth
                doubleClick={{ mode: 'zoomIn', step: 1.2 }}
                pinch={{ step: 5 }}
                wheel={{ step: 0.15 }}
              >
                <TransformComponent
                  wrapperClass="image-lightbox__transform"
                  contentClass="image-lightbox__content"
                  wrapperStyle={{
                    width: '100%',
                    height: '100%',
                    overflow: 'visible',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  contentStyle={{
                    width: '100%',
                    height: '100%',
                    overflow: 'visible',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <img src={src} alt={alt} className="image-lightbox__img" />
                </TransformComponent>
              </TransformWrapper>
            ) : (
              <div className="image-lightbox__content">
                <div className="app-skeleton-block" style={{ width: '100%', height: '100%', borderRadius: 24 }} />
              </div>
            )}
          </div>
        </div>,
        document.body,
      )}
    </>
  )
}
