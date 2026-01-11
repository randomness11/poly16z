import type { ReactNode } from 'react';
import clsx from 'clsx';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'green' | 'red' | 'blue' | 'purple' | 'yellow' | 'default';
}

const colorClasses = {
  green: 'text-green-400',
  red: 'text-red-400',
  blue: 'text-blue-400',
  purple: 'text-purple-400',
  yellow: 'text-yellow-400',
  default: 'text-white',
};

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'default',
}: StatCardProps) {
  return (
    <div className="glass rounded-xl p-5 hover:bg-white/5 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{title}</p>
          <p className={clsx('text-2xl font-bold', colorClasses[color])}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
          )}
          {trend && trendValue && (
            <div className={clsx(
              'flex items-center gap-1 mt-2 text-xs',
              trend === 'up' && 'text-green-400',
              trend === 'down' && 'text-red-400',
              trend === 'neutral' && 'text-slate-400',
            )}>
              {trend === 'up' && '↑'}
              {trend === 'down' && '↓'}
              {trend === 'neutral' && '→'}
              {trendValue}
            </div>
          )}
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-white/5">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="glass rounded-xl p-5 animate-pulse">
      <div className="h-4 w-20 bg-slate-700 rounded mb-2" />
      <div className="h-8 w-32 bg-slate-700 rounded" />
    </div>
  );
}
