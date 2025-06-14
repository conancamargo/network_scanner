import socket

HOST = '127.0.0.1'
PORT = 35640
CIDR = '192.168.3.21/24'

def main():
    client_socket = None
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        client_socket.send(CIDR.encode('utf-8'))

        print("Resposta do servidor:")
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            print(chunk.decode('utf-8'), end='')

        print("\nProcessamento da resposta concluído.")
    except Exception as e:
        print(f"Erro durante a conexão: {e}")
    finally:
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    main()