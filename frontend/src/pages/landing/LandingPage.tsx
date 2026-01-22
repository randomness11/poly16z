import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ClipboardIcon, CheckIcon, StarIcon, CpuChipIcon, ArrowsRightLeftIcon, ShieldCheckIcon, BoltIcon } from '@heroicons/react/24/outline';
import { PixelLogo } from './components/PixelLogo';
import '../../styles/landing.css';

export function LandingPage() {
  const [copied, setCopied] = useState(false);
  const command = 'pip install probablyprofit';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const providers = [
    { name: 'Claude', icon: <svg width="20" height="20" viewBox="0 6.603 1192.672 1193.397" fill="currentColor"><path d="m233.96 800.215 234.684-131.678 3.947-11.436-3.947-6.363h-11.436l-39.221-2.416-134.094-3.624-116.296-4.832-112.67-6.04-28.35-6.04-26.577-35.035 2.738-17.477 23.84-16.027 34.147 2.98 75.463 5.155 113.235 7.812 82.147 4.832 121.692 12.644h19.329l2.738-7.812-6.604-4.832-5.154-4.832-117.182-79.41-126.845-83.92-66.443-48.321-35.92-24.484-18.12-22.953-7.813-50.093 32.618-35.92 43.812 2.98 11.195 2.98 44.375 34.147 94.792 73.37 123.786 91.167 18.12 15.06 7.249-5.154.886-3.624-8.135-13.61-67.329-121.692-71.838-123.785-31.974-51.302-8.456-30.765c-2.98-12.645-5.154-23.275-5.154-36.242l37.127-50.416 20.537-6.604 49.53 6.604 20.86 18.121 30.765 70.39 49.852 110.818 77.315 150.684 22.631 44.698 12.08 41.396 4.51 12.645h7.813v-7.248l6.362-84.886 11.759-104.215 11.436-134.094 3.946-37.772 18.685-45.262 37.127-24.482 28.994 13.852 23.839 34.148-3.303 22.067-14.174 92.134-27.785 144.323-18.121 96.644h10.55l12.08-12.08 48.887-64.913 82.147-102.685 36.242-40.752 42.282-45.02 27.14-21.423h51.303l37.772 56.135-16.913 57.986-52.832 67.007-43.812 56.779-62.82 84.563-39.22 67.651 3.623 5.396 9.343-.886 141.906-30.201 76.671-13.852 91.49-15.705 41.396 19.329 4.51 19.65-16.269 40.189-97.852 24.16-114.764 22.954-170.9 40.43-2.093 1.53 2.416 2.98 76.993 7.248 32.94 1.771h80.617l150.12 11.195 39.222 25.933 23.517 31.732-3.946 24.16-60.403 30.766-81.503-19.33-190.228-45.26-65.235-16.27h-9.02v5.397l54.362 53.154 99.624 89.96 124.752 115.973 6.362 28.671-16.027 22.63-16.912-2.415-109.611-82.47-42.282-37.127-95.758-80.618h-6.363v8.456l22.067 32.296 116.537 175.167 6.04 53.719-8.456 17.476-30.201 10.55-33.181-6.04-68.215-95.758-70.39-107.84-56.778-96.644-6.926 3.947-33.503 360.886-15.705 18.443-36.243 13.852-30.201-22.953-16.027-37.127 16.027-73.37 19.329-95.758 15.704-76.107 14.175-94.55 8.456-31.41-.563-2.094-6.927.886-71.275 97.852-108.402 146.497-85.772 91.812-20.537 8.134-35.597-18.443 3.301-32.94 19.893-29.315 118.712-151.007 71.597-93.583 46.228-54.04-.322-7.813h-2.738l-315.302 204.725-56.135 7.248-24.16-22.63 2.98-37.128 11.435-12.08 94.792-65.236-.322.323z"/></svg> },
    { name: 'GPT-4', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg> },
    { name: 'Gemini', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 24A14.304 14.304 0 0 0 0 12 14.304 14.304 0 0 0 12 0a14.305 14.305 0 0 0 12 12 14.305 14.305 0 0 0-12 12"/></svg> },
  ];

  const features = [
    { icon: CpuChipIcon, title: 'AI Analysis', desc: 'LLM-powered market insights' },
    { icon: ArrowsRightLeftIcon, title: 'Multi-Strategy', desc: 'Value, arbitrage, sentiment' },
    { icon: ShieldCheckIcon, title: 'Risk Controls', desc: 'Position limits & stop losses' },
    { icon: BoltIcon, title: 'Auto Execution', desc: 'Real-time order placement' },
  ];

  return (
    <div className="landing-theme min-h-screen bg-landing-bg flex flex-col">
      {/* Main Hero - Everything in one view */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        {/* Logo */}
        <PixelLogo />

        {/* Tagline */}
        <p className="mt-6 text-base sm:text-lg text-landing-text-muted text-center font-mono">
          AI-powered prediction market trading framework
        </p>

        {/* Install Command */}
        <div className="mt-8 flex items-center gap-3 bg-landing-border/50 border border-landing-border px-4 py-3">
          <span className="text-landing-text-muted font-mono">$</span>
          <code className="font-mono text-white text-sm">{command}</code>
          <button
            onClick={handleCopy}
            className="ml-2 p-1.5 text-landing-text-muted hover:text-white transition-colors"
          >
            {copied ? <CheckIcon className="w-4 h-4" /> : <ClipboardIcon className="w-4 h-4" />}
          </button>
        </div>

        {/* CTAs */}
        <div className="mt-6 flex gap-4">
          <Link
            to="/app"
            className="px-5 py-2.5 bg-white text-black font-mono text-sm hover:bg-white/90 transition-colors"
          >
            Open Dashboard
          </Link>
          <a
            href="https://github.com/randomness11/probablyprofit"
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 border border-landing-border text-white font-mono text-sm hover:border-white/40 transition-colors flex items-center gap-2"
          >
            <StarIcon className="w-4 h-4" />
            GitHub
          </a>
        </div>

        {/* Providers */}
        <div className="mt-10 flex items-center gap-8">
          {providers.map((p) => (
            <div key={p.name} className="flex items-center gap-2 text-landing-text-muted hover:text-white transition-colors">
              {p.icon}
              <span className="font-mono text-xs">{p.name}</span>
            </div>
          ))}
        </div>

        {/* Features Row */}
        <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl w-full">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="border border-landing-border p-4 text-center">
                <Icon className="w-5 h-5 text-white mx-auto mb-2" />
                <h3 className="font-mono text-white text-sm">{f.title}</h3>
                <p className="text-landing-text-muted text-xs mt-1">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-landing-border py-4">
        <p className="text-center text-landing-text-muted font-mono text-xs">
          probablyprofit • MIT License
        </p>
      </footer>
    </div>
  );
}
