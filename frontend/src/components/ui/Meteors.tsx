
import { motion } from "framer-motion";

export const Meteors = ({ number = 16 }: { number?: number }) => {
  const meteors = new Array(number).fill(true);
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {meteors.map((_, idx) => {
        const duration = Math.random() * 1.5 + 2;
        const delay = idx * 1.2 + Math.random() * 5;
        const startX = Math.floor(Math.random() * 40) - 10;

        return (
          <motion.div
            key={idx}
            className="absolute"
            style={{
              left: `${startX}%`,
              top: `-5%`,
            }}
            animate={{
              left: [`${startX}%`, `${startX + 110}%`],
              top: ['-5%', '105%'],
            }}
            transition={{
              duration: duration,
              delay: delay,
              repeat: Infinity,
              repeatDelay: Math.random() * 8 + 5,
              ease: "linear",
            }}
          >
            <motion.div
              animate={{
                opacity: [0, 0.8, 0.8, 0],
              }}
              transition={{
                duration: duration,
                delay: delay,
                repeat: Infinity,
                repeatDelay: Math.random() * 8 + 5,
                times: [0, 0.15, 0.7, 1],
              }}
            >
              <div className="relative" style={{ transform: 'rotate(45deg)' }}>
                {/* Bright meteor head */}
                <div
                  className="absolute top-0 right-0 rounded-full"
                  style={{
                    width: '3px',
                    height: '3px',
                    background: 'radial-gradient(circle, rgba(255, 255, 255, 1) 0%, rgba(199, 210, 254, 0.9) 50%, transparent 100%)',
                    boxShadow: '0 0 18px 4px rgba(199, 210, 254, 0.6), 0 0 8px 2px rgba(255, 255, 255, 0.8)',
                  }}
                />

                {/* Main trail */}
                <div
                  className="absolute top-1/2 right-0 -translate-y-1/2"
                  style={{
                    width: '85px',
                    height: '1.5px',
                    background: 'linear-gradient(to left, rgba(255, 255, 255, 0.9), rgba(199, 210, 254, 0.7), rgba(167, 139, 250, 0.5), rgba(139, 92, 246, 0.3), transparent)',
                    filter: 'blur(0.5px)',
                  }}
                />

                {/* Soft glow trail */}
                <div
                  className="absolute top-1/2 right-0 -translate-y-1/2"
                  style={{
                    width: '100px',
                    height: '8px',
                    background: 'linear-gradient(to left, rgba(199, 210, 254, 0.4), rgba(167, 139, 250, 0.25), rgba(139, 92, 246, 0.15), transparent)',
                    filter: 'blur(5px)',
                  }}
                />
              </div>
            </motion.div>
          </motion.div>
        );
      })}
    </div>
  );
};
