import socket  # Esta linha estava faltando - ESSENCIAL para usar sockets

HOST = '127.0.0.1'  # Endereço do servidor
PORT = 35640        # Porta do servidor
CIDR = '192.168.1.4/24'  # Rede no formato padrão com barra

def main():
    try:
        # Cria o socket TCP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Conecta ao servidor
        client_socket.connect((HOST, PORT))
        
        # Envia a requisição no formato CIDR padrão
        client_socket.send(CIDR.encode('utf-8'))
        
        # Recebe a resposta do servidor
        print("Resposta do servidor:")
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            print(chunk.decode('utf-8'), end='')
        
        print("Conexão encerrada") #trocar para outra coisa pq pode ser que tenha dado erro na identificação do cidr
    except Exception as e:
        print(f"Erro durante a conexão: {e}")
    finally:
        client_socket.close()
        

if __name__ == "__main__":
    main()