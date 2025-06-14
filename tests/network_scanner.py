import socket
import threading
import ipaddress
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
from scapy.all import ARP, Ether, srp
from getmac import get_mac_address

PORT = 35640
MAX_WORKERS = 100  # Aumentamos o número de threads para maior paralelismo
PING_TIMEOUT = 0.5  # Timeout reduzido para 500ms
USE_ARP = True     # Usar ARP para redes locais (muito mais rápido)

def handle_client(conn, addr):
    print(f"Conexão estabelecida com {addr}")

    try:
        while True:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                break

            print(f"Recebido de {addr}: {data}")

            # Validar o formato CIDR
            cidr_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')
            if not cidr_pattern.match(data):
                conn.sendall(b"ERRO: Formato invalido. Use notacao CIDR como 192.168.105.0/24\n")
                continue

            # Extrair IP e prefixo
            ip_part, prefix_part = data.split('/')
            prefix = int(prefix_part)
            network = f"{ip_part}/{prefix}"

            try:
                # Verificar se é uma rede válida
                net = ipaddress.IPv4Network(network, strict=False)
                response = f"Scan iniciado para a rede: {net}\n".encode('utf-8')
                conn.sendall(response)

                # Realizar scan otimizado
                active_hosts = enhanced_scan(net)

                if active_hosts:
                    conn.sendall(f"Hosts ativos encontrados ({len(active_hosts)}):\n".encode('utf-8'))
                    # Envia informações completas como no Advanced IP Scanner
                    for host_info in active_hosts:
                        response_line = f"{host_info['name'] if host_info['name'] else host_info['ip']}\t"
                        response_line += f"{host_info['ip']}\t"
                        response_line += f"{host_info['mac']}\t" if host_info['mac'] else "\t"
                        response_line += f"{host_info['vendor']}\n" if host_info['vendor'] else "\n"
                        conn.sendall(response_line.encode('utf-8'))
                else:
                    conn.sendall(b"Nenhum host ativo encontrado na rede.\n")

            except ValueError as e:
                conn.sendall(f"ERRO: {str(e)}\n".encode('utf-8'))

    except Exception as e:
        print(f"Erro com {addr}: {e}")
    finally:
        conn.close()
        print(f"Conexão encerrada com {addr}")

def enhanced_scan(network):
    """Scan avançado com ARP e detecção de informações adicionais"""
    active_hosts = []
    
    # Primeiro tentamos com ARP que é muito mais rápido
    if USE_ARP:
        arp_results = arp_scan(network)
        active_hosts.extend(arp_results)
    
    # Complementa com ping para hosts não detectados pelo ARP
    ping_results = fast_ping_scan(network)
    
    # Combina resultados sem duplicatas
    existing_ips = {host['ip'] for host in active_hosts}
    for host in ping_results:
        if host['ip'] not in existing_ips:
            active_hosts.append(host)
    
    return active_hosts

def arp_scan(network):
    """Scan usando ARP para redes locais (extremamente rápido)"""
    hosts = []
    try:
        # Envia pacotes ARP para todos os IPs na rede
        arp_request = ARP(pdst=str(network))
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

        for sent, received in answered_list:
            mac = received.hwsrc
            ip = received.psrc
            vendor = "Unknown"  # Vendor lookup pode ser implementado se necessário
            hosts.append({
                'ip': ip,
                'mac': mac,
                'vendor': vendor,
                'name': get_hostname(ip)
            })
    except Exception as e:
        print(f"ARP scan error: {e}")
    return hosts

def fast_ping_scan(network):
    """Scan otimizado com ping paralelo"""
    hosts = []
    
    # Comando ping específico por sistema operacional
    ping_cmd = ['ping', '-n', '1', '-w', str(PING_TIMEOUT * 1000)] if platform.system() == 'Windows' else ['ping', '-c', '1', '-W', str(PING_TIMEOUT), '-i', '0.2']
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_host, ip, ping_cmd): ip for ip in network.hosts()}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                hosts.append(result)
    
    return hosts

def check_host(ip, ping_cmd):
    """Verifica um host individual e coleta informações"""
    ip_str = str(ip)
    try:
        # Executa ping
        if subprocess.run(ping_cmd + [ip_str], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL).returncode == 0:
            
            # Obtém o endereço MAC usando getmac
            mac = get_mac_address(ip=ip_str)
            
            return {
                'ip': ip_str,
                'mac': mac,
                'vendor': "Unknown",  # Vendor lookup pode ser implementado se necessário
                'name': get_hostname(ip_str)
            }
    except:
        return None
    return None

def get_hostname(ip):
    """Tenta resolver o nome do host"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return None

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', PORT))
        s.listen()
        print(f"Servidor escutando na porta {PORT}...")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()

if __name__ == "__main__":
    start_server()