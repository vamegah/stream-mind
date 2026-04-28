import { useState } from 'react';
import axios from 'axios';

export default function AIChatPanel() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/ai/chat', { query });
      setAnswer(res.data.answer);
    } catch (err) {
      setAnswer('Sorry, something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg mt-4">
      <h2 className="text-xl mb-2">AI Assistant (Apple Intelligence)</h2>
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about metrics, anomalies, trends..."
          className="flex-1 p-2 rounded bg-gray-700 text-white"
          onKeyPress={(e) => e.key === 'Enter' && ask()}
        />
        <button onClick={ask} className="bg-blue-600 px-4 py-2 rounded" disabled={loading}>
          {loading ? '...' : 'Ask'}
        </button>
      </div>
      {answer && (
        <div className="mt-3 p-3 bg-gray-700 rounded whitespace-pre-wrap">
          {answer}
        </div>
      )}
    </div>
  );
}