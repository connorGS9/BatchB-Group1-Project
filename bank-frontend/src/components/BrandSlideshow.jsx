import { useEffect, useState } from 'react'

// Photos that sit behind the green brand wash on the login panel.
// Free, hotlink-friendly Lorem Picsum images (Unsplash-sourced). To use real
// branch/brand photography later, drop files in /public and swap these for
// e.g. '/slides/branch.jpg' — nothing else needs to change.
const SLIDES = [
  'https://picsum.photos/id/1018/1200/1600',
  'https://picsum.photos/id/1015/1200/1600',
  'https://picsum.photos/id/1043/1200/1600',
  'https://picsum.photos/id/1036/1200/1600',
]

const INTERVAL_MS = 6000
const MOTION_QUERY = '(prefers-reduced-motion: reduce)'

const motionMedia = () =>
  typeof window !== 'undefined' && window.matchMedia ? window.matchMedia(MOTION_QUERY) : null

export default function BrandSlideshow() {
  const [index, setIndex] = useState(0)
  const [reduced, setReduced] = useState(() => motionMedia()?.matches ?? false)

  // Track the reduced-motion preference live, not just at mount.
  useEffect(() => {
    const mq = motionMedia()
    if (!mq) return
    const onChange = (e) => setReduced(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // Auto-advance, unless the user has asked for reduced motion.
  useEffect(() => {
    if (reduced || SLIDES.length < 2) {
      setIndex(0)
      return
    }
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % SLIDES.length)
    }, INTERVAL_MS)
    return () => clearInterval(timer)
  }, [reduced])

  return (
    <div className="slideshow">
      <div className="slides">
        {SLIDES.map((src, i) => (
          <div
            key={src}
            className={i === index ? 'slide active' : 'slide'}
            style={{ backgroundImage: `url(${src})` }}
          />
        ))}
      </div>
      <div className="slide-wash" />
      <div className="slide-dots">
        {SLIDES.map((src, i) => (
          <span key={src} className={i === index ? 'dot on' : 'dot'} />
        ))}
      </div>
    </div>
  )
}
