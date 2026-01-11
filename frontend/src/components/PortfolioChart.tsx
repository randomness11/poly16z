import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import { usePerformance } from '../hooks/useApi';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement
);

export function PortfolioChart() {
  const { data: performance } = usePerformance();
  const [history, setHistory] = useState<{ time: string; value: number }[]>([]);

  useEffect(() => {
    if (performance) {
      setHistory((prev) => {
        const newPoint = {
          time: new Date().toLocaleTimeString(),
          value: performance.current_capital,
        };
        const updated = [...prev, newPoint].slice(-30);
        return updated;
      });
    }
  }, [performance]);

  const chartData = {
    labels: history.map((h) => h.time),
    datasets: [
      {
        label: 'Portfolio Value',
        data: history.map((h) => h.value),
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: (context: { parsed: { y: number | null } }) => `$${(context.parsed.y ?? 0).toFixed(2)}`,
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#64748b',
          maxTicksLimit: 6,
        },
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#64748b',
          callback: (value: number | string) => `$${value}`,
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  return (
    <div className="glass rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Portfolio Value</h2>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

interface ExposureChartProps {
  cashBalance: number;
  exposureByCategory: Record<string, number>;
}

export function ExposureChart({ cashBalance, exposureByCategory }: ExposureChartProps) {
  const categories = Object.keys(exposureByCategory);
  const values = Object.values(exposureByCategory);

  const data = {
    labels: ['Cash', ...categories.map((c) => c.replace('_', ' '))],
    datasets: [
      {
        data: [cashBalance, ...values],
        backgroundColor: [
          '#22c55e',
          '#eab308',
          '#3b82f6',
          '#a855f7',
          '#ef4444',
          '#f97316',
          '#14b8a6',
        ],
        borderWidth: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: '#94a3b8',
          padding: 16,
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        callbacks: {
          label: (context: { label: string; parsed: number }) =>
            `${context.label}: $${context.parsed.toFixed(2)}`,
        },
      },
    },
  };

  return (
    <div className="h-48">
      <Doughnut data={data} options={options} />
    </div>
  );
}
