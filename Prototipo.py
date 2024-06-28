import psutil
import cpuinfo
import GPUtil
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetPowerUsage, nvmlShutdown
import time
import json

# Estima o consumo de energia da CPU
def estimate_cpu_power_usage(cpu_usage_percent, tdp_watts=65):
    return round((cpu_usage_percent / 100) * tdp_watts)

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
    base_power_usage = 2 if disk_type == 'SSD' else 6  # SSDs consomem cerca de 2W, HDs cerca de 6W
    # Ajusta o consumo de energia com base na porcentagem de uso, assumindo que o uso máximo dobra o consumo de energia
    estimated_power_usage = base_power_usage * (1 + (disk_usage_percent / 100))
    return round(estimated_power_usage, 2)

# Pega as informações do SSD/HD
def get_disk_info():
    disk_usage = psutil.disk_usage('/')
    disk_io_counters = psutil.disk_io_counters()
    # A porcentagem de uso do disco não é diretamente disponível, então podemos estimar com base nos contadores de I/O
    # Esta é uma simplificação; para uma estimativa mais precisa, considere calcular a diferença nos contadores de I/O ao longo do tempo
    disk_usage_percent = (disk_io_counters.read_bytes + disk_io_counters.write_bytes) / (disk_usage.total * 0.01)
    # Assumindo SSD como padrão; você pode ajustar a lógica para determinar se é SSD ou HD com base em informações específicas do sistema
    disk_type = 'SSD'
    return {
        'type': disk_type,
        'usage_percent': min(disk_usage_percent, 100),  # Limita a 100%
        'estimated_power_usage': estimate_disk_power_usage(disk_usage_percent, disk_type)
    }

# Pega as informações da GPU
def get_gpu_info():
    nvmlInit()
    handle = nvmlDeviceGetHandleByIndex(0)
    gpu_power_usage = round(nvmlDeviceGetPowerUsage(handle) / 1000)  # mW to W
    nvmlShutdown()
    gpus = GPUtil.getGPUs()
    gpu_info = gpus[0]
    return {
        'name': gpu_info.name,
        'load': round(gpu_info.load * 100),
        'memory_free': gpu_info.memoryFree,
        'memory_used': gpu_info.memoryUsed,
        'temperature': gpu_info.temperature,
        'power_usage': gpu_power_usage
    }

# Faz a estimativa de consumo de energia da Ram
def estimate_ram_power_usage(ram_info, power_per_gb=0.3):
    used_gb = ram_info['used'] / (1024 ** 3)  # Convert bytes to GB
    estimated_power_usage = used_gb * power_per_gb
    return round(estimated_power_usage)

# Função para medir a eficiência energética
def measure_efficiency():
    cpu_info = get_cpu_info()
    ram_info = get_ram_info()
    gpu_info = get_gpu_info()
    disk_info = get_disk_info()  # Obter informações do disco

    power_consumed = (
        cpu_info['estimated_power_usage'] +
        estimate_ram_power_usage(ram_info) +
        gpu_info['power_usage'] +
        disk_info['estimated_power_usage']  # Adicionar o consumo de energia do disco
    )

    efficiency_data = {
        'cpu_info': cpu_info,
        'ram_info': ram_info,
        'gpu_info': gpu_info,
        'disk_info': disk_info,  # Incluir informações do disco
        'total_power_consumed': power_consumed
    }
    return efficiency_data

# Função para calcular o PUE
def calculate_pue(total_power_consumed, it_power_consumed):
    return total_power_consumed / it_power_consumed

# Função para calcular as emissões de carbono
def calculate_carbon_emissions(power_consumed_kwh, emission_factor=0.233):
    """
    Calcula as emissões de carbono com base no consumo de energia.
    
    :param power_consumed_kwh: Consumo de energia em kWh
    :param emission_factor: Fator de emissão em kg CO2e por kWh (valor médio de referência)
    :return: Emissões de carbono em kg CO2e
    """
    return power_consumed_kwh * emission_factor

# Função para salvar dados em JSON
def save_to_json(data, filename='power_usage_data.json'):
    with open(filename, 'a') as f:
        json.dump(data, f, indent=4)
        f.write("\n")

if __name__ == "__main__":
    total_power_consumed_data_center = 500  # em Watts, valor aproximado
    emission_factor = 0.233  # kg CO2e por kWh, valor médio de referência

    while True:
        efficiency_data = measure_efficiency()
        it_power_consumed_watts = efficiency_data['total_power_consumed']
        it_power_consumed_kwh = it_power_consumed_watts / 1000  # Convertendo Watts para kWh
        pue = calculate_pue(total_power_consumed_data_center, it_power_consumed_watts)

        # Calcula as emissões de carbono
        carbon_emissions = calculate_carbon_emissions(it_power_consumed_kwh, emission_factor)

        # Preparando os dados para JSON
        data = {
            'Efficiency Data': efficiency_data,
            'PUE': pue,
            'Carbon Emissions': carbon_emissions
        }

        # Printando os dados para verificação
        
        print(f"Efficiency Data:\n"
      f"CPU: {efficiency_data['cpu_info']['Modelo']} | "
      f"Frequency: {efficiency_data['cpu_info']['hz']} | "
      f"Cores/Threads: {efficiency_data['cpu_info']['cores']}/{efficiency_data['cpu_info']['threads']} | "
      f"Usage: {efficiency_data['cpu_info']['usage_percent']}% | "
      f"Power: {efficiency_data['cpu_info']['estimated_power_usage']}W\n"
      f"RAM: Total: {efficiency_data['ram_info']['total'] / (1024 ** 3):.2f}GB | "
      f"Used: {efficiency_data['ram_info']['used'] / (1024 ** 3):.2f}GB | "
      f"Available: {efficiency_data['ram_info']['available'] / (1024 ** 3):.2f}GB | "
      f"Usage: {efficiency_data['ram_info']['percent']}%\n"
      f"GPU: {efficiency_data['gpu_info']['name']} | "
      f"Load: {efficiency_data['gpu_info']['load']}% | "
      f"Memory Used: {efficiency_data['gpu_info']['memory_used']}MB | "
      f"Temperature: {efficiency_data['gpu_info']['temperature']}°C | "
      f"Power: {efficiency_data['gpu_info']['power_usage']}W\n"
      f"Disk: Type: {efficiency_data['disk_info']['type']} | "
      f"Usage: {efficiency_data['disk_info']['usage_percent']:.2f}% | "
      f"Power: {efficiency_data['disk_info']['estimated_power_usage']}W\n"
      f"Total Power Consumed: {efficiency_data['total_power_consumed']}W\n"
      f"PUE: {pue}\n"
      f"Carbon Emissions: {carbon_emissions} kg CO2e")

        # Salvando dados no arquivo JSON
        try:
            save_to_json(data)
            print("Data successfully saved to power_usage_data.json")
        except Exception as e:
            print(f"Error saving data to JSON file: {e}")

        time.sleep(60)
