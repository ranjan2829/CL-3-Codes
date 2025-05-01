import sys
import re
import os
import io
from contextlib import redirect_stdout

def mapper(input_file="sample.txt"):
    """
    Reads from input file and emits word and character counts
    """
    result = []
    try:
        with open(input_file, "r") as f:
            for line in f:
                line = line.strip()
                
                # Word processing
                words = re.findall(r'\w+', line.lower())
                for word in words:
                    # Using tab as separator and type identifier
                    result.append(f"{word}\t1\tword")
                
                # Character processing
                for char in line:
                    if char.isalpha():
                        result.append(f"{char.lower()}\t1\tchar")
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
        
    return result

def reducer(mapper_output):
    """
    Aggregates counts from mapper output
    """
    word_counts = {}
    char_counts = {}

    for line in mapper_output:
        parts = line.strip().split("\t")
        if len(parts) != 3:
            continue
            
        key, value, type_id = parts
        try:
            value = int(value)
        except ValueError:
            continue
            
        if type_id == "word":
            word_counts[key] = word_counts.get(key, 0) + value
        elif type_id == "char":
            char_counts[key] = char_counts.get(key, 0) + value

    # Print word counts
    print("\nWord Counts:")
    for word, count in sorted(word_counts.items()):
        print(f"{word}: {count}")
    
    # Print character counts
    print("\nCharacter Counts:")
    for char, count in sorted(char_counts.items()):
        print(f"{char}: {count}")
            
    # Print totals
    print(f"\nSummary:")
    print(f"Total unique words: {len(word_counts)}")
    print(f"Total unique characters: {len(char_counts)}")

if __name__ == '__main__':
    # Simple pipeline to run both mapper and reducer
    input_file = "sample.txt"  # Default input file
    
    # If command line argument is provided, use it as input file
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        input_file = sys.argv[1]
        
    print(f"Processing file: {input_file}")
    print("Running MapReduce word and character count...")
    
    # Capture mapper output and pass it to the reducer
    mapper_output = mapper(input_file)
    
    # Display mapper output for debugging (optional)
    print("\nMapper output (intermediate results):")
    for line in mapper_output[:10]:  # Show first 10 lines only
        print(line)
    if len(mapper_output) > 10:
        print("...")
    
    # Pass mapper output to reducer
    print("\nReducer output (final results):")
    reducer(mapper_output)