import { motion } from "framer-motion";
import { HoverBorderGradient } from "./ui/HoverBorderGradient";
import { TextShimmer } from "./ui/TextShimmer";
import { Meteors } from "./ui/Meteors";
import GSAPTextDecode from "./ui/GSAPTextDecode";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useRef } from "react";

const Hero = () => {
  const containerRef = useRef<HTMLElement>(null);
  const blob1Ref = useRef<HTMLDivElement>(null);
  const blob2Ref = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { clientX, clientY } = e;
      const x = clientX - window.innerWidth / 2;
      const y = clientY - window.innerHeight / 2;

      gsap.to(blob1Ref.current, {
        x: x * 0.05,
        y: y * 0.05,
        duration: 2,
        ease: "power2.out",
      });

      gsap.to(blob2Ref.current, {
        x: x * -0.05,
        y: y * -0.05,
        duration: 2,
        ease: "power2.out",
      });
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, { scope: containerRef });

  return (
    <section ref={containerRef} className="relative min-h-screen flex items-center justify-center overflow-hidden bg-slate-950">
      <Meteors number={16} />

      {/* Ambient glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div ref={blob1Ref} className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-indigo-500/20 rounded-full blur-[120px]" />
        <div ref={blob2Ref} className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-purple-500/20 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-32 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-2xl shadow-indigo-500/50 mb-8 backdrop-blur-sm border border-indigo-400/20">
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </motion.div>

        <div className="mb-6 min-h-[5rem] md:min-h-[6rem] flex items-center justify-center">
          <GSAPTextDecode
            text="checkDK"
            className="text-7xl md:text-8xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white"
          />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mb-6"
        >
          <TextShimmer className="text-2xl md:text-3xl font-semibold">
            Predict. Diagnose. Fix – Before You Waste Time.
          </TextShimmer>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-xl text-slate-300 max-w-3xl mx-auto mb-12 leading-relaxed"
        >
          AI-powered CLI tool that detects and fixes Docker/Kubernetes issues before execution.
          Save hours of debugging by catching configuration errors before they happen.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="flex flex-wrap items-center justify-center gap-4"
        >
          <HoverBorderGradient
            as="a"
            href="#installation"
            className="!bg-slate-900 text-white px-8 py-3 text-base"
          >
            Get Started →
          </HoverBorderGradient>

          <motion.a
            href="#usage"
            className="px-8 py-3 rounded-xl border border-slate-700 bg-slate-900/50 backdrop-blur-sm text-slate-100 font-medium hover:border-indigo-400 hover:text-indigo-300 hover:bg-slate-800/50 transition-all duration-300"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            View Docs
          </motion.a>
        </motion.div>
      </div>
    </section>
  )
}

export default Hero
