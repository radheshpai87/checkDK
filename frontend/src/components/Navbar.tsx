import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useLocation, useNavigate } from "react-router-dom";

// ── Nav item definitions (route-aware) ───────────────────────────────────────

// On /demo  → anchor links live within the demo page
// On /      → anchor links live within the landing page
// Cross-route links (e.g. Features from /demo) use React Router navigation

type NavItem = {
  label: string;
  landingHref: string; // href used on the landing page
  demoHref: string;    // href used on the demo page
};

const NAV_ITEMS: NavItem[] = [
  { label: 'Features', landingHref: '#features', demoHref: '/#features' },
  { label: 'Playground', landingHref: '/demo#playground', demoHref: '#playground' },
  { label: 'Install', landingHref: '#installation', demoHref: '/#installation' },
  { label: 'Usage', landingHref: '#usage', demoHref: '/#usage' },
  { label: 'Dashboard', landingHref: '/demo#dashboard', demoHref: '#dashboard' },
];

const GITHUB_URL = "https://github.com/radheshpai87/checkDK";

// ── Navbar ────────────────────────────────────────────────────────────────────

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const isDemo = location.pathname === '/demo';

  // Active section tracking via IntersectionObserver
  useEffect(() => {
    const sectionIds = isDemo
      ? ['playground', 'dashboard']
      : ['features', 'installation', 'usage'];

    const observers: IntersectionObserver[] = [];

    sectionIds.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      const observer = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActiveSection(id); },
        { threshold: 0.3 }
      );
      observer.observe(el);
      observers.push(observer);
    });

    return () => observers.forEach(o => o.disconnect());
  }, [isDemo, location.pathname]);

  // Close mobile menu on scroll
  useEffect(() => {
    const handler = () => setMobileOpen(false);
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  const handleNavClick = (href: string) => {
    setMobileOpen(false);

    // Cross-route: e.g. clicking "Features" from /demo → navigate to /#features
    if (href.startsWith('/') && !href.startsWith('/#') === false) {
      // /#section navigation
      const [path, hash] = href.split('#');
      navigate(path || '/');
      setTimeout(() => {
        const el = document.getElementById(hash);
        el?.scrollIntoView({ behavior: 'smooth' });
      }, 300);
      return;
    }

    if (href.startsWith('/')) {
      // Pure route change like /demo
      navigate(href);
      return;
    }

    // Same-page anchor
    const el = document.querySelector(href);
    if (el) {
      setTimeout(() => el.scrollIntoView({ behavior: 'smooth' }), 150);
    }
  };

  const getHref = (item: NavItem) =>
    isDemo ? item.demoHref : item.landingHref;

  const getIsActive = (item: NavItem) => {
    const hash = isDemo ? item.demoHref : item.landingHref;
    // Only match pure in-page anchors
    if (!hash.startsWith('#')) return false;
    return activeSection === hash.replace('#', '');
  };

  return (
    <>
      <motion.nav
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="fixed top-4 sm:top-6 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] sm:w-auto"
      >
        <div className="px-4 sm:px-5 py-3 rounded-2xl backdrop-blur-xl bg-slate-900/70 border border-slate-700/50 shadow-2xl shadow-indigo-500/10 overflow-hidden">
          <div className="flex items-center justify-between gap-3 sm:gap-4">

            {/* ← Home button — only on /demo */}
            {isDemo && (
              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
              >
                <Link
                  to="/"
                  className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-slate-400 hover:text-indigo-300 text-sm font-medium transition-colors flex-shrink-0 border border-slate-700/50 hover:border-indigo-500/40 bg-slate-800/40"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Home
                </Link>
              </motion.div>
            )}

            {/* Logo */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="flex-shrink-0">
              <Link
                to="/"
                className="flex items-center gap-2"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="font-bold text-white text-lg">checkDK</span>
              </Link>
            </motion.div>

            {/* Desktop Nav Links */}
            <div className="hidden md:flex items-center gap-0.5 min-w-0 flex-shrink">
              {NAV_ITEMS.map((item) => {
                const href = getHref(item);
                const isActive = getIsActive(item);
                const isCrossRoute = href.startsWith('/');

                return isCrossRoute ? (
                  <motion.div key={item.label} whileTap={{ scale: 0.95 }}>
                    <Link
                      to={href}
                      onClick={() => {
                        if (href.includes('#')) {
                          const [path, hash] = href.split('#');
                          navigate(path || '/');
                          setTimeout(() => {
                            document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth' });
                          }, 300);
                        }
                      }}
                      className="relative block px-2.5 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white transition-colors"
                    >
                      {item.label}
                    </Link>
                  </motion.div>
                ) : (
                  <motion.a
                    key={item.label}
                    href={href}
                    onClick={(e) => { e.preventDefault(); handleNavClick(href); }}
                    className={`relative px-2.5 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? 'text-white' : 'text-slate-300 hover:text-white'
                      }`}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isActive && (
                      <motion.span
                        layoutId="nav-pill"
                        className="absolute inset-0 rounded-lg bg-slate-700/70"
                        style={{ borderRadius: 8 }}
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10">{item.label}</span>
                  </motion.a>
                );
              })}
            </div>

            {/* GitHub + Hamburger */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <motion.a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden md:flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-300 hover:text-white hover:border-indigo-500/50 transition-all text-sm font-medium"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
                <span className="hidden lg:inline">GitHub</span>
              </motion.a>

              {/* Hamburger — mobile only */}
              <motion.button
                className="md:hidden p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-300 hover:text-white transition-colors"
                onClick={() => setMobileOpen(o => !o)}
                whileTap={{ scale: 0.9 }}
                aria-label="Toggle menu"
              >
                <div className="w-4 h-4 flex flex-col justify-center gap-[5px]">
                  <motion.span className="block h-0.5 bg-current rounded-full origin-center"
                    animate={mobileOpen ? { rotate: 45, y: 7 } : { rotate: 0, y: 0 }}
                    transition={{ duration: 0.2 }} />
                  <motion.span className="block h-0.5 bg-current rounded-full"
                    animate={mobileOpen ? { opacity: 0, scaleX: 0 } : { opacity: 1, scaleX: 1 }}
                    transition={{ duration: 0.2 }} />
                  <motion.span className="block h-0.5 bg-current rounded-full origin-center"
                    animate={mobileOpen ? { rotate: -45, y: -7 } : { rotate: 0, y: 0 }}
                    transition={{ duration: 0.2 }} />
                </div>
              </motion.button>
            </div>
          </div>
        </div>
      </motion.nav>

      {/* ── Mobile Drawer ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.97 }}
              transition={{ duration: 0.2 }}
              className="fixed top-20 left-4 right-4 z-50 md:hidden rounded-2xl bg-slate-900 border border-slate-700/50 shadow-2xl shadow-indigo-500/10 overflow-hidden"
            >
              <div className="p-3 space-y-1">
                {/* ← Home in drawer when on /demo */}
                {isDemo && (
                  <Link
                    to="/"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-indigo-300 hover:bg-indigo-500/10 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Back to Home
                  </Link>
                )}

                {NAV_ITEMS.map((item, i) => {
                  const href = getHref(item);
                  const isActive = getIsActive(item);
                  const isCrossRoute = href.startsWith('/');

                  const cls = `flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${isActive
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`;

                  return isCrossRoute ? (
                    <motion.div key={item.label} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
                      <Link to={href} onClick={() => setMobileOpen(false)} className={cls}>
                        {item.label}
                      </Link>
                    </motion.div>
                  ) : (
                    <motion.a
                      key={item.label}
                      href={href}
                      onClick={(e) => { e.preventDefault(); handleNavClick(href); }}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className={cls}
                    >
                      {isActive && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />}
                      {item.label}
                    </motion.a>
                  );
                })}

                <div className="pt-2 mt-2 border-t border-slate-800">
                  <a
                    href={GITHUB_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-300 hover:bg-slate-800 hover:text-white transition-colors font-medium"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    GitHub
                  </a>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navbar;