export function FeaturesSection() {
  const features = [
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a4 4 0 0 1 4 4v1a1 1 0 0 0 1 1h1a4 4 0 0 1 0 8h-1a1 1 0 0 0-1 1v1a4 4 0 0 1-8 0v-1a1 1 0 0 0-1-1H6a4 4 0 0 1 0-8h1a1 1 0 0 0 1-1V6a4 4 0 0 1 4-4z"/>
          <circle cx="12" cy="12" r="2"/>
        </svg>
      ),
      title: 'AI-Powered Analysis',
      description: 'Leverage Claude, GPT-4, and other LLMs to analyze markets and identify opportunities.',
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
      ),
      title: 'Multiple Strategies',
      description: 'Choose from value betting, arbitrage, sentiment analysis, or create your own custom strategy.',
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
      ),
      title: 'Risk Management',
      description: 'Built-in position sizing, stop losses, and exposure limits to protect your portfolio.',
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
      ),
      title: 'Real-Time Execution',
      description: 'Automated trading with live market monitoring and instant order execution.',
    },
  ];

  return (
    <section className="py-20 px-4 max-w-5xl mx-auto">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="border border-landing-border p-6 hover:border-white/20 transition-colors"
          >
            <div className="text-white mb-4">{feature.icon}</div>
            <h3 className="font-mono text-white text-lg mb-2">{feature.title}</h3>
            <p className="text-landing-text-muted text-sm leading-relaxed">
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
