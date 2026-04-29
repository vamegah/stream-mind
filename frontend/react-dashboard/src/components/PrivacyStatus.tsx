import { useEffect, useState } from 'react';
import axios from 'axios';

export default function PrivacyStatus() {
  const [budget, setBudget] = useState<number | null>(null);
  const [userToken, setUserToken] = useState('');

  // For demo, we'll ask user to input a token (or use a dummy)
  const fetchBudget = async (token: string) => {
    if (!token) return;
    try {
      const res = await axios.get(`/api/v1/privacy/budget/${token}`);
      setBudget(res.data.remaining_budget);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    // Generate a random token for this session
    const dummyToken = 'user_' + Math.random().toString(36).substring(7);
    setUserToken(dummyToken);
    fetchBudget(dummyToken);
  }, []);

  const handleQuery = async () => {
    // Call the user history endpoint to consume budget
    try {
      const res = await axios.get(`/api/v1/user/${userToken}/history`);
      alert(JSON.stringify(res.data));
      fetchBudget(userToken); // refresh budget
    } catch (err) {
      alert('Error: ' + err);
    }
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg mt-4">
      <h2 className="text-xl mb-2">Privacy Budget (Apple-style)</h2>
      <p className="text-sm text-gray-300">Each query that accesses personal data costs ε=0.1. Daily budget ε=1.0.</p>
      <div className="mt-2">
        <span className="font-mono">Your token: {userToken}</span>
        <div className="mt-2">
          <span>Remaining budget: </span>
          <span className={`font-bold ${budget !== null && budget < 0.2 ? 'text-red-400' : 'text-green-400'}`}>
            {budget !== null ? budget.toFixed(2) : '?'}
          </span>
          / 1.0 ε
        </div>
        <button
          onClick={handleQuery}
          className="mt-3 bg-purple-600 px-4 py-2 rounded text-sm"
          disabled={budget !== null && budget < 0.1}
        >
          Query Personal Data (consumes budget)
        </button>
        {budget !== null && budget < 0.1 && (
          <p className="text-red-400 text-sm mt-2">Budget exhausted – returning only aggregated data.</p>
        )}
      </div>
    </div>
  );
}