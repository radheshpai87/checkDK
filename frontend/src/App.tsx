import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Installation from './components/Installation'
import Usage from './components/Usage'
import Footer from './components/Footer'
import { useEffect, useRef } from 'react'
import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

function App() {
  const lenisRef = useRef<Lenis | null>(null)

  useEffect(() => {
    // Initialize Lenis
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
    })

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

    lenisRef.current = lenis

    // Sync Lenis with GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update)

    gsap.ticker.add((time) => {
      lenis.raf(time * 1000)
    })

    gsap.ticker.lagSmoothing(0)

    return () => {
      document.removeEventListener('click', handleAnchorClick)
      gsap.ticker.remove((time) => {
        lenis.raf(time * 1000)
      })
      lenis.destroy()
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-indigo-500/30">
      <Navbar />
      <Hero />
      <Features />
      <Installation />
      <Usage />
      <Footer />
    </div>
  )
}

export default App
