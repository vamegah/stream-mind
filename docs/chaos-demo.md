# Chaos Demo: Flink TaskManager Kill & Recovery

## Prerequisites
- StreamMind deployed on minikube/K8s with Flink operator.
- Simulator running (e.g., `make simulate` at 1000 events/sec).
- Locust load test running in background.

## Steps to Record

1. **Start recording** (OBS, QuickTime, etc.)
2. Show the dashboard (http://streammind.local) updating normally.
3. Open terminal and run `./tests/chaos/flink_recovery_test.sh`.
4. Observe the TaskManager pod being terminated.
5. **Expected behaviour**:
   - Dashboard may freeze for a few seconds.
   - After 5-15 seconds, data resumes flowing.
   - Flink job automatically restarts (thanks to Kubernetes and checkpointing).
6. Stop recording.
7. **Edit video** to highlight the recovery time (show timestamps).

## Example Output in Terminal
