import psutil
import cpuinfo
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetPowerUsage, nvmlShutdown
import time
import datetime
from datetime import datetime
import csv  # Importar o módulo csv

# Estima o consumo de energia da CPU
def estimate_cpu_power_usage(cpu_usage_percent, tdp_watts=65):
    return (cpu_usage_percent / 100) * tdp_watts

# Pega as informações da CPU
def get_cpu_info():
    cpu_info = cpuinfo.get_cpu_info()
    cpu_usage_percent = psutil.cpu_percent(interval=1)
    return {
        'Modelo': cpu_info['brand_raw'],
        'hz': cpu_info['hz_actual_friendly'],
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True),
        'usage_percent': cpu_usage_percent,
        'estimated_power_usage': estimate_cpu_power_usage(cpu_usage_percent)
    }

# Pega as informações da Ram
def get_ram_info():
    ram_info = psutil.virtual_memory()
    return {
        'total': ram_info.total,
        'available': ram_info.available,
        'used': ram_info.used,
        'percent': ram_info.percent,
    }

def estimate_disk_power_usage(disk_usage_percent, disk_type='SSD'):
    base_power_usage = 2 if disk_type == 'SSD' else 6
    estimated_power_usage = base_power_usage * (1 + (disk_usage_percent / 100))
    return round(estimated_power_usage, 2)

# Pega as informações do SSD/HD
def get_disk_info():
    disk_usage = psutil.disk_usage('/')
    disk_io_counters = psutil.disk_io_counters()
    disk_usage_percent = (disk_io_counters.read_bytes + disk_io_counters.write_bytes) / (disk_usage.total * 0.01)
    disk_type = 'SSD'
    return {
        'type': disk_type,
        'usage_percent': min(disk_usage_percent, 100),
        'estimated_power_usage': estimate_disk_power_usage(disk_usage_percent, disk_type)
    }

# Faz a estimativa de consumo de energia da Ram
def estimate_ram_power_usage(ram_info, power_per_gb=0.3):
    used_gb = ram_info['used'] / (1024 ** 3)
    estimated_power_usage = used_gb * power_per_gb
    return round(estimated_power_usage)

# Função para medir a eficiência energética
def measure_efficiency():
    cpu_info = get_cpu_info()
    ram_info = get_ram_info()
    disk_info = get_disk_info()

    power_consumed = (
        cpu_info['estimated_power_usage'] +
        estimate_ram_power_usage(ram_info) +
        disk_info['estimated_power_usage']
    )

    efficiency_data = {
        'cpu_info': cpu_info,
        'ram_info': ram_info,
        'disk_info': disk_info,
        'total_power_consumed': power_consumed
    }
    return efficiency_data

# Função para calcular o PUE
def calculate_pue(total_power_consumed, average_watts_per_second):
    return total_power_consumed / average_watts_per_second


# Função para calcular as emissões de carbono
def calculate_carbon_emissions(power_consumed_kwh, emission_factor=0.233):
    return power_consumed_kwh * emission_factor

# Substituir a função save_to_json por save_to_csv
def save_to_csv(data, filename='power_usage_data2.csv'):
    try:
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Check if the file is empty to write headers
            file.seek(0, 2)  # Move to the end of the file
            if file.tell() == 0:  # If file is empty, write headers
                writer.writerow(['Saved At', 'CPU Model', 'CPU Frequency', 'Cores/Threads', 'CPU Usage', 'CPU Power', 'RAM Total GB', 'RAM Used GB', 'RAM Available GB', 'RAM Usage', 'Disk Type', 'Disk Usage', 'Disk Power', 'Total Power Consumed W', 'PUE', 'Carbon Emissions kg CO2e'])
            # Write data row
            writer.writerow([data['saved_at'], data['Efficiency Data']['cpu_info']['Modelo'], data['Efficiency Data']['cpu_info']['hz'], f"{data['Efficiency Data']['cpu_info']['cores']}/{data['Efficiency Data']['cpu_info']['threads']}", data['Efficiency Data']['cpu_info']['usage_percent'], data['Efficiency Data']['cpu_info']['estimated_power_usage'], data['Efficiency Data']['ram_info']['total'] / (1024 ** 3), data['Efficiency Data']['ram_info']['used'] / (1024 ** 3), data['Efficiency Data']['ram_info']['available'] / (1024 ** 3), data['Efficiency Data']['ram_info']['percent'], data['Efficiency Data']['disk_info']['type'], data['Efficiency Data']['disk_info']['usage_percent'], data['Efficiency Data']['disk_info']['estimated_power_usage'], data['Efficiency Data']['total_power_consumed'], data['PUE'], data['Carbon Emissions']])
    except Exception as e:
        print(f"Error saving data to CSV file: {e}")
        time.sleep(60)

# Added function
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

if __name__ == "__main__":
    total_power_consumed_data_center = 500
    emission_factor = 0.233

    while True:
        efficiency_data = measure_efficiency()
        it_power_consumed_watts = efficiency_data['total_power_consumed']
        it_power_consumed_kwh = it_power_consumed_watts / 1000
        pue = calculate_pue(total_power_consumed_data_center, it_power_consumed_watts)

        carbon_emissions = calculate_carbon_emissions(it_power_consumed_kwh, emission_factor)

        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        data = {
            'Efficiency Data': efficiency_data,
            'PUE': pue,
            'Carbon Emissions': carbon_emissions,
            'saved_at': formatted_now
        }

        import pandas as pd  # Importar o módulo pandas

# Substituir a função save_to_csv por save_to_excel
def save_to_excel(data, filename='power_usage_data2.xlsx'):
    try:
        # Verifica se o arquivo já existe para não sobrescrever os dados existentes
        try:
            existing_df = pd.read_excel(filename)
        except FileNotFoundError:
            existing_df = pd.DataFrame()

        # Cria um DataFrame com os dados a serem adicionados
        new_data = pd.DataFrame([{
            'Saved At': data['saved_at'],
            'CPU Model': data['Efficiency Data']['cpu_info']['Modelo'],
            'CPU Frequency': data['Efficiency Data']['cpu_info']['hz'],
            'Cores/Threads': f"{data['Efficiency Data']['cpu_info']['cores']}/{data['Efficiency Data']['cpu_info']['threads']}",
            'CPU Usage': data['Efficiency Data']['cpu_info']['usage_percent'],
            'CPU Power': data['Efficiency Data']['cpu_info']['estimated_power_usage'],
            'RAM Total GB': data['Efficiency Data']['ram_info']['total'] / (1024 ** 3),
            'RAM Used GB': data['Efficiency Data']['ram_info']['used'] / (1024 ** 3),
            'RAM Available GB': data['Efficiency Data']['ram_info']['available'] / (1024 ** 3),
            'RAM Usage': data['Efficiency Data']['ram_info']['percent'],
            'Disk Type': data['Efficiency Data']['disk_info']['type'],
            'Disk Usage': data['Efficiency Data']['disk_info']['usage_percent'],
            'Disk Power': data['Efficiency Data']['disk_info']['estimated_power_usage'],
            'Total Power Consumed W': data['Efficiency Data']['total_power_consumed'],
            'PUE': data['PUE'],
            'Carbon Emissions kg CO2e': data['Carbon Emissions']
        }])

        # Concatena os novos dados com os dados existentes, se houver
        df_to_save = pd.concat([existing_df, new_data], ignore_index=True)

        # Salva o DataFrame como um arquivo Excel
        df_to_save.to_excel(filename, index=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to Excel file: {e}")