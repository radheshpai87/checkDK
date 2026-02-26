import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Playground from '../components/playground/Playground'
import Dashboard from '../components/dashboard/Dashboard'

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 },
}

const DemoPage = () => {
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

            {/* ── Demo hero banner ─────────────────────────────────────────────── */}
            <section className="relative pt-36 pb-16 px-6 text-center overflow-hidden">
                {/* Subtle background glow */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[300px] bg-indigo-500/8 rounded-full blur-[100px]" />
                </div>

                {/* Grid lines decoration */}
                <div className="absolute inset-0 pointer-events-none opacity-[0.03]"
                    style={{
                        backgroundImage: 'linear-gradient(#6366f1 1px, transparent 1px), linear-gradient(90deg, #6366f1 1px, transparent 1px)',
                        backgroundSize: '60px 60px',
                    }}
                />

                <div className="relative z-10 max-w-3xl mx-auto">
                    {/* Badge */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-mono font-medium mb-8"
                    >
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                        Client-side demo · Real AI analysis coming soon
                    </motion.div>

                    {/* Heading */}
                    <motion.h1
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-5 bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white"
                    >
                        Interactive Demo
                    </motion.h1>

                    {/* Subtext */}
                    <motion.p
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-slate-400 text-lg max-w-2xl mx-auto mb-8 leading-relaxed"
                    >
                        Paste any Docker Compose or Kubernetes manifest and get a full analysis
                        report — exactly what{' '}
                        <code className="text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded text-sm font-mono">
                            checkdk
                        </code>{' '}
                        outputs in your terminal.
                    </motion.p>

                    {/* Jump links */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                        className="flex items-center justify-center gap-3 flex-wrap"
                    >
                        <a
                            href="#playground"
                            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
                        >
                            Open Playground ↓
                        </a>
                        <a
                            href="#dashboard"
                            className="px-5 py-2 rounded-xl border border-slate-700 bg-slate-900/50 hover:border-slate-600 text-slate-300 hover:text-white text-sm font-medium transition-colors"
                        >
                            View Dashboard ↓
                        </a>
                    </motion.div>
                </div>
            </section>

            {/* Divider */}
            <div className="h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent mx-6" />

            {/* ── Playground + Dashboard ───────────────────────────────────────── */}
            <Playground />

            <div className="h-px bg-gradient-to-r from-transparent via-slate-800/60 to-transparent mx-6" />

            <Dashboard />

            {/* ── Footer strip ─────────────────────────────────────────────────── */}
            <footer className="border-t border-slate-800 py-8 px-6">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
                    <p>© 2026 checkDK · Built for developers who value their time.</p>
                    <Link
                        to="/"
                        className="flex items-center gap-1.5 hover:text-indigo-300 transition-colors"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        Back to home
                    </Link>
                </div>
            </footer>
        </motion.div>
    )
}

export default DemoPage
