import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { Link } from "react-router-dom";
import { HoverBorderGradient } from "./ui/HoverBorderGradient";
import { TextShimmer } from "./ui/TextShimmer";
import { Meteors } from "./ui/Meteors";

const Hero = () => {
  const containerRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const glow1Ref = useRef<HTMLDivElement>(null);
  const glow2Ref = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);

  useGSAP(() => {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    gsap.set([contentRef.current?.children], { opacity: 0, y: 30 });
    gsap.set(titleRef.current, { y: 50, opacity: 0 });

    tl.to(contentRef.current?.children || [], {
      y: 0,
      opacity: 1,
      duration: 1,
      stagger: 0.15,
      delay: 0.2
    });

    const handleMouseMove = (e: MouseEvent) => {
      const { clientX, clientY } = e;
      const x = (clientX / window.innerWidth - 0.5) * 2;
      const y = (clientY / window.innerHeight - 0.5) * 2;

      gsap.to(glow1Ref.current, { x: x * 50, y: y * 50, duration: 2, ease: "power2.out" });
      gsap.to(glow2Ref.current, { x: -x * 50, y: -y * 50, duration: 2, ease: "power2.out" });
      gsap.to(titleRef.current, {
        x: x * 10, y: y * 10,
        rotationY: x * 5, rotationX: -y * 5,
        duration: 1, ease: "power2.out",
      });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, { scope: containerRef });

  return (
    <section ref={containerRef} className="relative min-h-screen flex items-center justify-center overflow-hidden bg-slate-950 perspective-1000">
      <Meteors number={16} />

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div ref={glow1Ref} className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-indigo-500/20 rounded-full blur-[120px]" />
        <div ref={glow2Ref} className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-purple-500/20 rounded-full blur-[120px]" />
      </div>

      <div ref={contentRef} className="relative z-10 max-w-5xl mx-auto px-6 py-32 text-center transform-style-3d">
        <div className="mb-8 flex justify-center">
          <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-2xl shadow-indigo-500/50 mb-8 backdrop-blur-sm border border-indigo-400/20">
            <svg className="w-9 h-9 sm:w-12 sm:h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        {/* FIX: Responsive font sizes - was 7xl/8xl (clips on mobile), now scales from 4xl up */}
        <h1
          ref={titleRef}
          className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white will-change-transform"
        >
          checkDK
        </h1>

        <div className="mb-6">
          <TextShimmer className="text-xl sm:text-2xl md:text-3xl font-semibold">
            Predict. Diagnose. Fix – Before You Waste Time.
          </TextShimmer>
        </div>

        <p className="text-base sm:text-lg md:text-xl text-slate-300 max-w-3xl mx-auto mb-12 leading-relaxed">
          AI-powered CLI tool that detects and fixes Docker/Kubernetes issues before execution.
          Save hours of debugging by catching configuration errors before they happen.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <HoverBorderGradient
            as="a"
            href="#installation"
            className="!bg-slate-900 text-white px-8 py-3 text-base w-full sm:w-auto justify-center"
          >
            Get Started →
          </HoverBorderGradient>

          <Link
            to="/demo"
            className="group px-8 py-3 w-full sm:w-auto justify-center rounded-xl border border-slate-700 bg-slate-900/50 backdrop-blur-sm text-slate-100 font-medium hover:border-indigo-400 hover:text-indigo-300 hover:bg-slate-800/50 transition-all duration-300 flex items-center"
          >
            <span className="inline-block group-hover:scale-105 transition-transform">Try Playground ↗</span>
          </Link>
        </div>
      </div>
    </section>
  );
};

export default Hero;