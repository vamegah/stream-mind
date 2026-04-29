#!/bin/bash
# Chaos script: kills a random pod in the streammind namespace every N seconds
# Usage: ./kill_random_pod.sh [interval_seconds] [namespace]

NAMESPACE=${2:-streammind}
INTERVAL=${1:-30}

echo "🔪 Chaos Monkey starting: will kill a random pod every $INTERVAL seconds in namespace $NAMESPACE"
echo "Press Ctrl+C to stop."

while true; do
  # Get all pods in the namespace, exclude those with 'kafka' (stateful) or 'cassandra' (data loss risk) – but we can kill them too for resilience test
  PODS=$(kubectl -n $NAMESPACE get pods -o name | grep -v "kafka" | grep -v "cassandra" | grep -v "zookeeper")
  if [ -z "$PODS" ]; then
    echo "No eligible pods found."
  else
    RANDOM_POD=$(echo "$PODS" | shuf -n 1)
    echo "$(date): Killing $RANDOM_POD"
    kubectl -n $NAMESPACE delete $RANDOM_POD --grace-period=0 --force
  fi
  sleep $INTERVAL
done