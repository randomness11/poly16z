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
    <div className="glass rounded-xl p-5 card-hover group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1 group-hover:text-slate-300 transition-colors">
            {title}
          </p>
          <p className={clsx(
            'text-2xl font-bold font-mono-numbers animate-fade-in',
            colorClasses[color]
          )}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
          )}
          {trend && trendValue && (
            <div className={clsx(
              'flex items-center gap-1 mt-2 text-xs font-medium',
              trend === 'up' && 'text-green-400',
              trend === 'down' && 'text-red-400',
              trend === 'neutral' && 'text-slate-400',
            )}>
              <span className={clsx(
                'inline-block transition-transform',
                trend === 'up' && 'group-hover:-translate-y-0.5',
                trend === 'down' && 'group-hover:translate-y-0.5',
              )}>
                {trend === 'up' && '↑'}
                {trend === 'down' && '↓'}
                {trend === 'neutral' && '→'}
              </span>
              {trendValue}
            </div>
          )}
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-white/5 group-hover:bg-white/10 transition-colors">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="glass rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="h-4 w-20 skeleton rounded mb-3" />
          <div className="h-8 w-32 skeleton rounded mb-2" />
          <div className="h-3 w-24 skeleton rounded" />
        </div>
        <div className="w-9 h-9 skeleton rounded-lg" />
      </div>
    </div>
  );
}
