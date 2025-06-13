import socket
import threading
import ipaddress
import re
from host_scanner import HostScanner

PORT = 35640  # Porta na qual o servidor irá escutar
USE_ARP = True # Flag que pode ser usada para controlar o uso do ARP (atualmente sempre usado se o prefixlen não for /32)

class NetworkScannerServer:
    def __init__(self, port=PORT):
        """
        Inicializa o servidor com a porta especificada.
        """
        self.port = port

    @staticmethod
    def parse_network_input(data):
        """
        Analisa a string de entrada da rede para garantir que está no formato CIDR válido (ex: 192.168.1.0/24).
        Retorna uma lista de objetos IPv4Network ou uma string de erro.
        """
        cidr_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')
        if not cidr_pattern.match(data.strip()):
            return "ERRO: Formato inválido. Use apenas: 192.168.1.0/24 (CIDR).\n"
        try:
            # Tenta criar um objeto IPv4Network a partir da string CIDR
            network = ipaddress.IPv4Network(data.strip(), strict=False)
            return [network]
        except (ipaddress.AddressValueError, ValueError) as e:
            return f"ERRO: {str(e)}\n"

    @staticmethod
    def format_host_info(host_info):
        """
        Formata as informações de um host descoberto em uma string legível para o cliente.
        """
        response = []
        response.append(f"Nome DNS: {host_info['name'] if host_info.get('name') else host_info['ip']}")
        response.append(f"Endereço IP: {host_info['ip']}")
        response.append(f"MAC Address: {host_info.get('mac', '')}")
        response.append(f"Fabricante: {host_info.get('vendor', '')}")
        if host_info.get('snmp_info'):
            # Adiciona informações SNMP se disponíveis
            for desc, value in host_info['snmp_info'].items():
                response.append(f"{desc}: {value}")
        return '\n'.join(response) + '\n\n'

    def enhanced_scan(self, network):
        """
        Realiza uma varredura aprimorada da rede, combinando varredura ARP e ping,
        e enriquecendo os resultados com informações SNMP.
        """
        if network.prefixlen == 32:
            # Se for um único IP (/32), escaneia apenas aquele host
            host_info = HostScanner.scan_host(str(network.network_address))
            if host_info:
                from snmp_helper import SNMPHelper # Importação local para evitar dependência circular
                host_info['snmp_info'] = SNMPHelper.get_all_info(host_info['ip']) # Obtém infos SNMP
                host_info['name'] = HostScanner.get_hostname(host_info['ip']) # Garante nome DNS
                return [host_info]
            return []

        # Realiza varredura ARP
        arp_hosts = HostScanner.arp_scan(network)
        # Realiza varredura ping rápida
        ping_results = HostScanner.fast_ping_scan(network)

        # Combina os resultados, priorizando ARP e removendo duplicatas por IP
        existing_ips = {host['ip'] for host in arp_hosts}
        all_hosts = arp_hosts + [host for host in ping_results if host['ip'] not in existing_ips]

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from snmp_helper import SNMPHelper # Importação local para evitar dependência circular

        def enrich_host(host):
            """Função auxiliar para enriquecer um único host com SNMP e nome DNS."""
            host['snmp_info'] = SNMPHelper.get_all_info(host['ip'])
            host['name'] = HostScanner.get_hostname(host['ip'])
            return host

        # Usa um ThreadPoolExecutor para enriquecer os hosts com informações SNMP em paralelo
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(enrich_host, host) for host in all_hosts]
            enriched_hosts = [f.result() for f in as_completed(futures)]
        return enriched_hosts

    def handle_client(self, conn, addr):
        """
        Manipula a comunicação com um cliente individual em uma thread separada.
        Recebe a requisição, processa a varredura e envia a resposta.
        """
        print(f"Conexão estabelecida com {addr}.")
        try:
            # Recebe os dados da requisição do cliente
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                return # Se não há dados, encerra a conexão
            print(f"Recebido de {addr}: {data}")

            # Analisa a entrada da rede
            networks = self.parse_network_input(data)
            if isinstance(networks, str):
                # Se houver erro na entrada, envia a mensagem de erro de volta ao cliente
                conn.sendall(networks.encode('utf-8'))
                return

            conn.sendall(b"Scan iniciado, aguarde...\n\n") # Confirma o início do scan
            active_hosts = []
            for net in networks:
                # Realiza a varredura aprimorada para cada rede fornecida
                active_hosts.extend(self.enhanced_scan(net))

            if active_hosts:
                # Se hosts ativos forem encontrados, formata e envia a resposta
                response = f"Hosts ativos encontrados ({len(active_hosts)}):\n\n"
                response += ''.join([self.format_host_info(host_info) for host_info in active_hosts])
                conn.sendall(response.encode('utf-8'))
            else:
                # Se nenhum host for encontrado
                conn.sendall(b"Nenhum host ativo encontrado na rede.\n")
        except Exception as e:
            print(f"Erro com {addr}: {e}")
        finally:
            conn.close() # Garante que a conexão seja fechada
            print(f"Conexão encerrada com {addr}.")

    def start(self):
        """
        Inicia o servidor, ligando-o à porta e escutando por conexões de clientes.
        Cada nova conexão é tratada em uma nova thread.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Permite reutilizar o endereço e a porta rapidamente após o fechamento
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', self.port)) # Liga o socket a todas as interfaces disponíveis na porta especificada
            s.listen() # Começa a escutar por conexões de entrada
            print(f"Servidor escutando na porta {self.port}...")
            while True:
                conn, addr = s.accept() # Aceita uma nova conexão de cliente
                # Cria uma nova thread para lidar com o cliente
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.daemon = True # Define a thread como daemon para que ela termine quando o programa principal terminar
                client_thread.start() # Inicia a thread do cliente