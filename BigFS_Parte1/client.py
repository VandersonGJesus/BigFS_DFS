import socket
import os

# Endereço e porta do servidor
HOST = 'localhost'
PORT = 9999

# Função para receber arquivos enviados pelo servidor
def receive_file(sock, save_path):
    buffer = b''  # Buffer para armazenar dados recebidos

    while True:
        data = sock.recv(4096)  # Recebe dados do socket
        if not data:
            break  # Se não há mais dados, encerra

        buffer += data  # Adiciona ao buffer
        
        while True:
            # Procura o fim do cabeçalho (linha)
            header_end = buffer.find(b'\n')
            if header_end == -1:
                break  # Se não encontrou, espera mais dados
            
            # Extrai e decodifica o cabeçalho
            header = buffer[:header_end].decode().strip()
            buffer = buffer[header_end+1:]  # Remove o cabeçalho do buffer
            
            if header.startswith("ERROR"):
                # Caso ocorra erro enviado pelo servidor
                print(header)
                return
            elif header.startswith("FILE"):
                # Cabeçalho indicando arquivo
                parts = header.split()
                filename = parts[1]
                size = int(parts[2])  # Tamanho do arquivo

                # Garante que o buffer tenha o conteúdo completo do arquivo
                while len(buffer) < size:
                    data = sock.recv(4096)
                    if not data:
                        break
                    buffer += data
                
                file_data = buffer[:size]  # Extrai conteúdo
                buffer = buffer[size:]  # Remove o conteúdo do buffer

                # Salva o arquivo no diretório especificado
                os.makedirs(save_path, exist_ok=True)
                with open(os.path.join(save_path, filename), 'wb') as f:
                    f.write(file_data)
                print(f"Arquivo recebido: {filename}")
            elif header == "END":
                # Fim da transferência
                print("Transferência concluída")
                return

# Função principal do cliente
def main():
    # Cria socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))  # Conecta ao servidor
    print(f"Conectado ao servidor {HOST}:{PORT}")

    # Loop de interação com o usuário
    while True:
        cmd = input("Comando (ls/rm/cp/get/exit): ").strip()  # Lê comando do usuário
        if cmd == 'exit':
            break  # Encerra o loop se comando for 'exit'
        
        client.send(cmd.encode())  # Envia o comando ao servidor
        
        if cmd.startswith('get'):
            # Para o comando 'get', solicita diretório de destino
            save_dir = input("Diretório para salvar: ").strip()
            receive_file(client, save_dir)
        else:
            # Para outros comandos, recebe e imprime a resposta
            response = client.recv(1024).decode()
            print(response)

    client.close()  # Fecha conexão com o servidor

# Ponto de entrada do script
if __name__ == '__main__':
    main()
