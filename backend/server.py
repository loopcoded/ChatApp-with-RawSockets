# backend/server.py
import socket
import threading
from rsa_utils import generate_keys, decrypt_message
from cryptography.hazmat.primitives import serialization

HOST = '127.0.0.1'
PORT = 5000

server_private_key, server_public_key = generate_keys()

with open("server_public.pem", "wb") as f:
    f.write(server_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

clients = {}  # username -> connection
lock = threading.Lock()

def handle_client(conn, addr):
    username = None
    try:
        # First message must be username
        username = conn.recv(1024).decode().strip()
        # Step 2: Check for duplicate login
        with lock:
            if username in clients:
                conn.sendall("[Server]: Duplicate login detected. Connection rejected.".encode())
                conn.close()
                print(f"[!] Rejected duplicate login for '{username}' from {addr}")
                return
            clients[username] = conn
            print(f"[+] {username} ({addr}) joined the chat.")
            
            # Send list of currently online users (excluding the new user)
            other_users = [user for user in clients.keys() if user != username]
            if other_users:
                user_list = ", ".join(other_users)
                conn.sendall(f"[Server]: Currently online: {user_list}".encode())
            else:
                conn.sendall("[Server]: You're the first user online.".encode())

        # Welcome broadcast to all other users
        broadcast(f"[Server]: {username} joined the chat.", sender=username)
        while True:
            data = conn.recv(4096)
            if not data:
                break
            
            # Try to decrypt first, if it fails, treat as unencrypted command
            try:
                message = decrypt_message(data, server_private_key)
                print(f"[DEBUG] Decrypted message from {username}: {message}")
            except Exception as e:
                # If decryption fails, treat as unencrypted command (like /file)
                message = data.decode(errors="ignore")
                print(f"[DEBUG] Unencrypted message from {username}: {message}")

            # Handle file transfer command
            if message.startswith("/file"):
                # Format: /file <username> <filename>
                parts = message.split(" ", 2)
                if len(parts) < 3:
                    conn.sendall("[Server]: Usage: /file <username> <filename>".encode())
                    continue
            
                target_user, file_name = parts[1], parts[2]
                if target_user not in clients:
                    conn.sendall(f"[Server]: User '{target_user}' not found.".encode())
                    continue
            
                # Notify sender to send file size and bytes
                ready_msg = "[Server]: Ready to receive file size."
                conn.sendall(ready_msg.encode())
                print(f"[DEBUG] Sent ready message to {username}: {ready_msg}")

                # Receive file size (fixed-length, 10-byte string)
                size_data = conn.recv(10)
                if not size_data:
                    conn.sendall("[Server]: Failed to receive file size.".encode())
                    continue
                    
                try:
                    file_size = int(size_data.decode().strip())
                    print(f"[DEBUG] Receiving file '{file_name}' of size {file_size} bytes")
                except ValueError:
                    conn.sendall("[Server]: Invalid file size received.".encode())
                    continue
            
                # Receive actual file content
                file_data = b''
                while len(file_data) < file_size:
                    remaining = file_size - len(file_data)
                    chunk_size = min(4096, remaining)
                    chunk = conn.recv(chunk_size)
                    if not chunk:
                        break
                    file_data += chunk
                    #print(f"[DEBUG] Received {len(file_data)}/{file_size} bytes")
                
                if len(file_data) != file_size:
                    conn.sendall(f"[Server]: File transfer incomplete. Expected {file_size}, got {len(file_data)} bytes.".encode())
                    continue
                
                # Send to target user
                try:
                    receiver = clients[target_user]
                    receiver.sendall(f"[File]: {username} sent you a file: {file_name}".encode())
                    # Send header with filename and size
                    header = f"{file_name}|{file_size}".ljust(64)
                    receiver.sendall(header.encode())
                    receiver.sendall(file_data)
                    conn.sendall(f"[Server]: File '{file_name}' sent successfully to {target_user}.".encode())
                    print(f"[DEBUG] File '{file_name}' forwarded to {target_user}")
                except Exception as e:
                    conn.sendall(f"[Server]: Failed to send file to {target_user}: {str(e)}".encode())
                    print(f"[ERROR] Failed to forward file to {target_user}: {e}")
            
            elif message.startswith("/msg"):
                # Format: /msg <username> <message>
                parts = message.split(" ", 2)
                if len(parts) >= 3:
                    target, msg_body = parts[1], parts[2]
                    send_private_message(username, target, msg_body)
                else:
                    conn.sendall("[Server]: Invalid private message format.".encode())
            else:
                # Regular message - broadcast to all
                broadcast(f"[{username}]: {message}", sender=username)

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")
    finally:
        with lock:
            if username and username in clients:
                del clients[username]
        conn.close()
        if username:
            broadcast(f"[Server]: {username} left the chat.", sender=None)
            print(f"[-] {username} disconnected.")

def broadcast(message, sender=None):
    with lock:
        for user, client_conn in clients.items():
            if user != sender:
                try:
                    client_conn.sendall(message.encode())
                except:
                    pass

def send_private_message(from_user, to_user, message):
    with lock:
        if to_user in clients:
            try:
                clients[to_user].sendall(f"[Private] {from_user}: {message}".encode())
            except:
                pass
        else:
            if from_user in clients:
                clients[from_user].sendall(f"[Server]: User '{to_user}' not found.".encode())

# Start server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"[Server] Listening on {HOST}:{PORT}")

while True:
    conn, addr = server_socket.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
    print(f"[Server] Active connections: {threading.active_count() - 1}")