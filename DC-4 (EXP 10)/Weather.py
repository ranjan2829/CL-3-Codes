import sys

# Mapper function
def mapper(data):
    first_line = True
    mapped_data = []
    for line in data:
        line = line.strip()
        if not line:
            continue

        
        if first_line:
            first_line = False
            continue

        columns = line.split(',')
        if len(columns) >= 3:  
            try:
                year = columns[0]
                temperature = float(columns[2])  
                mapped_data.append((year, temperature))
            except ValueError:
                pass

    return mapped_data


# Reducer function
def reducer(mapped_data):
    current_year = None
    max_temp = float('-inf')  
    min_temp = float('inf')   
    global_max_temp = float('-inf')  
    global_min_temp = float('inf')   
    global_hottest_year = global_coldest_year = None

    for year, temperature in mapped_data:
        # If we're still processing the same year
        if year == current_year:
            max_temp = max(max_temp, temperature)
            min_temp = min(min_temp, temperature)
        else:
            if current_year:
                print(f"{current_year}\tMax: {max_temp}\tMin: {min_temp}")
                if max_temp > global_max_temp:
                    global_max_temp = max_temp
                    global_hottest_year = current_year
                if min_temp < global_min_temp:
                    global_min_temp = min_temp
                    global_coldest_year = current_year
            current_year = year
            max_temp = temperature  # Reset for new year
            min_temp = temperature  # Reset for new year

    # Output the last year's data
    if current_year:
        print(f"{current_year}\tMax: {max_temp}\tMin: {min_temp}")
        if max_temp > global_max_temp:
            global_max_temp = max_temp
            global_hottest_year = current_year
        if min_temp < global_min_temp:
            global_min_temp = min_temp
            global_coldest_year = current_year

    print(f"\nHottest Year: {global_hottest_year} with Max Temp: {global_max_temp}")
    print(f"Coldest Year: {global_coldest_year} with Min Temp: {global_min_temp}")

def main():
    
    with open('data.csv', 'r') as f:
        data = f.readlines()

    
    mapped_data = mapper(data)

    
    mapped_data.sort(key=lambda x: x[0])

    
    reducer(mapped_data)


if __name__ == "__main__":
    main()
