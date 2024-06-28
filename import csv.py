import csv
from datetime import datetime

def calculate_average_charging_rate(file_path):
    with open(file_path, newline='') as csvfile:
        data_reader = csv.reader(csvfile)
        next(data_reader)  # Skip header if present
        
        previous_time = None
        previous_energy = None
        total_watts_per_second = 0
        count = 0
        
        for row in data_reader:
            current_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            current_energy = float(row[-1])  # Assuming the last column is energy in kWh
            
            if previous_time is not None:
                time_diff = (current_time - previous_time).total_seconds()
                energy_diff = current_energy - previous_energy  # kWh
                watts_per_second = (energy_diff * 3600000) / time_diff  # Convert kWh to Watts and divide by seconds
                
                total_watts_per_second += watts_per_second
                count += 1
            
            previous_time = current_time
            previous_energy = current_energy
        
        if count > 0:
            average_watts_per_second = total_watts_per_second / count
            return round(average_watts_per_second)
        else:
            return None

# Replace 'power_usage_data.csv' with the path to your actual CSV file
average_rate = calculate_average_charging_rate('power_usage_data.csv')
if average_rate is not None:
    print(f"Average charging rate: {average_rate} Watts per second")
else:
    print("Insufficient data for calculation.")