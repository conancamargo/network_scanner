import socket
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from scapy.all import ARP, Ether, srp
from getmac import get_mac_address
from mac_vendor_lookup import MACVendorLookup

MAX_WORKERS = 200  # Define o número máximo de threads para o ThreadPoolExecutor
PING_TIMEOUT = 0.2 # Define o tempo limite para o ping em segundos

class HostScanner:
    @staticmethod
    def get_hostname(ip):
        """
        Tenta resolver o nome do host (DNS) para um determinado endereço IP.
        Retorna o nome do host se encontrado, caso contrário, None.
        """
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None

    @staticmethod
    def check_host(ip, ping_cmd):
        """
        Verifica a disponibilidade de um host usando ping ICMP.
        Se o host responder, tenta obter seu endereço MAC, fabricante e nome DNS.
        Retorna um dicionário com as informações do host ou None se não estiver ativo.
        """
        ip_str = str(ip)
        try:
            import subprocess
            # Executa o comando ping e verifica o código de retorno
            if subprocess.run(ping_cmd + [ip_str],
                              stdout=subprocess.DEVNULL, # Redireciona a saída padrão para DEVNULL
                              stderr=subprocess.DEVNULL).returncode == 0: # Redireciona a saída de erro para DEVNULL
                # Se o ping for bem-sucedido, tenta obter o MAC e o fabricante
                mac = get_mac_address(ip=ip_str)
                vendor = MACVendorLookup.get_vendor(mac) if mac else None
                return {
                    'ip': ip_str,
                    'mac': mac,
                    'vendor': vendor,
                    'name': HostScanner.get_hostname(ip_str),
                    'snmp_info': None # snmp_info será preenchido posteriormente
                }
        except Exception as e:
            # Captura exceções e retorna None em caso de erro
            return None
        return None

    @staticmethod
    def arp_scan(network):
        """
        Realiza uma varredura ARP para descobrir hosts ativos na rede local.
        Retorna uma lista de dicionários com informações dos hosts encontrados via ARP.
        """
        hosts = []
        try:
            # Cria uma requisição ARP para todos os hosts na rede
            arp_request = ARP(pdst=str(network))
            # Cria um frame Ethernet de broadcast
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            # Combina o broadcast com a requisição ARP
            arp_request_broadcast = broadcast / arp_request
            # Envia o pacote ARP e captura as respostas
            answered_list = srp(arp_request_broadcast, timeout=0.2, verbose=False)[0]

            for sent, received in answered_list:
                # Extrai o MAC address e tenta obter o fabricante
                mac = received.hwsrc
                vendor = MACVendorLookup.get_vendor(mac) if mac else None
                hosts.append({
                    'ip': received.psrc, # Endereço IP do host respondente
                    'mac': mac,
                    'vendor': vendor,
                    'name': HostScanner.get_hostname(received.psrc),
                    'snmp_info': None
                })
        except Exception as e:
            print(f"ARP scan error: {e}")
        return hosts

    @staticmethod
    def fast_ping_scan(network):
        """
        Realiza uma varredura ping rápida em todos os hosts de uma rede usando ThreadPoolExecutor.
        Retorna uma lista de dicionários com informações dos hosts que responderam ao ping.
        """
        hosts = []
        # Define o comando ping dependendo do sistema operacional
        ping_cmd = ['ping', '-n', '1', '-w', str(int(PING_TIMEOUT * 1000))] if platform.system() == 'Windows' else ['ping', '-c', '1', '-W', str(PING_TIMEOUT), '-i', '0.2']
        # Cria um pool de threads para executar a verificação de hosts em paralelo
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submete a tarefa check_host para cada IP na rede
            futures = {executor.submit(HostScanner.check_host, ip, ping_cmd): ip for ip in network.hosts()}
            # Processa os resultados à medida que as tarefas são concluídas
            for future in as_completed(futures):
                result = future.result()
                if result:
                    hosts.append(result)
        return hosts

    @staticmethod
    def scan_host(ip_str):
        """
        Coleta informações básicas (MAC, fabricante, nome DNS) para um único endereço IP.
        Usado para varreduras de um único host (/32).
        """
        mac = get_mac_address(ip=ip_str)
        vendor = MACVendorLookup.get_vendor(mac) if mac else None
        return {
            'ip': ip_str,
            'mac': mac,
            'vendor': vendor,
            'name': HostScanner.get_hostname(ip_str),
            'snmp_info': None
        }