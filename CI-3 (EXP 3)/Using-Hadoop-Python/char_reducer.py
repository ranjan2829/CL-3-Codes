#!/usr/bin/env python3
import sys

current_char = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    
    # Skip empty lines or handle malformed input
    if not line or '\t' not in line:
        continue
        
    char, count = line.split('\t')
    
    try:
        count = int(count)
    except ValueError:
        continue

    if current_char == char:
        current_count += count
    else:
        if current_char:
            print(f"{current_char}\t{current_count}")
        current_char = char
        current_count = count

# Output the last character
if current_char:
    print(f"{current_char}\t{current_count}")