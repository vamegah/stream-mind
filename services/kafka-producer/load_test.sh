#!/bin/bash
# Run simulator at 1000 events/sec for 60 seconds (or until Ctrl+C)

RATE=${1:-1000}
DURATION=${2:-60}

echo "Simulating $RATE events/sec for $DURATION seconds..."
python simulator.py --rate $RATE --duration $DURATION