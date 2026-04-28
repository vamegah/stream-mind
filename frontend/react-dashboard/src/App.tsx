import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useMetricsWebSocket } from './hooks/useWebSocket';

interface MetricPoint {
  timestamp: number;
  topContent: string;
  count: number;
}

function App() {
  const { metrics, readyState } = useMetricsWebSocket();
  const [chartData, setChartData] = useState<MetricPoint[]>([]);
  const [activeUsers, setActiveUsers] = useState(0);

  useEffect(() => {
    if (metrics) {
      // For chart, we'll store the top trending item's count over time
      const topTrending = metrics.trending?.[0];
      const newPoint = {
        timestamp: metrics.timestamp,
        topContent: topTrending?.content_id || 'none',
        count: topTrending?.count || 0,
      };
      setChartData(prev => [...prev.slice(-20), newPoint]); // keep last 20 points
      setActiveUsers(metrics.active_users);
    }
  }, [metrics]);

  const connectionStatus = {
    0: 'Connecting',
    1: 'Open',
    2: 'Closing',
    3: 'Closed',
  }[readyState];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-4">StreamMind – Apple TV Analytics</h1>
      <div className="mb-4 text-sm">WebSocket: {connectionStatus}</div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl mb-2">Real‑Time Trending (Top Content)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={(ts) => new Date(ts).toLocaleTimeString()} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#8884d8" name="Play Count" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl mb-2">Active Users (Simulated)</h2>
          <div className="text-5xl font-mono">{activeUsers}</div>
          <div className="mt-4 text-sm text-gray-400">Approximate unique users in last 5 minutes</div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg col-span-2">
          <h2 className="text-xl mb-2">Top 10 Trending Now</h2>
          <ul className="list-disc pl-5">
            {metrics?.trending?.slice(0, 5).map((item: any) => (
              <li key={item.content_id}>{item.content_id} – {item.count} plays in last minute</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;