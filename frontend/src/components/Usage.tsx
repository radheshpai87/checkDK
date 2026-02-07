import { motion } from "framer-motion";
import { BackgroundGradient } from "./ui/BackgroundGradient";

const Usage = () => {
  const examples = [
    {
      title: "Docker Compose",
      description: "Validate and run Docker Compose configurations",
      code: "$ checkdk docker compose up",
      output: "[WARN] Port conflict detected on 'web' service\n[FIX]  Port 8080 is used by nginx (PID 1234)\n       Change to 8081:80 or run: sudo systemctl stop nginx"
    },
    {
      title: "Kubernetes",
      description: "Validate manifests before applying",
      code: "$ checkdk kubectl apply -f deployment.yaml",
      output: "[OK]   Analyzing deployment.yaml\n[OK]   All validations passed\n[INFO] Applying to cluster..."
    },
    {
      title: "Dry Run Mode",
      description: "Analyze without executing",
      code: "$ checkdk docker compose up --dry-run",
      output: "[OK]   YAML syntax valid\n[OK]   All images available\n[WARN] Warning: redis container has no resource limits"
    }
  ];

  const detections = [
    { 
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>,
      label: "Port conflicts" 
    },
    { 
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>,
      label: "Missing env variables" 
    },
    { 
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>,
      label: "Invalid YAML syntax" 
    },
    { 
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>,
      label: "Resource limit issues" 
    },
    { 
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>,
      label: "Service dependencies" 
    },
    { 
      icon: <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>,
      label: "Image availability" 
    }
  ];

  return (
    <section id="usage" className="py-24 px-6 bg-slate-900/50">
      <div className="max-w-7xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-5xl md:text-6xl font-bold text-center mb-20 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white"
        >
          Usage Examples
        </motion.h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-20">
          {examples.map((example, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <BackgroundGradient className="h-full">
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-slate-100">{example.title}</h3>
                  <p className="text-slate-300 text-sm">{example.description}</p>
                  
                  <div className="space-y-3">
                    <div className="relative group">
                      <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg opacity-25 group-hover:opacity-40 blur transition duration-300"></div>
                      <div className="relative bg-slate-900 dark:bg-slate-900/80 rounded-lg p-4 border border-slate-700 dark:border-slate-800">
                        <code className="text-emerald-400 font-mono text-sm">{example.code}</code>
                        <div className="mt-3 pt-3 border-t border-slate-700">
                          <pre className="font-mono text-xs whitespace-pre-wrap leading-relaxed">
                            {example.output.split('\n').map((line, i) => {
                              if (line.includes('[OK]')) {
                                return <div key={i} className="text-green-400">{line}</div>;
                              } else if (line.includes('[WARN]')) {
                                return <div key={i} className="text-amber-400">{line}</div>;
                              } else if (line.includes('[FIX]')) {
                                return <div key={i} className="text-cyan-400">{line}</div>;
                              } else if (line.includes('[INFO]')) {
                                return <div key={i} className="text-blue-400">{line}</div>;
                              } else if (line.includes('[ERROR]')) {
                                return <div key={i} className="text-red-400">{line}</div>;
                              }
                              return <div key={i} className="text-slate-400">{line}</div>;
                            })}
                          </pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </BackgroundGradient>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h3 className="text-3xl font-bold mb-12 text-white">What It Detects</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 max-w-5xl mx-auto">
            {detections.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ scale: 1.05 }}
                className="bg-slate-900 rounded-xl p-6 border border-slate-800 shadow-sm hover:shadow-lg hover:border-indigo-400 transition-all duration-300"
              >
                <div className="text-indigo-400 mb-3">{item.icon}</div>
                <p className="text-sm font-medium text-slate-200">{item.label}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default Usage
