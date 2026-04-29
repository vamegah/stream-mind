#!/bin/bash
# Measure p99 latency of /api/v1/metrics/live endpoint over 1 minute

ENDPOINT=${1:-"http://localhost:8000/api/v1/metrics/live"}
DURATION=60
SAMPLE_INTERVAL=0.5  # seconds

echo "Measuring latency for $DURATION seconds against $ENDPOINT"
TEMP_FILE=$(mktemp)

END_TIME=$((SECONDS + DURATION))
while [ $SECONDS -lt $END_TIME ]; do
  curl -o /dev/null -s -w "%{time_total}\n" $ENDPOINT >> $TEMP_FILE
  sleep $SAMPLE_INTERVAL
done

# Sort and compute p99
SORTED=$(sort -n $TEMP_FILE)
COUNT=$(cat $TEMP_FILE | wc -l)
PERCENTILE_INDEX=$(echo "$COUNT * 0.99" | bc | xargs printf "%.0f")
P99=$(echo "$SORTED" | sed -n "${PERCENTILE_INDEX}p")
echo "p99 latency: $P99 seconds"

# Check if below 0.5 sec
if (( $(echo "$P99 < 0.5" | bc -l) )); then
  echo "✅ Latency is within target (< 500ms)"
else
  echo "❌ Latency too high: $P99 sec"
  exit 1
fi
rm $TEMP_FILE