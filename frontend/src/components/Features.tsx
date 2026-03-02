import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { BackgroundGradient } from "./ui/BackgroundGradient";

const Features = () => {
  const containerRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLHeadingElement>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  const features = [
    {
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>,
      title: 'Pre-execution Validation',
      description: 'Analyze Docker and Kubernetes configs before running commands',
      color: 'from-blue-500 to-cyan-500',
      iconColor: 'text-cyan-700'
    },
    {
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>,
      title: 'AI-Powered Explanations',
      description: 'Get plain English explanations for complex technical errors',
      color: 'from-purple-500 to-pink-500',
      iconColor: 'text-purple-700'
    },
    {
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>,
      title: 'Instant Detection',
      description: 'Catch port conflicts, missing images, and resource issues immediately',
      color: 'from-amber-500 to-orange-500',
      iconColor: 'text-orange-700'
    },
    {
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>,
      title: 'Smart Fix Suggestions',
      description: 'Step-by-step guidance with exact code snippets to resolve issues',
      color: 'from-emerald-500 to-teal-500',
      iconColor: 'text-teal-700'
    },
    {
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>,
      title: 'Works Offline',
      description: 'Core validation features work without internet connection',
      color: 'from-indigo-500 to-purple-500',
      iconColor: 'text-indigo-700'
    },
    {
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>,
      title: 'Zero Configuration',
      description: 'Works out of the box with sensible defaults',
      color: 'from-rose-500 to-red-500',
      iconColor: 'text-rose-700'
    }
  ]

  useGSAP(() => {
    // Header Animation
    gsap.fromTo(headerRef.current,
      { opacity: 0, y: 50 },
      {
        opacity: 1,
        y: 0,
        duration: 1,
        ease: "power3.out",
        scrollTrigger: {
          trigger: headerRef.current,
          start: "top 80%", // When top of element hits 80% from top of viewport
          toggleActions: "play none none none"
        }
      }
    );

    // Cards Animation
    gsap.fromTo(cardRefs.current,
      { opacity: 0, y: 50, scale: 0.9 },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.8,
        stagger: 0.1,
        ease: "power3.out",
        scrollTrigger: {
          trigger: containerRef.current, // Use section as trigger for the grid
          start: "top 70%",
          toggleActions: "play none none none"
        }
      }
    );
  }, { scope: containerRef });

  const addToRefs = (el: HTMLDivElement | null) => {
    if (el && !cardRefs.current.includes(el)) {
      cardRefs.current.push(el);
    }
  };

  return (
    <section id="features" ref={containerRef} className="py-24 px-6 bg-slate-900/50 relative overflow-hidden">
      {/* Background accents */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <h2
          ref={headerRef}
          className="text-5xl md:text-6xl font-bold text-center mb-20 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white"
        >
          Why checkDK?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} ref={addToRefs}>
              <BackgroundGradient className="h-full group">
                <div className="flex flex-col h-full">
                  <div className={`inline-flex w-fit p-3 rounded-xl bg-gradient-to-r ${feature.color} bg-opacity-10 mb-4 ${feature.iconColor}`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-3 text-slate-100 group-hover:text-white transition-colors">{feature.title}</h3>
                  <p className="text-slate-300 leading-relaxed group-hover:text-slate-200 transition-colors">{feature.description}</p>
                </div>
              </BackgroundGradient>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Features
