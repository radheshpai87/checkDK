"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { TextPlugin } from "gsap/TextPlugin";
import { useRef } from "react";

gsap.registerPlugin(TextPlugin);

interface GSAPTypewriterProps {
    text: string;
    className?: string;
    cursorClassName?: string;
    delay?: number;
    speed?: number;
}

export const GSAPTypewriter = ({
    text,
    className,
    cursorClassName = "bg-indigo-500",
    delay = 0
}: GSAPTypewriterProps) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const textRef = useRef<HTMLSpanElement>(null);
    const cursorRef = useRef<HTMLSpanElement>(null);

    useGSAP(() => {
        const tl = gsap.timeline({ delay: delay, repeat: -1, repeatDelay: 5 });

        // Initial state: empty text
        tl.set(textRef.current, { text: "" });

        // Typing effect
        tl.to(textRef.current, {
            duration: text.length * 0.05,
            text: text,
            ease: "none",
        });

        // Blinking cursor effect (runs independently)
        gsap.to(cursorRef.current, {
            opacity: 0,
            repeat: -1,
            yoyo: true,
            duration: 0.5,
            ease: "power2.inOut",
        });

    }, { scope: containerRef });

    return (
        <div ref={containerRef} className={`flex items-center ${className}`}>
            <span ref={textRef}></span>
            <span ref={cursorRef} className={`inline-block w-2 h-5 ml-1 ${cursorClassName}`}></span>
        </div>
    );
};

export default GSAPTypewriter;
