import socket
import threading
import os

# Pasta onde os arquivos do servidor ficarão armazenados
SERVER_FILES = 'server_files'

# Endereço e porta onde o servidor irá escutar conexões
HOST = '0.0.0.0'  # Escuta em todas as interfaces de rede disponíveis
PORT = 9999

# Função que lida com cada cliente conectado
def handle_client(client_socket):
    try:
        while True:
            # Recebe dados do cliente
            data = client_socket.recv(1024).decode()
            if not data:
                break  # Sai do loop se não houver dados

            # Divide os dados em comando e argumentos
            parts = data.strip().split()
            if not parts:
                continue  # Pula caso a linha esteja vazia
            
            command = parts[0]  # Primeiro elemento é o comando
            args = parts[1:]    # O restante são os argumentos

            # Comando 'ls' - lista arquivos/diretórios
            if command == 'ls':
                path = args[0] if args else '.'  # Usa argumento ou diretório atual
                full_path = os.path.join(SERVER_FILES, path)
                
                if not os.path.exists(full_path):
                    response = "ERROR: Path/file not found\n"
                else:
                    if os.path.isfile(full_path):
                        response = f"FILE: {path} Size: {os.path.getsize(full_path)} bytes\n"
                    else:
                        files = os.listdir(full_path)
                        response = "\n".join(files) + "\n"
                client_socket.send(response.encode())

            # Comando 'rm' - remove arquivos
            elif command == 'rm':
                if not args:
                    response = "ERROR: Missing path\n"
                else:
                    path = args[0]
                    full_path = os.path.join(SERVER_FILES, path)
                    
                    if not os.path.exists(full_path):
                        response = "ERROR: Path/file not found\n"
                    else:
                        if os.path.isfile(full_path):
                            os.remove(full_path)
                            response = "OK: File removed\n"
                        else:
                            # Se for um diretório, remove apenas os arquivos dentro dele
                            count = 0
                            for f in os.listdir(full_path):
                                file_path = os.path.join(full_path, f)
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                                    count += 1
                            response = f"OK: Removed {count} files\n"
                client_socket.send(response.encode())

            # Comando 'cp' - copia arquivos para o destino
            elif command == 'cp':
                if len(args) < 2:
                    response = "ERROR: Missing source/destination\n"
                else:
                    sources = args[:-1]  # Arquivos de origem
                    dest = args[-1]     # Último argumento é o destino
                    dest_path = os.path.join(SERVER_FILES, dest)
                    os.makedirs(dest_path, exist_ok=True)  # Garante que o destino existe
                    
                    error = None
                    for src in sources:
                        src_path = os.path.join(SERVER_FILES, src)
                        if not os.path.exists(src_path):
                            error = f"ERROR: Source {src} not found"
                            break
                        
                        if os.path.isfile(src_path):
                            with open(src_path, 'rb') as f_src:
                                content = f_src.read()
                            dest_file = os.path.join(dest_path, os.path.basename(src_path))
                            with open(dest_file, 'wb') as f_dest:
                                f_dest.write(content)
                        else:
                            error = "ERROR: Can't copy directories"
                            break
                    
                    response = error + "\n" if error else "OK: Files copied\n"
                client_socket.send(response.encode())

            # Comando 'get' - envia arquivos para o cliente
            elif command == 'get':
                if not args:
                    response = "ERROR: Missing path\n"
                    client_socket.send(response.encode())
                    continue
                
                path = args[0]
                full_path = os.path.join(SERVER_FILES, path)
                
                if not os.path.exists(full_path):
                    # Informa erro e termina com marcador 'END'
                    client_socket.send("ERROR: Path/file not found\nEND\n".encode())
                else:
                    if os.path.isfile(full_path):
                        # Se for arquivo, envia cabeçalho e conteúdo
                        with open(full_path, 'rb') as f:
                            content = f.read()
                        header = f"FILE {os.path.basename(full_path)} {len(content)}\n"
                        client_socket.send(header.encode())
                        client_socket.send(content)
                    else:
                        # Se for diretório, envia todos os arquivos dentro
                        for filename in os.listdir(full_path):
                            file_path = os.path.join(full_path, filename)
                            if os.path.isfile(file_path):
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                header = f"FILE {filename} {len(content)}\n"
                                client_socket.send(header.encode())
                                client_socket.send(content)
                    client_socket.send(b"END\n")  # Indica fim da transmissão

            else:
                # Comando inválido
                response = "ERROR: Invalid command\n"
                client_socket.send(response.encode())

    except Exception as e:
        # Em caso de erro, exibe no console
        print(f"Error: {e}")
    finally:
        # Fecha conexão com o cliente
        client_socket.close()

# Função principal que inicia o servidor
def main():
    # Garante que a pasta do servidor exista
    if not os.path.exists(SERVER_FILES):
        os.makedirs(SERVER_FILES)

    # Cria o socket TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))  # Associa o socket ao endereço e porta
    server.listen(5)  # Começa a escutar conexões (máx 5 em espera)
    print(f"Servidor ouvindo em {HOST}:{PORT}")

    # Aceita conexões em loop
    while True:
        client_sock, addr = server.accept()
        print(f"Conexão aceita de {addr}")
        # Cria nova thread para lidar com o cliente
        client_handler = threading.Thread(target=handle_client, args=(client_sock,))
        client_handler.start()

# Executa a função principal quando o script é rodado diretamente
if __name__ == '__main__':
    main()