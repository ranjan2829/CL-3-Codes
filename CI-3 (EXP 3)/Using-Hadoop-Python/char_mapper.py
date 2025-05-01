#!/usr/bin/env python3
import sys

for line in sys.stdin:
    for char in line.strip():
        print(f"{char}\t1")
