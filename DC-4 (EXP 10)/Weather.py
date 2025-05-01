import sys

# Mapper function
def mapper():
    first_line = True
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        # Skip the header row
        if first_line:
            first_line = False
            continue
            
        columns = line.split(',')
        if len(columns) >= 3:  # Changed from 4 to 3
            try:
                year = columns[0]
                temperature = float(columns[2])  
                print(f"{year}\t{temperature}")
            except ValueError:
                pass

# Reducer function
def reducer():
    current_year = None
    max_temp = float('-inf')  
    min_temp = float('inf')   # This is correct
    global_max_temp = float('-inf')  # This is correct
    global_min_temp = float('inf')   
    global_hottest_year = global_coldest_year = None

    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                year, temp = line.split('\t')
                temperature = float(temp)

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

            except ValueError:
                pass

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


# Main logic to call the correct function based on arguments
if __name__ == "__main__":
    if '--mapper' in sys.argv:
        mapper()
    elif '--reducer' in sys.argv:
        reducer()
    else:
        print("Please use --mapper or --reducer.")
