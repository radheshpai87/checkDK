const Footer = () => {
  return (
    <footer className="bg-slate-950 text-white py-24 px-6 border-t border-slate-800">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-8">
          <div>
            <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              checkDK
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Predict. Diagnose. Fix – Before You Waste Time.
            </p>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              <li>
                <a href="#installation" className="text-slate-400 hover:text-indigo-300 transition-colors">
                  Installation
                </a>
              </li>
              <li>
                <a href="#usage" className="text-slate-400 hover:text-indigo-300 transition-colors">
                  Documentation
                </a>
              </li>
              <li>
                <a href="https://github.com" className="text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-300 transition-colors">
                  GitHub
                </a>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold mb-4">Support</h4>
            <ul className="space-y-2">
              <li>
                <a href="https://github.com" className="text-slate-400 hover:text-indigo-300 transition-colors">
                  Report Issues
                </a>
              </li>
              <li>
                <a href="https://github.com" className="text-slate-400 hover:text-indigo-300 transition-colors">
                  Contribute
                </a>
              </li>
              <li>
                <a href="https://github.com" className="text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-300 transition-colors">
                  Community
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="pt-8 border-t border-slate-800 text-center">
          <p className="text-slate-500 dark:text-slate-500 text-sm">
            &copy; 2026 checkDK. Built for developers who value their time.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
