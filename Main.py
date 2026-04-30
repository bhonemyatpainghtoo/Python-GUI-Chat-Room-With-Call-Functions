import tkinter as tk
import random 
from Client_text import (
    TextClient, 
    SIGNAL_INCOMING_CALL, 
    SIGNAL_CALL_ACCEPTED, 
    SIGNAL_CALL_DECLINED, 
    SIGNAL_CALL_ENDED
)
from Client_gui import ChatGUI
from Client_audio import start_voice, stop_voice

def main():
    root = tk.Tk()
    
    app = ChatGUI(root)       
    client = TextClient()     

    # Track current call state
    current_call_partner = None
    current_call_ip = None      # <--- NEW: Tracks the dynamic target IP
    current_rx_port = 0
    current_tx_port = 0

    def handle_connect(ip, port, username):
        success = client.connect(ip, port, username)
        if success:
            client.start_receiving()
        return success

    def handle_send(msg):
        formatted_msg = f"{client.username}: {msg}"
        client.send_message(formatted_msg)
        app.display_message(f"You: {msg}")

    def handle_start_call(target):
        nonlocal current_call_partner, current_rx_port, current_tx_port
        
        if not target or target == client.username or target == "Broadcast":
            app.show_error("Please click a valid user from the list to call.")
            return

        current_call_partner = target
        
        current_rx_port = random.randint(20000, 50000)
        current_tx_port = random.randint(20000, 50000)
        while current_tx_port == current_rx_port:
            current_tx_port = random.randint(20000, 50000)
        
        call_signal = f"@{target} {SIGNAL_INCOMING_CALL}:{client.username}:{current_rx_port}:{current_tx_port}"
        client.send_message(call_signal)
        app.display_message(f"System: Ringing {target}...")

    def handle_end_call():
        nonlocal current_call_partner, current_call_ip
        if current_call_partner:
            client.send_message(f"@{current_call_partner} {SIGNAL_CALL_ENDED}:{client.username}")
            
        stop_voice()
        app.display_message("System: You ended the call.")
        current_call_partner = None
        current_call_ip = None

    app.on_connect = handle_connect
    app.on_send_message = handle_send
    app.on_start_call = handle_start_call
    app.on_end_call = handle_end_call

    def handle_message_received(msg):
        if msg.startswith("USER_LIST:"):
            users_string = msg.replace("USER_LIST:", "")
            user_list = users_string.split(",") if users_string else []
            
            def apply_users():
                if hasattr(app, 'user_listbox'):
                    app.update_users(user_list + ["Broadcast"])
                else:
                    root.after(50, apply_users) 
            
            apply_users()
            return

        if not msg.startswith(f"{client.username}:"):
            def apply_msg():
                if hasattr(app, 'chat_display'):
                    app.display_message(msg)
                else:
                    root.after(50, apply_msg)
            apply_msg()

    def handle_signal_received(signal_msg):
        nonlocal current_call_partner, current_call_ip, current_rx_port, current_tx_port
        
        # Parse the signal
        parts = signal_msg.split(":")
        base_signal = parts[0]
        other_user = parts[1] if len(parts) > 1 else "Unknown"
        
        if base_signal == SIGNAL_INCOMING_CALL:
            caller_rx = int(parts[2])
            caller_tx = int(parts[3])
            caller_ip = parts[4]  # <--- NEW: Extract the IP injected by the server
            
            accepted = app.show_incoming_call_popup(other_user)
            if accepted:
                current_call_partner = other_user
                current_call_ip = caller_ip 
                current_rx_port = caller_tx  
                current_tx_port = caller_rx  
                
                client.send_message(f"@{other_user} {SIGNAL_CALL_ACCEPTED}:{client.username}")
                start_voice(current_call_ip, current_rx_port, current_tx_port)
                app.display_message(f"System: Call with {other_user} started.")
            else:
                client.send_message(f"@{other_user} {SIGNAL_CALL_DECLINED}:{client.username}")
                app.display_message(f"System: Call from {other_user} declined.")

        elif base_signal == SIGNAL_CALL_ACCEPTED:
            receiver_ip = parts[2] # <--- NEW: Extract the receiver's IP
            current_call_ip = receiver_ip
            
            app.display_message(f"System: {other_user} accepted! Connecting audio...")
            start_voice(current_call_ip, current_rx_port, current_tx_port)

        elif base_signal == SIGNAL_CALL_DECLINED:
            app.display_message(f"System: {other_user} declined your call.")
            current_call_partner = None

        elif base_signal == SIGNAL_CALL_ENDED:
            stop_voice()
            app.display_message(f"System: {other_user} ended the call.")
            current_call_partner = None
            current_call_ip = None

    def handle_error(err_msg):
        app.show_error(err_msg)

    client.on_message_received = handle_message_received
    client.on_signal_received = handle_signal_received
    client.on_error = handle_error

    def on_closing():
        client.disconnect()
        stop_voice()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
