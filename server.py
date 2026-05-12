# server.py
import socket
import threading
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

class ServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cloud Storage Server")
        self.root.geometry("800x600")
        
        # Server state
        self.is_running = False
        self.server_socket = None
        self.storage_path = ""
        self.connected_clients = {}  # {client_name: connection}
        self.files_info = {}  # {filename: {"owner": owner, "original_name": original_name}}
        
        self.setup_gui()
        self.load_files_info()
        
    def setup_gui(self):
        # Server controls frame
        controls_frame = ttk.Frame(self.root, padding="10")
        controls_frame.pack(fill=tk.X)
        
        # Port entry
        ttk.Label(controls_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(controls_frame, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # Storage path selection
        ttk.Label(controls_frame, text="Storage Path:").pack(side=tk.LEFT, padx=5)
        self.path_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=self.path_var, width=40).pack(side=tk.LEFT)
        ttk.Button(controls_frame, text="Browse", command=self.browse_path).pack(side=tk.LEFT, padx=5)
        
        # Start/Stop button
        self.start_button = ttk.Button(controls_frame, text="Start Server", command=self.toggle_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log display
        self.log_text = tk.Text(log_frame, height=20, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def validate_port(self, port_str):
        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                return port
            raise ValueError("Port must be between 1024 and 65535")
        except ValueError as e:
            raise ValueError("Invalid port number. " + str(e))
            
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)
            
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def load_files_info(self):
        try:
            with open("files_info.json", "r") as f:
                self.files_info = json.load(f)
        except FileNotFoundError:
            self.files_info = {}
            
    def save_files_info(self):
        with open("files_info.json", "w") as f:
            json.dump(self.files_info, f)
            
    def start_server(self):
        if not self.path_var.get():
            messagebox.showerror("Error", "Please select storage path first")
            return
            
        if not self.port_entry.get():
            messagebox.showerror("Error", "Please enter a port number")
            return
            
        try:
            port = self.validate_port(self.port_entry.get())
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('', port))
            self.server_socket.listen(5)
            
            self.storage_path = self.path_var.get()
            os.makedirs(self.storage_path, exist_ok=True)
            
            self.is_running = True
            self.start_button.config(text="Stop Server")
            
            # Start accepting clients in a separate thread
            threading.Thread(target=self.accept_clients, daemon=True).start()
            
            self.log(f"Server started on port {port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
            
    def stop_server(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
            
        for client in self.connected_clients.values():
            try:
                client.close()
            except:
                pass
                
        self.connected_clients.clear()
        self.start_button.config(text="Start Server")
        self.log("Server stopped")
        
    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
            
    def accept_clients(self):
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, 
                              args=(client_socket, address),
                              daemon=True).start()
            except:
                if self.is_running:
                    self.log("Error accepting client connection")
                    
    def handle_client(self, client_socket, address):
        client_name = None
        try:
            # First message should be the client name
            client_name = client_socket.recv(1024).decode()
            
            if client_name in self.connected_clients:
                client_socket.send("ERROR: Name already in use".encode())
                client_socket.close()
                return
                
            self.connected_clients[client_name] = client_socket
            client_socket.send("OK".encode())
            self.log(f"Client {client_name} connected from {address}")
            
            while True:
                command = client_socket.recv(1024).decode()
                if not command:
                    break
                    
                command_parts = command.split('|')
                operation = command_parts[0]
                
                if operation == "UPLOAD":
                    self.handle_upload(client_socket, client_name, command_parts[1:])
                elif operation == "DOWNLOAD":
                    self.handle_download(client_socket, command_parts[1:])
                elif operation == "LIST":
                    self.handle_list(client_socket)
                elif operation == "DELETE":
                    self.handle_delete(client_socket, client_name, command_parts[1])
                    
        except Exception as e:
            self.log(f"Error handling client: {str(e)}")
        finally:
            if client_name and client_name in self.connected_clients:
                del self.connected_clients[client_name]
            try:
                client_socket.close()
            except:
                pass
            self.log(f"Client {client_name} disconnected")
            
    def handle_upload(self, client_socket, client_name, params):
        filename = params[0]
        file_size = int(params[1])
        
        # Create unique server filename
        server_filename = f"{client_name}_{filename}"
        
        # Send ready signal
        client_socket.send("READY".encode())
        
        # Receive and save file
        with open(os.path.join(self.storage_path, server_filename), 'wb') as f:
            remaining = file_size
            while remaining > 0:
                chunk = client_socket.recv(min(4096, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
                
        # Update files info
        self.files_info[server_filename] = {
            "owner": client_name,
            "original_name": filename
        }
        self.save_files_info()
        
        self.log(f"File {filename} uploaded by {client_name}")
        client_socket.send("SUCCESS".encode())
        
    def handle_download(self, client_socket, params):
        filename = params[0]
        owner = params[1]
        server_filename = f"{owner}_{filename}"
        
        if not os.path.exists(os.path.join(self.storage_path, server_filename)):
            client_socket.send("ERROR: File not found".encode())
            return
            
        # Send file size first
        file_size = os.path.getsize(os.path.join(self.storage_path, server_filename))
        client_socket.send(f"SIZE|{file_size}".encode())
        
        # Wait for ready signal
        if client_socket.recv(1024).decode() != "READY":
            return
            
        # Send file
        with open(os.path.join(self.storage_path, server_filename), 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                client_socket.send(chunk)
                
        self.log(f"File {filename} downloaded from {owner}")
        
        # Notify owner if connected
        if owner in self.connected_clients:
            try:
                notification = f"NOTIFICATION|Your file {filename} was downloaded"
                self.connected_clients[owner].send(notification.encode())
            except:
                pass
                
    def handle_list(self, client_socket):
        file_list = []
        for server_filename, info in self.files_info.items():
            file_list.append({
                "filename": info["original_name"],
                "owner": info["owner"]
            })
        
        client_socket.send(json.dumps(file_list).encode())
        
    def handle_delete(self, client_socket, client_name, filename):
        server_filename = f"{client_name}_{filename}"
        
        if server_filename not in self.files_info:
            client_socket.send("ERROR: File not found".encode())
            return
            
        if self.files_info[server_filename]["owner"] != client_name:
            client_socket.send("ERROR: Permission denied".encode())
            return
            
        try:
            os.remove(os.path.join(self.storage_path, server_filename))
            del self.files_info[server_filename]
            self.save_files_info()
            client_socket.send("SUCCESS".encode())
            self.log(f"File {filename} deleted by {client_name}")
        except Exception as e:
            client_socket.send(f"ERROR: {str(e)}".encode())
            
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        if self.is_running:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    server = ServerGUI()
    server.run()