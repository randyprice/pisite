#!/bin/sh
output_file="$1"; shift
sleep_interval_sec="$1"; shift

trap 'echo exiting; exit 0' INT TERM

while true; do
    podman --remote ps --format json > "$output_file"
    sleep "$sleep_interval_sec" &
    wait $!
done
