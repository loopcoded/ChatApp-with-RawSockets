# gui_client.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import socket
import time
from datetime import datetime
from backend.rsa_utils import encrypt_message
from cryptography.hazmat.primitives import serialization

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Chat Client")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        # Chat client variables
        self.client_socket = None
        self.username = None
        self.server_public_key = None
        self.connected = False
        self.users_online = set()
        
        # Thread communication
        self.file_transfer_lock = threading.Lock()
        self.pending_server_response = None
        self.response_event = threading.Event()
        
        self.setup_gui()
        self.connect_to_server()
        
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for connection info
        top_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = tk.Label(top_frame, text="Disconnected", 
                                   fg='#e74c3c', bg='#34495e', 
                                   font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=5)
        
        # Middle frame - main chat area
        middle_frame = tk.Frame(main_frame, bg='#2c3e50')
        middle_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Users list
        left_panel = tk.Frame(middle_frame, bg='#34495e', width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Users list header
        users_header = tk.Label(left_panel, text="Online Users", 
                              fg='#ecf0f1', bg='#34495e', 
                              font=('Arial', 12, 'bold'))
        users_header.pack(pady=10)
        
        # Users listbox
        self.users_listbox = tk.Listbox(left_panel, 
                                      bg='#2c3e50', fg='#ecf0f1',
                                      font=('Arial', 10),
                                      selectbackground='#3498db',
                                      relief=tk.FLAT)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Private message button
        private_btn = tk.Button(left_panel, text="Private Message", 
                              bg='#3498db', fg='white', font=('Arial', 9),
                              relief=tk.FLAT, cursor='hand2',
                              command=self.send_private_message)
        private_btn.pack(pady=(0, 5), padx=10, fill=tk.X)
        
        # Send file button
        file_btn = tk.Button(left_panel, text="Send File", 
                           bg='#e67e22', fg='white', font=('Arial', 9),
                           relief=tk.FLAT, cursor='hand2',
                           command=self.send_file)
        file_btn.pack(pady=(0, 10), padx=10, fill=tk.X)
        
        # Right panel - Chat area
        right_panel = tk.Frame(middle_frame, bg='#2c3e50')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(right_panel,
                                                    bg='#34495e', fg='#ecf0f1',
                                                    font=('Arial', 10),
                                                    relief=tk.FLAT,
                                                    wrap=tk.WORD,
                                                    state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Message input frame
        input_frame = tk.Frame(right_panel, bg='#2c3e50')
        input_frame.pack(fill=tk.X)
        
        # Message entry
        self.message_entry = tk.Entry(input_frame, 
                                    bg='#34495e', fg='#ecf0f1',
                                    font=('Arial', 11),
                                    relief=tk.FLAT)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        
        # Send button
        send_btn = tk.Button(input_frame, text="Send", 
                           bg='#27ae60', fg='white', font=('Arial', 10),
                           relief=tk.FLAT, cursor='hand2',
                           command=self.send_message)
        send_btn.pack(side=tk.RIGHT)
        
        # Configure text tags for different message types
        self.chat_display.tag_configure("system", foreground="#95a5a6", font=('Arial', 9, 'italic'))
        self.chat_display.tag_configure("private", foreground="#e74c3c", font=('Arial', 10, 'bold'))
        self.chat_display.tag_configure("file", foreground="#f39c12", font=('Arial', 10, 'bold'))
        self.chat_display.tag_configure("user", foreground="#3498db", font=('Arial', 10, 'bold'))
        self.chat_display.tag_configure("timestamp", foreground="#7f8c8d", font=('Arial', 8))
        
    def connect_to_server(self):
        try:
            # Get username
            self.username = simpledialog.askstring("Username", "Enter your username:")
            if not self.username:
                self.root.destroy()
                return
            
            # Load server's public key
            try:
                with open("../backend/server_public.pem", "rb") as f:
                    self.server_public_key = serialization.load_pem_public_key(f.read())
            except FileNotFoundError:
                messagebox.showerror("Error", "Server public key not found! Make sure the server is running.")
                self.root.destroy()
                return
            
            # Connect to server
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('127.0.0.1', 5000))
            
            # Send username
            self.client_socket.sendall(self.username.encode())
            
            self.connected = True
            self.status_label.config(text=f"Connected as {self.username}", fg='#27ae60')
            
            # Start receive thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            self.add_message("Connected to server!", "system")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            self.root.destroy()
    
    def receive_messages(self):
        while self.connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    decoded = data.decode()
                    
                    # Handle server responses for file transfers
                    if decoded.startswith("[Server]:") and ("Ready" in decoded or "rejected" in decoded or "not found" in decoded or "sent successfully" in decoded):
                        with self.file_transfer_lock:
                            self.pending_server_response = decoded
                            self.response_event.set()
                        continue
                    
                    # Handle file transfers
                    if decoded.startswith("[File]:"):
                        self.handle_incoming_file(decoded)
                        continue
                    
                    # Handle user join/leave messages to update user list
                    if "joined the chat" in decoded or "left the chat" in decoded:
                        self.update_user_list(decoded)
                    
                    # Display message
                    self.display_message(decoded)
                    
                except UnicodeDecodeError:
                    self.add_message("Received binary data", "system")
                
            except Exception as e:
                if self.connected:
                    self.add_message(f"Connection error: {e}", "system")
                break
        
        self.connected = False
        self.status_label.config(text="Disconnected", fg='#e74c3c')
    
    def handle_incoming_file(self, file_message):
        try:
            self.add_message(file_message, "file")
            
            # Receive file header
            header = self.client_socket.recv(64).decode().strip()
            file_name, file_size = header.split("|")
            file_size = int(file_size)
            consent = messagebox.askyesno(
                "Incoming File",
                f"You have received a file: '{file_name}' ({file_size} bytes).\n\nDo you want to download it?"
            )
    
            if not consent:
                self.add_message(f"❌ You declined the file: '{file_name}'", "system")
                return  # Skip receiving the file
            
            self.add_message(f"Receiving file '{file_name}' ({file_size} bytes)...", "system")
            
            # Receive file data
            file_data = b''
            while len(file_data) < file_size:
                remaining = file_size - len(file_data)
                chunk_size = min(4096, remaining)
                chunk = self.client_socket.recv(chunk_size)
                if not chunk:
                    break
                file_data += chunk
            
            if len(file_data) == file_size:
                # Save file
                os.makedirs("downloads", exist_ok=True)
                file_path = f"downloads/{file_name}"
                with open(file_path, "wb") as f:
                    f.write(file_data)
                self.add_message(f"File '{file_name}' saved successfully in downloads/", "file")
                
                # Ask if user wants to open the file
                if messagebox.askyesno("File Received", f"File '{file_name}' received successfully!\nDo you want to open the downloads folder?"):
                    os.startfile(os.path.abspath("downloads"))
            else:
                self.add_message(f"File transfer incomplete. Expected {file_size}, got {len(file_data)} bytes", "system")
                
        except Exception as e:
            self.add_message(f"Error receiving file: {e}", "system")
    
    def update_user_list(self, message):
        if "joined the chat" in message:
            # Extract username from "[Server]: username joined the chat."
            try:
                username = message.split(": ")[1].split(" joined")[0]
                if username != self.username:
                    self.users_online.add(username)
            except:
                pass
        elif "left the chat" in message:
            # Extract username from "[Server]: username left the chat."
            try:
                username = message.split(": ")[1].split(" left")[0]
                self.users_online.discard(username)
            except:
                pass
        
        # Update listbox
        self.users_listbox.delete(0, tk.END)
        for user in sorted(self.users_online):
            self.users_listbox.insert(tk.END, user)
    
    def display_message(self, message):
        if message.startswith("[Private]"):
            self.add_message(message, "private")
        elif message.startswith("[Server]"):
            self.add_message(message, "system")
        elif message.startswith("[File]"):
            self.add_message(message, "file")
        else:
            self.add_message(message, "user")
    
    def add_message(self, message, tag="user"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{message}\n", tag)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if not message or not self.connected:
            return
        
        self.message_entry.delete(0, tk.END)
        
        try:
            if len(message.encode()) > 200:
                messagebox.showwarning("Message Too Long", "Message too long for RSA encryption. Try breaking it up.")
                return
            
            encrypted = encrypt_message(message, self.server_public_key)
            self.client_socket.sendall(encrypted)
            
        except Exception as e:
            messagebox.showerror("Send Error", f"Error sending message: {e}")
    
    def send_private_message(self):
        selected = self.users_listbox.curselection()
        if not selected:
            messagebox.showwarning("No User Selected", "Please select a user from the list.")
            return
        
        target_user = self.users_listbox.get(selected[0])
        message = simpledialog.askstring("Private Message", f"Message to {target_user}:")
        
        if message:
            try:
                private_msg = f"/msg {target_user} {message}"
                if len(private_msg.encode()) > 200:
                    messagebox.showwarning("Message Too Long", "Message too long for RSA encryption.")
                    return
                
                encrypted = encrypt_message(private_msg, self.server_public_key)
                self.client_socket.sendall(encrypted)
                
                # Show in chat that we sent a private message
                self.add_message(f"[Private] To {target_user}: {message}", "private")
                
            except Exception as e:
                messagebox.showerror("Send Error", f"Error sending private message: {e}")
    
    def send_file(self):
        selected = self.users_listbox.curselection()
        if not selected:
            messagebox.showwarning("No User Selected", "Please select a user to send the file to.")
            return
        
        target_user = self.users_listbox.get(selected[0])
        file_path = filedialog.askopenfilename(title="Select File to Send")
        
        if not file_path:
            return
        
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            self.add_message(f"Sending file '{file_name}' ({file_size} bytes) to {target_user}...", "system")
            
            # Send file command
            cmd = f"/file {target_user} {file_name}"
            self.client_socket.sendall(cmd.encode())
            
            # Wait for server response
            self.response_event.clear()
            if self.response_event.wait(timeout=5.0):
                with self.file_transfer_lock:
                    server_response = self.pending_server_response
                    self.pending_server_response = None
                
                if "Ready" not in server_response:
                    self.add_message(f"Server rejected file: {server_response}", "system")
                    return
            else:
                self.add_message("Timeout waiting for server response", "system")
                return
            
            # Send file size
            size_str = str(file_size).ljust(10)
            self.client_socket.sendall(size_str.encode())
            
            # Send file data
            bytes_sent = 0
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    self.client_socket.sendall(chunk)
                    bytes_sent += len(chunk)
                    
                    # Update progress
                    progress = (bytes_sent / file_size) * 100
                    self.status_label.config(text=f"Sending file... {progress:.1f}%")
            
            self.status_label.config(text=f"Connected as {self.username}")
            self.add_message(f"File '{file_name}' sent successfully to {target_user}!", "file")
            
        except Exception as e:
            self.add_message(f"Error sending file: {e}", "system")
            self.status_label.config(text=f"Connected as {self.username}")
    
    def on_closing(self):
        self.connected = False
        if self.client_socket:
            self.client_socket.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()