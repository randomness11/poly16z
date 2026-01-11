import { Bot, Wifi, WifiOff, Play, Square, Settings } from 'lucide-react';
import { useStatus, useWebSocket, useAgentControl } from '../hooks/useApi';
import clsx from 'clsx';

export function Header() {
  const { data: status } = useStatus();
  const { connected } = useWebSocket();
  const { start, stop, loading } = useAgentControl();

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">probablyprofit</h1>
              <p className="text-xs text-slate-400">AI Trading Bot</p>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center gap-6">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              {connected ? (
                <>
                  <Wifi className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-green-400">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-red-400" />
                  <span className="text-sm text-red-400">Disconnected</span>
                </>
              )}
            </div>

            {/* Agent Info */}
            {status && (
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Agent:</span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono text-xs">
                    {status.agent_type}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Strategy:</span>
                  <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 font-mono text-xs">
                    {status.strategy}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Mode:</span>
                  <span className={clsx(
                    'px-2 py-0.5 rounded font-mono text-xs',
                    status.dry_run
                      ? 'bg-yellow-500/20 text-yellow-400'
                      : 'bg-green-500/20 text-green-400'
                  )}>
                    {status.dry_run ? 'Dry Run' : 'Live'}
                  </span>
                </div>
                <div className="text-slate-400">
                  Uptime: <span className="text-white">{formatUptime(status.uptime_seconds)}</span>
                </div>
              </div>
            )}

            {/* Controls */}
            <div className="flex items-center gap-2">
              {status?.running ? (
                <button
                  onClick={stop}
                  disabled={loading}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors disabled:opacity-50"
                >
                  <Square className="w-4 h-4" />
                  Stop
                </button>
              ) : (
                <button
                  onClick={start}
                  disabled={loading}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  Start
                </button>
              )}
              <button className="p-1.5 rounded-lg text-slate-400 hover:bg-white/5 transition-colors">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
