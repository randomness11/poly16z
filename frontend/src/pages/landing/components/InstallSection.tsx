import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export function InstallSection() {
  const [copied, setCopied] = useState(false);
  const command = 'pip install probablyprofit';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="flex justify-center py-12 px-4">
      <div className="flex items-center gap-4 bg-landing-border/50 border border-landing-border px-6 py-4">
        <span className="text-landing-text-muted font-mono">$</span>
        <code className="font-mono text-white text-sm sm:text-base">
          {command}
        </code>
        <button
          onClick={handleCopy}
          className="ml-4 p-2 text-landing-text-muted hover:text-white transition-colors"
          aria-label="Copy to clipboard"
        >
          {copied ? (
            <Check className="w-4 h-4 text-landing-accent" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>
      </div>
    </section>
  );
}
