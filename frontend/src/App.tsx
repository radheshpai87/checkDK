import { useEffect, useRef } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Installation from './components/Installation'
import Usage from './components/Usage'
import Footer from './components/Footer'
import DemoPage from './pages/DemoPage'

gsap.registerPlugin(ScrollTrigger)

// Expose Lenis globally; also expose the boundary-prevent map so Playground
// can arm/disarm Lenis permission per inner-scroll element.
declare global {
  interface Window {
    __lenis: Lenis | null
    __lenisPreventMap: WeakMap<Element, 'prevent' | 'chain'> | null
  }
}

// ── Shared page transition variants ──────────────────────────────────────────

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
}

// ── Landing page ──────────────────────────────────────────────────────────────

function LandingPage() {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="min-h-screen bg-slate-950 text-slate-200 selection:bg-indigo-500/30"
    >
      <Navbar />
      <Hero />
      <Features />
      <Installation />
      <Usage />
      <Footer />
    </motion.div>
  )
}

// ── Root app with Lenis + router ──────────────────────────────────────────────

function App() {
  const lenisRef = useRef<Lenis | null>(null)
  const location = useLocation()

  useEffect(() => {
    // Boundary-prevent map: Playground writes to this; our prevent callback reads it.
    //   'prevent' → Lenis should ignore this element (native inner scroll)
    //   'chain'   → Lenis should process this element (page scroll)
    window.__lenisPreventMap = new WeakMap()

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      // Dynamically allow/prevent Lenis based on the map Playground manages.
      // When an element is mapped to 'prevent', Lenis ignores wheel events from
      // it (inner element scrolls natively). When mapped to 'chain', Lenis
      // processes the event and smoothly scrolls the page as normal.
      prevent: (node: HTMLElement) => {
        const state = window.__lenisPreventMap?.get(node)
        // Undefined = not managed by us → don't prevent Lenis.
        if (state === undefined) return false
        return state === 'prevent'
      },
    })

    window.__lenis = lenis
    lenisRef.current = lenis

    // Intercept anchor clicks so Lenis handles them smoothly
    const handleAnchorClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const anchor = target.closest('a')
      if (!anchor) return
      const href = anchor.getAttribute('href')
      if (!href || !href.startsWith('#')) return
      const id = href.slice(1)
      if (!id) return
      const el = document.getElementById(id)
      if (!el) return
      e.preventDefault()
      lenis.scrollTo(el, { offset: -100 })
    }

    document.addEventListener('click', handleAnchorClick)

    lenis.on('scroll', ScrollTrigger.update)

    const tickerCallback = (time: number) => {
      lenis.raf(time * 1000)
    }

    gsap.ticker.add(tickerCallback)
    gsap.ticker.lagSmoothing(0)

    return () => {
      document.removeEventListener('click', handleAnchorClick)
      gsap.ticker.remove(tickerCallback)
      lenis.destroy()
      window.__lenis = null
      window.__lenisPreventMap = null
    }
  }, [])

  // Scroll to top on route change
  useEffect(() => {
    lenisRef.current?.scrollTo(0, { immediate: true })
  }, [location.pathname])

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/demo" element={<DemoPage />} />
      </Routes>
    </AnimatePresence>
  )
}

export default App