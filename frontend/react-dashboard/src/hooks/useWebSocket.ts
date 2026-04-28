import useWebSocket from 'react-use-websocket';

export const useMetricsWebSocket = () => {
  const { lastJsonMessage, readyState } = useWebSocket('ws://localhost:8000/ws/metrics', {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });
  return { metrics: lastJsonMessage as any, readyState };
};