import re

def mapper(input_file="sample.txt"):
    result = []
    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            words = re.findall(r'\w+', line.lower())
            for word in words:
                result.append(f"{word}\t1\tword")
            for char in line:
                if char.isalpha():
                    result.append(f"{char.lower()}\t1\tchar")
    return result

def reducer(mapper_output):
    word_counts, char_counts = {}, {}
    for line in mapper_output:
        parts = line.strip().split("\t")
        if len(parts) != 3:
            continue
        key, value, type_id = parts
        value = int(value)
        if type_id == "word":
            word_counts[key] = word_counts.get(key, 0) + value
        elif type_id == "char":
            char_counts[key] = char_counts.get(key, 0) + value
    print("Word Counts:")
    for word in sorted(word_counts):
        print(f"{word}: {word_counts[word]}")
    print("Character Counts:")
    for char in sorted(char_counts):
        print(f"{char}: {char_counts[char]}")
    print(f"Summary:\nTotal unique words: {len(word_counts)}\nTotal unique characters: {len(char_counts)}")

if __name__ == '__main__':
    input_file = "sample.txt"
    print("Running MapReduce word and character count...")
    mapper_output = mapper(input_file)
    print("Reducer output:")
    reducer(mapper_output)
