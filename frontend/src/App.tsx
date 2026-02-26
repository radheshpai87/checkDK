import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Installation from './components/Installation'
import Usage from './components/Usage'
import Playground from './components/playground/Playground'
import Dashboard from './components/dashboard/Dashboard'
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
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
    })

    lenisRef.current = lenis

    lenis.on('scroll', ScrollTrigger.update)

    // FIX: Store the ticker callback so it can be properly removed
    const tickerCallback = (time: number) => {
      lenis.raf(time * 1000)
    }

    gsap.ticker.add(tickerCallback)
    gsap.ticker.lagSmoothing(0)

    return () => {
      // FIX: Remove the exact same function reference
      gsap.ticker.remove(tickerCallback)
      lenis.destroy()
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-indigo-500/30">
      <Navbar />
      <Hero />
      <Features />
      <Playground />
      <Installation />
      <Usage />
      <Dashboard />
      <Footer />
    </div>
  )
}

export default App