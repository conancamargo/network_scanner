import socket

HOST = '127.0.0.1'  # Endereço do servidor
PORT = 35640        # Porta do servidor
CIDR = '192.168.102.0/24'  # Rede a ser escaneada

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Envia a requisição ao servidor
client_socket.send(CIDR.encode('utf-8'))

# Recebe e imprime a resposta do servidor em tempo real
print("Resposta do servidor:")
while True:
    chunk = client_socket.recv(1024)  # Recebe um pedaço da resposta
    if not chunk:
        break
    print(chunk.decode('utf-8'), end='')  # Imprime o que foi recebido sem adicionar nova linha extra

# INSERIR PRINT COM "SCAN CONCLUIDO" E FINALIZAR O PROGRAMA

client_socket.close()