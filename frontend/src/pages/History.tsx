import { useState, useMemo } from 'react';
import { Download, Filter, Calendar, ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react';
import { useTrades } from '../hooks/useApi';

type SortField = 'timestamp' | 'market' | 'side' | 'size' | 'price' | 'pnl';
type SortOrder = 'asc' | 'desc';

export function History() {
  const { data: trades, loading, error } = useTrades(200);
  const [filter, setFilter] = useState<'all' | 'buy' | 'sell'>('all');
  const [dateRange, setDateRange] = useState<'all' | '7d' | '30d' | '90d'>('all');
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [search, setSearch] = useState('');

  const filteredTrades = useMemo(() => {
    let result = [...trades];

    // Filter by side
    if (filter !== 'all') {
      result = result.filter(t => t.side.toLowerCase() === filter);
    }

    // Filter by date range
    if (dateRange !== 'all') {
      const days = parseInt(dateRange);
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);
      result = result.filter(t => new Date(t.timestamp) >= cutoff);
    }

    // Filter by search
    if (search) {
      const lower = search.toLowerCase();
      result = result.filter(t =>
        t.market_name?.toLowerCase().includes(lower) ||
        t.market_id?.toLowerCase().includes(lower)
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'timestamp':
          comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          break;
        case 'market':
          comparison = (a.market_name || '').localeCompare(b.market_name || '');
          break;
        case 'side':
          comparison = a.side.localeCompare(b.side);
          break;
        case 'size':
          comparison = a.size - b.size;
          break;
        case 'price':
          comparison = a.price - b.price;
          break;
        case 'pnl':
          comparison = (a.realized_pnl || 0) - (b.realized_pnl || 0);
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [trades, filter, dateRange, search, sortField, sortOrder]);

  const stats = useMemo(() => {
    const wins = filteredTrades.filter(t => (t.realized_pnl || 0) > 0).length;
    const losses = filteredTrades.filter(t => (t.realized_pnl || 0) < 0).length;
    const totalPnl = filteredTrades.reduce((sum, t) => sum + (t.realized_pnl || 0), 0);
    const totalVolume = filteredTrades.reduce((sum, t) => sum + (t.size * t.price), 0);

    return {
      total: filteredTrades.length,
      wins,
      losses,
      winRate: filteredTrades.length > 0 ? (wins / filteredTrades.length) * 100 : 0,
      totalPnl,
      totalVolume,
    };
  }, [filteredTrades]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const exportToCSV = () => {
    const headers = ['Timestamp', 'Market', 'Side', 'Outcome', 'Size', 'Price', 'P&L'];
    const rows = filteredTrades.map(t => [
      new Date(t.timestamp).toISOString(),
      t.market_name || t.market_id,
      t.side,
      t.outcome,
      t.size.toFixed(2),
      t.price.toFixed(4),
      (t.realized_pnl || 0).toFixed(2),
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-1">Total Trades</p>
          <p className="text-2xl font-bold text-white">{stats.total}</p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-1">Win Rate</p>
          <p className={`text-2xl font-bold ${stats.winRate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.winRate.toFixed(1)}%
          </p>
          <p className="text-xs text-slate-500">{stats.wins}W / {stats.losses}L</p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-1">Total P&L</p>
          <p className={`text-2xl font-bold ${stats.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(stats.totalPnl)}
          </p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-1">Volume</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(stats.totalVolume)}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="glass rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search markets..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Side Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            {(['all', 'buy', 'sell'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  filter === f
                    ? 'bg-purple-500/20 text-purple-400'
                    : 'text-slate-400 hover:bg-white/5'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          {/* Date Range */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            {(['all', '7d', '30d', '90d'] as const).map(d => (
              <button
                key={d}
                onClick={() => setDateRange(d)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  dateRange === d
                    ? 'bg-purple-500/20 text-purple-400'
                    : 'text-slate-400 hover:bg-white/5'
                }`}
              >
                {d === 'all' ? 'All Time' : d}
              </button>
            ))}
          </div>

          {/* Export */}
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Trades Table */}
      <div className="glass rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading trades...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-400">{error}</div>
        ) : filteredTrades.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No trades found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  {[
                    { key: 'timestamp', label: 'Time' },
                    { key: 'market', label: 'Market' },
                    { key: 'side', label: 'Side' },
                    { key: 'size', label: 'Size' },
                    { key: 'price', label: 'Price' },
                    { key: 'pnl', label: 'P&L' },
                  ].map(col => (
                    <th
                      key={col.key}
                      onClick={() => handleSort(col.key as SortField)}
                      className="px-4 py-3 text-left text-sm font-medium text-slate-400 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-2">
                        {col.label}
                        {sortField === col.key && (
                          <ArrowUpDown className={`w-3 h-3 ${sortOrder === 'asc' ? 'rotate-180' : ''}`} />
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((trade, i) => (
                  <tr
                    key={trade.id || i}
                    className="border-b border-slate-700/50 hover:bg-white/5"
                  >
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="max-w-[300px] truncate text-sm text-white">
                        {trade.market_name || trade.market_id}
                      </div>
                      <div className="text-xs text-slate-500">{trade.outcome}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                        trade.side.toLowerCase() === 'buy'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.side.toLowerCase() === 'buy' ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-white font-mono">
                      ${trade.size.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300 font-mono">
                      ${trade.price.toFixed(4)}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono">
                      <span className={
                        (trade.realized_pnl || 0) > 0
                          ? 'text-green-400'
                          : (trade.realized_pnl || 0) < 0
                          ? 'text-red-400'
                          : 'text-slate-400'
                      }>
                        {(trade.realized_pnl || 0) >= 0 ? '+' : ''}
                        {formatCurrency(trade.realized_pnl || 0)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
