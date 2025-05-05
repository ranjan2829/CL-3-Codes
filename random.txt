import csv
from collections import defaultdict

# Simulate Mapper: Read CSV and emit (year, temp)
def mapper(file_path):
    mapped_data = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            try:
                year = row[0]
                temp = float(row[1])
                mapped_data.append((year, temp))
            except:
                continue
    return mapped_data

# Simulate Shuffle and Sort: Group by year (in this case, we don't need reduce by year, just track min/max)
def reducer(mapped_data):
    max_temp = float('-inf')
    min_temp = float('inf')
    hottest_year = None
    coolest_year = None

    for year, temp in mapped_data:
        if temp > max_temp:
            max_temp = temp
            hottest_year = year
        if temp < min_temp:
            min_temp = temp
            coolest_year = year

    return hottest_year, max_temp, coolest_year, min_temp

# Main
if __name__ == "__main__":
    file_path = "weather.csv"
    mapped_data = mapper(file_path)
    hottest_year, max_temp, coolest_year, min_temp = reducer(mapped_data)

    print(f"Hottest Year: {hottest_year} with {max_temp}°C")
    print(f"Coolest Year: {coolest_year} with {min_temp}°C")