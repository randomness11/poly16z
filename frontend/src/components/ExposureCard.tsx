import { RefreshCw, AlertTriangle } from 'lucide-react';
import { useExposure } from '../hooks/useApi';
import { ExposureChart } from './PortfolioChart';
import clsx from 'clsx';

export function ExposureCard() {
  const { data, loading, refresh } = useExposure();

  if (loading || !data) {
    return (
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Portfolio Exposure</h2>
        <div className="animate-pulse space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-slate-700/50 rounded" />
            ))}
          </div>
          <div className="h-48 bg-slate-700/50 rounded" />
        </div>
      </div>
    );
  }

  const { risk_metrics, warnings, correlation_groups, exposure_by_category, cash_balance, total_exposure } = data;

  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Portfolio Exposure</h2>
        <button
          onClick={refresh}
          className="p-2 rounded-lg text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-4 space-y-2">
          {warnings.map((warning, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-300"
            >
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {warning}
            </div>
          ))}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Total Exposure</div>
          <div className="text-xl font-bold text-yellow-400">
            ${total_exposure.toFixed(2)}
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Cash Balance</div>
          <div className="text-xl font-bold text-green-400">
            ${cash_balance.toFixed(2)}
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Exposure %</div>
          <div className={clsx(
            'text-xl font-bold',
            risk_metrics.exposure_pct > 80 ? 'text-red-400' :
            risk_metrics.exposure_pct > 50 ? 'text-yellow-400' : 'text-green-400'
          )}>
            {risk_metrics.exposure_pct.toFixed(1)}%
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Daily Loss Used</div>
          <div className={clsx(
            'text-xl font-bold',
            risk_metrics.daily_loss_limit_used > 75 ? 'text-red-400' :
            risk_metrics.daily_loss_limit_used > 50 ? 'text-yellow-400' : 'text-green-400'
          )}>
            {risk_metrics.daily_loss_limit_used.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Correlation Groups */}
      {correlation_groups.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-slate-400 mb-3">Correlation Groups</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {correlation_groups.map((group) => (
              <div
                key={group.group_name}
                className={clsx(
                  'rounded-lg p-3 border',
                  group.risk_level === 'high' && 'bg-red-500/10 border-red-500/30',
                  group.risk_level === 'medium' && 'bg-yellow-500/10 border-yellow-500/30',
                  group.risk_level === 'low' && 'bg-green-500/10 border-green-500/30'
                )}
              >
                <div className="font-semibold text-sm capitalize">
                  {group.group_name.replace('_', ' ')}
                </div>
                <div className={clsx(
                  'text-lg font-bold',
                  group.risk_level === 'high' && 'text-red-400',
                  group.risk_level === 'medium' && 'text-yellow-400',
                  group.risk_level === 'low' && 'text-green-400'
                )}>
                  ${group.total_exposure.toFixed(2)}
                </div>
                <div className="text-xs text-slate-400">
                  {group.positions_count} positions
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Exposure Chart */}
      <ExposureChart
        cashBalance={cash_balance}
        exposureByCategory={exposure_by_category}
      />
    </div>
  );
}
