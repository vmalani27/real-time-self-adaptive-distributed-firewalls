#!/bin/bash
# Capture packets for post-analysis
# Usage: ./tcpdump_capture.sh <interface> <output_file>
tcpdump -i "$1" -w "$2" 