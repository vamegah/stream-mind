import { useEffect, useState } from 'react';
import axios from 'axios';

interface Anomaly {
  anomaly_id: string;
  content_id: string;
  detected_at: string;
  drop_percent: number;
  resolved: boolean;
}

export default function AnomalyTimeline() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  useEffect(() => {
    const fetchAnomalies = async () => {
      const res = await axios.get('/api/v1/anomalies?limit=10');
      setAnomalies(res.data);
    };
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-800 p-4 rounded-lg mt-4">
      <h2 className="text-xl mb-2">Recent Anomalies</h2>
      {anomalies.length === 0 && <p className="text-gray-400">No anomalies detected.</p>}
      <ul className="space-y-2">
        {anomalies.map((a) => (
          <li key={a.anomaly_id} className="border-l-4 border-red-500 pl-3">
            <span className="font-mono">{a.content_id}</span> – drop {a.drop_percent.toFixed(1)}% at {new Date(a.detected_at).toLocaleTimeString()}
            {a.resolved ? ' ✅' : ' ⚠️'}
          </li>
        ))}
      </ul>
    </div>
  );
}