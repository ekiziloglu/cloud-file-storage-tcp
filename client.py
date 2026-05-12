# client.py
import socket
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime


# GUI class for the Cloud Storage Client
class ClientGUI:
    def __init__(self, master=None):
        # Create the root window if not provided
        if master is None:
            self.root = tk.Tk()
        else:
            self.root = master
            
        # Configure root window
        self.root.title("Cloud Storage Client")
        self.root.geometry("800x600")
        
        # Client state
        self.is_connected = False
        self.client_socket = None
        self.download_path = ""
        
        # Setup GUI components
        self.setup_gui()
        
    def setup_gui(self):
        # Connection frame for server details and connect/disconnect button

        conn_frame = ttk.Frame(self.root, padding="10")
        conn_frame.pack(fill=tk.X)
        
        # Input fields for server IP, port, and username
        ttk.Label(conn_frame, text="Server IP:").pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.ip_entry.insert(0, "localhost")
        
        ttk.Label(conn_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(conn_frame, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(conn_frame, text="Username:").pack(side=tk.LEFT)
        self.username_entry = ttk.Entry(conn_frame, width=20)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        

        # Connect/Disconnect toggle button
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # File operations frame
        file_frame = ttk.Frame(self.root, padding="10")
        file_frame.pack(fill=tk.X)
        
        # Upload controls
        ttk.Button(file_frame, text="Upload File", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Download File", command=self.download_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Refresh List", command=self.refresh_file_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Set Download Path", command=self.set_download_path).pack(side=tk.LEFT, padx=5)
        
        # File list frame
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview to display server files with columns for filename and owner
        columns = ("Filename", "Owner")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=150)

        # Scrollbar for file list    
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add download path display label
        self.download_path_label = ttk.Label(self.root, text="No download path set", wraplength=400)
        self.download_path_label.pack(pady=5)
        
        # Context menu for right-click actions on files
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Download", command=self.download_file)
        self.context_menu.add_command(label="Delete", command=self.delete_file)
        
        # Bind right-click to show context menu
        self.file_tree.bind("<Button-3>", self.show_context_menu)
        
        # Log frame
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget for logs
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def validate_port(self, port_str):
        """Validate the port input and ensure it's within the acceptable range."""  

        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                return port
            raise ValueError("Port must be between 1024 and 65535")
        except ValueError as e:
            raise ValueError("Invalid port number. " + str(e))

    def log(self, message):
        """Log messages with a timestamp."""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def set_download_path(self):
        """Set the directory where files will be downloaded."""

        path = filedialog.askdirectory(title="Select Download Directory")
        if path:
            self.download_path = path
            self.download_path_label.config(text=f"Download Path: {path}")
            self.log(f"Download path set to: {path}")

    def connect(self):
        """Establish a connection to the server."""

        try:
            if not self.username_entry.get():
                messagebox.showerror("Error", "Please enter a username")
                return

            if not self.port_entry.get():
                messagebox.showerror("Error", "Please enter a port number")
                return

            port = self.validate_port(self.port_entry.get())
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip_entry.get(), port))
            
            # Send username
            self.client_socket.send(self.username_entry.get().encode())
            
            # Receive response
            response = self.client_socket.recv(1024).decode()
            if response.startswith("ERROR"):
                raise Exception(response)
                
            self.is_connected = True
            self.connect_button.config(text="Disconnect")
            self.log(f"Connected to server at {self.ip_entry.get()}:{port}")
            
            # Start listening for notifications in a separate thread
            threading.Thread(target=self.listen_for_notifications, daemon=True).start()
            
            # Get initial file list
            self.refresh_file_list()
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
                
    def disconnect(self):
        """Disconnect from the server."""

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        self.is_connected = False
        self.connect_button.config(text="Connect")
        self.file_tree.delete(*self.file_tree.get_children())
        self.log("Disconnected from server")
        
    def toggle_connection(self):
        """Toggle between connecting and disconnecting."""

        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
            
    def listen_for_notifications(self):
        """Listen for notifications from the server in a separate thread."""
            

        while self.is_connected and self.client_socket:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break
                    
                if data.startswith("NOTIFICATION"):
                    message = data.split("|")[1]
                    self.log(message)
            except:
                break
        self.disconnect()
        
    def upload_file(self):
        """Upload a file to the server."""
        


        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to server")
            return
        
        # Open file dialog to select the file for upload
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filename:
            return  # Exit if no file is selected
            
        try:
            file_size = os.path.getsize(filename)
            base_filename = os.path.basename(filename)
            
            # Send upload command
            command = f"UPLOAD|{base_filename}|{file_size}"
            self.client_socket.send(command.encode())
            
            # Wait for ready signal
            if self.client_socket.recv(1024).decode() != "READY":
                raise Exception("Server not ready")
                
            # Send file
            with open(filename, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    self.client_socket.send(chunk)
                    
            response = self.client_socket.recv(1024).decode()
            if response != "SUCCESS":
                raise Exception(response)
                
            self.log(f"Successfully uploaded {base_filename}")
            self.refresh_file_list()
            
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))
            
    def refresh_file_list(self):
        """Request the server for the current list of files."""

        if not self.is_connected:
            return
            
        try:
            self.client_socket.send("LIST".encode())
            response = self.client_socket.recv(4096).decode()
            files = json.loads(response)
            
            self.file_tree.delete(*self.file_tree.get_children())
            for file in files:
                self.file_tree.insert("", tk.END, values=(file["filename"], file["owner"]))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get file list: {str(e)}")
            
    def show_context_menu(self, event):
        """Show the right-click context menu."""

        if not self.is_connected:
            return
            
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def download_file(self):
        """Download a selected file from the server."""
    

        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to server")
            return
            
        if not self.download_path:
            messagebox.showerror("Error", 
                "Please set download path first using 'Set Download Path' button")
            return
            
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a file to download")
            return
            
        item = self.file_tree.item(selected[0])
        filename = item['values'][0]
        owner = item['values'][1]
        
        # Check if file already exists
        target_path = os.path.join(self.download_path, filename)
        if os.path.exists(target_path):
            if not messagebox.askyesno("File exists", 
                f"File {filename} already exists. Do you want to overwrite it?"):
                return
        
        try:
            command = f"DOWNLOAD|{filename}|{owner}"
            self.client_socket.send(command.encode())
            
            response = self.client_socket.recv(1024).decode()
            if response.startswith("ERROR"):
                raise Exception(response)
                
            # Parse size
            _, size = response.split("|")
            file_size = int(size)
            
            # Show progress dialog
            progress = tk.Toplevel(self.root)
            progress.title("Downloading...")
            progress.geometry("300x150")
            
            # Center progress window
            progress.geometry("+%d+%d" % (
                self.root.winfo_x() + self.root.winfo_width()/2 - 150,
                self.root.winfo_y() + self.root.winfo_height()/2 - 75))
                
            ttk.Label(progress, text=f"Downloading {filename}...").pack(pady=10)
            progress_bar = ttk.Progressbar(progress, length=200, mode='determinate')
            progress_bar.pack(pady=10)
            
            # Send ready signal
            self.client_socket.send("READY".encode())
            
            # Receive file
            with open(target_path, 'wb') as f:
                remaining = file_size
                while remaining > 0:
                    chunk = self.client_socket.recv(min(4096, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
                    progress_bar['value'] = ((file_size - remaining) / file_size) * 100
                    progress.update()
            
            progress.destroy()
            self.log(f"Successfully downloaded {filename}")
            
            if messagebox.askyesno("Download Complete", 
                f"Successfully downloaded {filename}\nDo you want to open the download folder?"):
                self.open_download_folder()
                
        except Exception as e:
            messagebox.showerror("Download Error", str(e))

    def open_download_folder(self):
        """Open the folder where files are downloaded."""

        if self.download_path:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(self.download_path)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    subprocess.Popen(['open', self.download_path])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open download folder: {str(e)}")
            
    def delete_file(self):
        """Delete a selected file from the server."""

        if not self.is_connected:
            return
            
        selected = self.file_tree.selection()
        if not selected:
            return
            
        item = self.file_tree.item(selected[0])
        filename = item['values'][0]
        owner = item['values'][1]

        # Ensure the user can only delete their own files
        if owner != self.username_entry.get():
            messagebox.showerror("Error", "You can only delete your own files")
            return
            
        try:
            command = f"DELETE|{filename}"
            self.client_socket.send(command.encode())
            
            response = self.client_socket.recv(1024).decode()
            if response != "SUCCESS":
                raise Exception(response)
                
            self.log(f"Successfully deleted {filename}")
            self.refresh_file_list()
            
        except Exception as e:
            messagebox.showerror("Delete Error", str(e))
            
    def run(self):
        """Start the client GUI."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle GUI closure and cleanup."""
        if self.is_connected:
            self.disconnect()
        self.root.destroy()

# Main entry point for the client application

def main():
    root = tk.Tk()
    app = ClientGUI(root)
    app.run()

if __name__ == "__main__":
    main()