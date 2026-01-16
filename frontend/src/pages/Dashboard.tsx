import { DollarSign, TrendingUp, Wallet, Activity } from 'lucide-react';
import {
  StatCard,
  StatCardSkeleton,
  PortfolioChart,
  PositionsTable,
  ExposureCard,
  ArbitrageCard,
} from '../components';
import { useStatus, usePerformance } from '../hooks/useApi';

function StatusItem({ label, value, variant = 'default' }: {
  label: string;
  value: string;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple';
}) {
  const variantClasses = {
    default: 'bg-slate-500/20 text-slate-300',
    success: 'bg-green-500/20 text-green-400',
    warning: 'bg-yellow-500/20 text-yellow-400',
    error: 'bg-red-500/20 text-red-400',
    info: 'bg-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={`px-2 py-0.5 rounded text-xs font-mono ${variantClasses[variant]}`}>
        {value}
      </span>
    </div>
  );
}

export function Dashboard() {
  const { data: status } = useStatus();
  const { data: performance, loading: perfLoading } = usePerformance();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
  };

  return (
    <>
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {perfLoading || !performance ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <StatCard
              title="Balance"
              value={formatCurrency(performance.current_capital)}
              subtitle={`Initial: ${formatCurrency(performance.initial_capital)}`}
              icon={<Wallet className="w-5 h-5 text-green-400" />}
              color="green"
              trend={performance.total_return >= 0 ? 'up' : 'down'}
              trendValue={formatPercent(performance.total_return_pct)}
            />
            <StatCard
              title="Today's P&L"
              value={formatCurrency(performance.daily_pnl)}
              icon={<DollarSign className="w-5 h-5 text-blue-400" />}
              color={performance.daily_pnl >= 0 ? 'green' : 'red'}
            />
            <StatCard
              title="Open Positions"
              value={status?.positions_count || 0}
              subtitle={`Loop count: ${status?.loop_count || 0}`}
              icon={<Activity className="w-5 h-5 text-purple-400" />}
              color="purple"
            />
            <StatCard
              title="Win Rate"
              value={`${(performance.win_rate * 100).toFixed(1)}%`}
              subtitle={`${performance.total_trades} total trades`}
              icon={<TrendingUp className="w-5 h-5 text-yellow-400" />}
              color={performance.win_rate >= 0.5 ? 'green' : 'yellow'}
            />
          </>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Portfolio Chart - 2 cols */}
        <div className="lg:col-span-2">
          <PortfolioChart />
        </div>

        {/* Bot Status Card */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Bot Status</h2>
          <div className="space-y-4">
            <StatusItem label="Status" value={status?.running ? 'Running' : 'Stopped'} variant={status?.running ? 'success' : 'default'} />
            <StatusItem label="Agent" value={status?.agent_name || 'Unknown'} />
            <StatusItem label="Agent Type" value={status?.agent_type || 'Unknown'} variant="info" />
            <StatusItem label="Strategy" value={status?.strategy || 'Unknown'} variant="purple" />
            <StatusItem label="Mode" value={status?.dry_run ? 'Dry Run' : 'Live'} variant={status?.dry_run ? 'warning' : 'success'} />
            <StatusItem
              label="Last Observation"
              value={status?.last_observation
                ? new Date(status.last_observation).toLocaleTimeString()
                : 'Never'}
            />
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="mb-8">
        <PositionsTable />
      </div>

      {/* Exposure & Arbitrage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ExposureCard />
        <ArbitrageCard />
      </div>
    </>
  );
}
