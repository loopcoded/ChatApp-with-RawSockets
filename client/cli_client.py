# cli_client.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import threading
import socket
import time
from backend.rsa_utils import encrypt_message
from cryptography.hazmat.primitives import serialization

HOST = '127.0.0.1'
PORT = 5000

# Load server's public key
with open("../backend/server_public.pem", "rb") as f:
    server_public_key = serialization.load_pem_public_key(f.read())

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Enter username
username = input("Enter your username: ")
client_socket.sendall(username.encode())

# Shared variables for thread communication
file_transfer_mode = False
file_transfer_lock = threading.Lock()
pending_server_response = None
response_event = threading.Event()

def receive_messages():
    global file_transfer_mode, pending_server_response
    
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
                
            try:
                decoded = data.decode()
                
                # Check if this is a server response to file command
                if decoded.startswith("[Server]:") and ("Ready" in decoded or "rejected" in decoded or "not found" in decoded):
                    with file_transfer_lock:
                        pending_server_response = decoded
                        response_event.set()
                    continue
                
                if decoded.startswith("[File]:"):
                    print("\n" + decoded)
                    # Receive file header (filename|size)
                    header = client_socket.recv(64).decode().strip()
                    file_name, file_size = header.split("|")
                    file_size = int(file_size)
                    
                    print(f"[Client]: Receiving file '{file_name}' ({file_size} bytes)...")
                    
                    # Receive file data
                    file_data = b''
                    while len(file_data) < file_size:
                        remaining = file_size - len(file_data)
                        chunk_size = min(4096, remaining)
                        chunk = client_socket.recv(chunk_size)
                        if not chunk:
                            break
                        file_data += chunk
                        #print(f"[Client]: Downloaded {len(file_data)}/{file_size} bytes")
                   
                    if len(file_data) == file_size:
                        # Save file
                        os.makedirs("downloads", exist_ok=True)
                        with open(f"downloads/{file_name}", "wb") as f:
                            f.write(file_data)
                        print(f"[Client]: File '{file_name}' saved successfully in downloads/")
                    else:
                        print(f"[Client]: File transfer incomplete. Expected {file_size}, got {len(file_data)} bytes")
                else:
                    print("\n" + decoded)
            except UnicodeDecodeError:
                print("\n[Client]: Received binary data (file content)")
            
            # Show prompt again
            print("> ", end="", flush=True)
            
        except Exception as e:
            print(f"[Client] Error receiving message: {e}")
            break

threading.Thread(target=receive_messages, daemon=True).start()

try:
    while True:
        msg = input("> ")

        if msg.startswith("/file"):
            parts = msg.split(" ", 2)
            if len(parts) < 3:
                print("[Client]: Usage: /file <username> <file_path>")
                continue

            _, to_user, file_path = parts
            if not os.path.exists(file_path):
                print("[Client]: File not found.")
                continue

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            print(f"[Client]: Sending file '{file_name}' ({file_size} bytes) to {to_user}...")

            # Send file header message (UNENCRYPTED)
            cmd = f"/file {to_user} {file_name}"
            client_socket.sendall(cmd.encode())
            
            # Wait for server response using thread communication
            response_event.clear()
            if response_event.wait(timeout=5.0):
                with file_transfer_lock:
                    server_response = pending_server_response
                    pending_server_response = None
                
                print(f"[Client]: Server response: {server_response}")
                if "Ready" not in server_response:
                    print("[Client]: Server rejected file.")
                    continue
            else:
                print("[Client]: Timeout waiting for server response")
                continue

            # Send file size (10 bytes, padded)
            size_str = str(file_size).ljust(10)
            print(f"[Client]: Sending file size: {file_size}")
            client_socket.sendall(size_str.encode())

            # Send file data in chunks
            print("[Client]: Sending file content...")
            bytes_sent = 0
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)
                    bytes_sent += len(chunk)
                    #print(f"[Client]: Sent {bytes_sent}/{file_size} bytes")

            print(f"[Client]: File '{file_name}' sent successfully to {to_user}.")

        else:
            # Regular message - encrypt it
            if len(msg.encode()) > 200:
                print("[Client]: Message too long for RSA encryption. Try breaking it up.")
                continue
            try:
                encrypted = encrypt_message(msg, server_public_key)
                client_socket.sendall(encrypted)
            except Exception as e:
                print(f"[Client]: Error encrypting message: {e}")

except KeyboardInterrupt:
    print("\n[Client] Exiting.")
    client_socket.close()