from scapy.all import ARP, Ether, srp

# comando para executar o ping
# sudo /home/aurora/Code/Python/network_scanner/venv/bin/python tests/test_network_scanner_server.py


# Define o alvo da busca (sub-rede, por exemplo, 192.168.1.0/24)
# Substitua pela sua própria sub-rede
target_ip = "192.168.1.0/24"

print(f"Buscando dispositivos na rede {target_ip}...")

# Cria um pacote Ether com broadcast e um pacote ARP com "quem tem"
# pdst = Protocol Destination (destino do protocolo)
arp_request = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target_ip)

# Envia o pacote ARP e espera pelas respostas
# timeout: tempo em segundos para esperar por respostas
# verbose=False: para não imprimir informações detalhadas de cada pacote
ans, unans = srp(arp_request, timeout=2, verbose=False)

print("\nDispositivos encontrados:")
# Itera sobre as respostas
for sent, received in ans:
    print(f"IP: {received.psrc}\tMAC: {received.hwsrc}")

# Se houver pacotes não respondidos, você pode inspecioná-los em 'unans'
if unans:
    print("\nPacotes não respondidos:")
    for packet in unans:
        print(packet.summary())