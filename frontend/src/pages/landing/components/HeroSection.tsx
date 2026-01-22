import { PixelLogo } from './PixelLogo';

export function HeroSection() {
  return (
    <section className="flex flex-col items-center justify-center pt-20 pb-16 px-4">
      <PixelLogo />

      <p className="mt-8 text-lg sm:text-xl text-landing-text-muted text-center max-w-2xl font-mono">
        AI-powered prediction market trading framework
      </p>

      <div className="mt-10 flex gap-4">
        <a
          href="https://github.com/randomness11/probablyprofit"
          target="_blank"
          rel="noopener noreferrer"
          className="px-6 py-3 bg-white text-black font-mono text-sm hover:bg-white/90 transition-colors"
        >
          Get Started
        </a>
        <a
          href="https://github.com/randomness11/probablyprofit"
          target="_blank"
          rel="noopener noreferrer"
          className="px-6 py-3 border border-landing-border text-white font-mono text-sm hover:border-white/40 transition-colors"
        >
          View on GitHub
        </a>
      </div>
    </section>
  );
}
