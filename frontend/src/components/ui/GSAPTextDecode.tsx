"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useRef } from "react";

interface GSAPTextDecodeProps {
  text: string;
  className?: string;
  duration?: number;
  delay?: number;
}

const GSAPTextDecode = ({ text, className, duration = 1.5, delay = 0 }: GSAPTextDecodeProps) => {
  const textRef = useRef<HTMLHeadingElement>(null);
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+";

  useGSAP(() => {
    const el = textRef.current;
    if (!el) return;

    const originalText = text;
    const splitText = originalText.split("");
    
    // Set initial random state
    el.innerText = splitText.map(() => chars[Math.floor(Math.random() * chars.length)]).join("");

    const tl = gsap.timeline({ delay });

    // Animate the text scrambling to the final text
    const onUpdate = function () {
      // @ts-ignore
      const progress = this.progress();
      const currentText = splitText.map((char, i) => {
        if (progress * splitText.length > i) {
          return char;
        }
        return chars[Math.floor(Math.random() * chars.length)];
      }).join("");
      
      el.innerText = currentText;
    };

    tl.to({}, {
      duration: duration,
      onUpdate: onUpdate,
      ease: "power2.out",
    });

    // Ensure final state is clean
    tl.set(el, { innerText: originalText });

  }, { scope: textRef });

  return (
    <h1 ref={textRef} className={className}>
      {text}
    </h1>
  );
};

export default GSAPTextDecode;
