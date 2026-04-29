#!/bin/bash
# Run simulator at 10k eps for 30 seconds
make simulate RATE=10000 DURATION=30 &
SIM_PID=$!
sleep 5
# Measure API endpoint response time
for i in {1..20}; do
  curl -o /dev/null -s -w "Request $i: %{time_total}s\n" http://localhost:8000/api/v1/metrics/live
  sleep 1
done
kill $SIM_PID