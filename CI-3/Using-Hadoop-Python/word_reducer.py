#!/usr/bin/env python3
import sys

current_word = None
word_count = 0

for line in sys.stdin:
    word, count = line.strip().split("\t")
    count = int(count)

    if current_word == word:
        word_count += count
    else:
        if current_word:
            print(f"{current_word}\t{word_count}")
        current_word = word
        word_count = count

if current_word:
    print(f"{current_word}\t{word_count}")
