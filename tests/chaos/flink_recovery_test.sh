#!/bin/bash
# Kill a Flink TaskManager pod and verify that the job recovers within 30 seconds
NAMESPACE=${1:-streammind}

echo "🔍 Locating a Flink TaskManager pod..."
TM_POD=$(kubectl -n $NAMESPACE get pods -l app=flink,component=taskmanager -o name | head -1)
if [ -z "$TM_POD" ]; then
  echo "No Flink TaskManager found. Is Flink operator running?"
  exit 1
fi

echo "🪓 Killing $TM_POD"
kubectl -n $NAMESPACE delete $TM_POD --grace-period=0 --force

echo "⏳ Waiting for job recovery..."
START=$(date +%s)
RECOVERED=false
while [ $(( $(date +%s) - START )) -lt 60 ]; do
  # Check if the Flink job is running (look for job status in Flink deployment)
  JOB_STATUS=$(kubectl -n $NAMESPACE get flinkdeployment trending-aggregator -o jsonpath='{.status.jobStatus.state}')
  if [ "$JOB_STATUS" == "RUNNING" ]; then
    RECOVERED=true
    break
  fi
  sleep 2
done

if [ "$RECOVERED" = true ]; then
  ELAPSED=$(( $(date +%s) - START ))
  echo "✅ Job recovered in $ELAPSED seconds"
  if [ $ELAPSED -le 30 ]; then
    echo "🎉 Recovery within 30 seconds target."
  else
    echo "⚠️ Recovery took $ELAPSED seconds (exceeds 30s)."
  fi
else
  echo "❌ Job did not recover within 60 seconds."
  exit 1
fi