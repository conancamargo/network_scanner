from network_scanner_server import NetworkScannerServer

if __name__ == "__main__":
    # Este é o ponto de entrada principal do script.
    # Ele só será executado quando o script for chamado diretamente.
    server = NetworkScannerServer() # Cria uma instância do servidor de scanner de rede
    server.start() # Inicia o servidor para escutar por conexões de clientes