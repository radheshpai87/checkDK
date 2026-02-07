import { motion } from "framer-motion";
import { useState } from "react";

const Installation = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const requirements = [
    {
      title: "Python 3.10+",
      description: "Required for running checkDK",
      icon: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    },
    {
      title: "Docker 20.10+",
      description: "For Docker container analysis",
      icon: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
    },
    {
      title: "kubectl",
      description: "For Kubernetes manifest validation",
      icon: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
      </svg>
    }
  ];

  const steps = [
    {
      number: "1",
      title: "Install via pip",
      code: "pip install checkdk",
      description: "Install checkDK from PyPI"
    },
    {
      number: "2",
      title: "Verify installation",
      code: "checkdk --version",
      description: "Confirm checkDK is installed correctly"
    },
    {
      number: "3",
      title: "Start using it",
      code: "checkdk docker compose up",
      description: "Begin validating your Docker and Kubernetes commands"
    }
  ];

  return (
    <section id="installation" className="py-24 px-6 bg-slate-950">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-5xl md:text-6xl font-bold text-center mb-12 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white"
        >
          Get Started
        </motion.h2>

        {/* Requirements Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <h3 className="text-3xl font-semibold mb-8 text-center text-slate-100">Requirements</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {requirements.map((req, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative group"
              >
                <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl opacity-20 group-hover:opacity-30 blur transition duration-300"></div>
                <div className="relative bg-slate-900/90 rounded-2xl p-6 border border-slate-800 h-full">
                  <div className="flex flex-col items-center text-center">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white mb-4">
                      {req.icon}
                    </div>
                    <h4 className="text-xl font-semibold text-white mb-2">{req.title}</h4>
                    <p className="text-slate-400 text-sm">{req.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Installation Steps */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h3 className="text-3xl font-semibold mb-10 text-center text-slate-100">Installation Steps</h3>
          <div className="space-y-6">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative group"
              >
                <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl opacity-20 group-hover:opacity-30 blur transition duration-300"></div>
                <div className="relative bg-slate-900/90 rounded-2xl p-6 border border-slate-800">
                  <div className="flex gap-6 items-start">
                    <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-lg">
                      {step.number}
                    </div>
                    
                    <div className="flex-1">
                      <h4 className="text-xl font-semibold mb-2 text-white">{step.title}</h4>
                      <p className="text-slate-400 text-sm mb-4">{step.description}</p>
                      <div className="relative bg-slate-950 rounded-xl border border-slate-800 group/code">
                        <div className="flex items-center justify-between p-4 pr-3">
                          <code className="text-cyan-400 font-mono text-base flex-1">{step.code}</code>
                          <button
                            onClick={() => copyToClipboard(step.code, index)}
                            className="flex-shrink-0 ml-3 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 opacity-0 group-hover/code:opacity-100 transition-all duration-200"
                            title="Copy to clipboard"
                          >
                            {copiedIndex === index ? (
                              <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default Installation
