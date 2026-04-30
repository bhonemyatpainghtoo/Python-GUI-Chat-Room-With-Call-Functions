import socket
import threading
import time

def get_local_ip():
    """Automatically finds the computer's Wi-Fi / LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

# ─── Server Configuration ────────────────────────────────────────────────────
HOST = get_local_ip()  
PORT = 5555         
BUFFER_SIZE = 1024  

active_clients = {}

def broadcast(message, sender_socket=None):
    for client in list(active_clients.keys()):
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                print(f"[Error] Broadcasting failed: {e}")
                remove_client(client)

def broadcast_user_list():
    users = list(active_clients.values())
    user_list_msg = "USER_LIST:" + ",".join(users)
    broadcast(user_list_msg)

def remove_client(client_socket):
    if client_socket in active_clients:
        username = active_clients[client_socket]
        print(f"[Disconnected] {username} left the chat.")
        del active_clients[client_socket]
        client_socket.close()
        
        broadcast(f"Server: {username} has left the chat.")
        time.sleep(0.1)  
        broadcast_user_list()

def handle_client(client_socket, address):
    try:
        username = client_socket.recv(BUFFER_SIZE).decode('utf-8').strip()
        if not username:
            username = f"User_{address[1]}"
        
        active_clients[client_socket] = username
        print(f"[New Connection] {username} connected from {address}")
        
        broadcast(f"Server: {username} has joined the chat!", client_socket)
        time.sleep(0.1)  # <--- FIX: Prevents the UI crash bug
        broadcast_user_list()

        while True:
            data = client_socket.recv(BUFFER_SIZE)
            
            if not data:
                break 
            
            message = data.decode('utf-8').strip()
            
            # ─── PRIVATE ROUTING PROTOCOL (With IP Injection) ─────────────────
            if message.startswith("@"):
                try:
                    target_tag, private_msg = message.split(" ", 1)
                    target_user = target_tag[1:] 
                    
                    target_socket = None
                    for sock, user in active_clients.items():
                        if user == target_user:
                            target_socket = sock
                            break
                            
                    if target_socket:
                        # --- NEW: Stamp the sender's IP onto the signal ---
                        sender_ip = address[0] 
                        private_msg_with_ip = f"{private_msg}:{sender_ip}"
                        
                        target_socket.send(private_msg_with_ip.encode('utf-8'))
                    else:
                        client_socket.send(f"Server: User {target_user} is not online.".encode('utf-8'))
                except ValueError:
                    pass 
                    
            # ─── PUBLIC BROADCAST ──────────────────────────────────────────────
            else:
                print(f"[{username}] {message}")
                broadcast(message, client_socket)

    except Exception as e:
        print(f"[Error] Connection lost with {address}: {e}")
    finally:
        remove_client(client_socket)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[Server Started] Listening on {HOST}:{PORT}")
        print("Waiting for clients to connect...")

        while True:
            client_socket, address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address), daemon=True)
            thread.start()
            print(f"[Active Connections] {threading.active_count() - 1}")

    except KeyboardInterrupt:
        print("\n[Server Shutting Down]")
    except Exception as e:
        print(f"[Server Error] {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
