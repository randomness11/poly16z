import { Zap, RefreshCw, TrendingUp } from 'lucide-react';
import { useArbitrage } from '../hooks/useApi';
import type { ArbitrageOpportunity } from '../types/api';
import clsx from 'clsx';

export function ArbitrageCard() {
  const { data, scanning, scan } = useArbitrage();

  const opportunities: ArbitrageOpportunity[] = data?.opportunities || [];
  const bestProfit = opportunities.length > 0
    ? Math.max(...opportunities.map((o: ArbitrageOpportunity) => o.net_profit_pct))
    : 0;
  const avgConfidence = opportunities.length > 0
    ? opportunities.reduce((sum: number, o: ArbitrageOpportunity) => sum + o.confidence, 0) / opportunities.length
    : 0;

  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold">Arbitrage Opportunities</h2>
        </div>
        <div className="flex items-center gap-3">
          {data?.last_scan && (
            <span className="text-xs text-slate-400">
              Last scan: {new Date(data.last_scan).toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={scan}
            disabled={scanning}
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
              scanning
                ? 'bg-purple-500/30 text-purple-300 cursor-not-allowed'
                : 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30'
            )}
          >
            <RefreshCw className={clsx('w-4 h-4', scanning && 'animate-spin')} />
            {scanning ? 'Scanning...' : 'Scan Markets'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Opportunities</div>
          <div className="text-xl font-bold text-purple-400">
            {opportunities.length}
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Best Profit</div>
          <div className="text-xl font-bold text-green-400">
            {(bestProfit * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Matched Pairs</div>
          <div className="text-xl font-bold text-blue-400">
            {data?.matched_pairs_count || 0}
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-xs text-slate-400 mb-1">Avg Confidence</div>
          <div className="text-xl font-bold">
            {(avgConfidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Opportunities List */}
      <div className="space-y-3">
        {opportunities.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            {data?.last_scan
              ? 'No arbitrage opportunities found. Markets are efficiently priced.'
              : 'Click "Scan Markets" to detect arbitrage opportunities'}
          </div>
        ) : (
          opportunities.map((opp: ArbitrageOpportunity, i: number) => (
            <OpportunityCard key={i} opportunity={opp} />
          ))
        )}
      </div>
    </div>
  );
}

interface OpportunityCardProps {
  opportunity: {
    net_profit_pct: number;
    confidence: number;
    polymarket_question: string;
    buy_side: string;
    buy_platform: string;
    buy_price: number;
    sell_side: string;
    sell_platform: string;
    sell_price: number;
    combined_cost: number;
  };
}

function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const profitColor = opportunity.net_profit_pct > 0.05 ? 'green' :
    opportunity.net_profit_pct > 0.02 ? 'yellow' : 'slate';

  return (
    <div className={clsx(
      'bg-white/5 rounded-lg p-4 border',
      profitColor === 'green' && 'border-green-500/30',
      profitColor === 'yellow' && 'border-yellow-500/30',
      profitColor === 'slate' && 'border-slate-500/30'
    )}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <TrendingUp className={clsx(
              'w-4 h-4',
              profitColor === 'green' && 'text-green-400',
              profitColor === 'yellow' && 'text-yellow-400',
              profitColor === 'slate' && 'text-slate-400'
            )} />
            <span className={clsx(
              'font-semibold',
              profitColor === 'green' && 'text-green-400',
              profitColor === 'yellow' && 'text-yellow-400',
              profitColor === 'slate' && 'text-slate-400'
            )}>
              {(opportunity.net_profit_pct * 100).toFixed(1)}% Profit
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 line-clamp-2">
            {opportunity.polymarket_question}
          </p>
        </div>
        <div className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
          {(opportunity.confidence * 100).toFixed(0)}% conf
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-blue-500/10 rounded p-2">
          <div className="text-blue-400 font-medium">
            Buy {opportunity.buy_side.toUpperCase()}
          </div>
          <div className="text-slate-300">{opportunity.buy_platform}</div>
          <div className="text-white font-bold">
            {(opportunity.buy_price * 100).toFixed(1)}¢
          </div>
        </div>
        <div className="bg-green-500/10 rounded p-2">
          <div className="text-green-400 font-medium">
            Buy {opportunity.sell_side.toUpperCase()}
          </div>
          <div className="text-slate-300">{opportunity.sell_platform}</div>
          <div className="text-white font-bold">
            {(opportunity.sell_price * 100).toFixed(1)}¢
          </div>
        </div>
      </div>

      <div className="mt-2 text-xs text-slate-400">
        Combined: {(opportunity.combined_cost * 100).toFixed(1)}¢ → Guaranteed $1.00 payout
      </div>
    </div>
  );
}
