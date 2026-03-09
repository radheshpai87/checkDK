import { motion } from 'framer-motion'
import { Navigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import DocsTab from '../components/dashboard/DocsTab'
import Footer from '../components/Footer'
import { useAuth } from '../context/AuthContext'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
}

export default function DocsPage() {
  const { isAuthenticated, isLoading } = useAuth()

  // Authenticated users have docs inside the dashboard
  if (!isLoading && isAuthenticated) {
    return <Navigate to="/app/dashboard" replace />
  }

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

      {/* Hero banner */}
      <section className="relative pt-36 pb-8 px-6 text-center overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[300px] bg-indigo-500/8 rounded-full blur-[100px]" />
        </div>
        <div className="relative max-w-3xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white mb-4">
            Documentation
          </h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Installation guides, CLI reference, API endpoints, and ML prediction docs.
          </p>
        </div>
      </section>

      <DocsTab />
      <Footer />
    </motion.div>
  )
}
