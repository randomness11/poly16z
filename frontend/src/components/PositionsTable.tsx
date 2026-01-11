import { usePositions } from '../hooks/useApi';
import clsx from 'clsx';

export function PositionsTable() {
  const { data: positions, loading } = usePositions();

  if (loading) {
    return (
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Open Positions</h2>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-slate-700/50 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Open Positions</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-slate-400 border-b border-white/10">
              <th className="pb-3 font-medium">Market</th>
              <th className="pb-3 font-medium">Side</th>
              <th className="pb-3 font-medium text-right">Size</th>
              <th className="pb-3 font-medium text-right">Entry</th>
              <th className="pb-3 font-medium text-right">Current</th>
              <th className="pb-3 font-medium text-right">P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No open positions
                </td>
              </tr>
            ) : (
              positions.map((position) => {
                const pnlPct = position.avg_price > 0
                  ? ((position.current_price - position.avg_price) / position.avg_price) * 100
                  : 0;

                return (
                  <tr
                    key={position.market_id}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="py-3">
                      <span className="text-sm text-white">
                        {position.market_id.slice(0, 20)}...
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        position.outcome === 'Yes'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      )}>
                        {position.outcome}
                      </span>
                    </td>
                    <td className="py-3 text-right font-mono text-sm">
                      {position.size.toFixed(2)}
                    </td>
                    <td className="py-3 text-right font-mono text-sm text-slate-400">
                      ${position.avg_price.toFixed(2)}
                    </td>
                    <td className="py-3 text-right font-mono text-sm">
                      ${position.current_price.toFixed(2)}
                    </td>
                    <td className={clsx(
                      'py-3 text-right font-mono text-sm',
                      position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    )}>
                      {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                      <span className="text-xs ml-1 opacity-70">
                        ({pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%)
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
