import tkinter as tk
from tkinter import scrolledtext, messagebox

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Voice & Text Chat")
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        # attach networking functions
        self.on_connect = None
        self.on_send_message = None
        self.on_start_call = None
        self.on_end_call = None

        self.setup_connection_screen()

    def setup_connection_screen(self):
        self.conn_frame = tk.Frame(self.root, pady=100)
        self.conn_frame.pack()

        tk.Label(self.conn_frame, text="Join Chat Room", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(self.conn_frame, text="Server IP:").grid(row=1, column=0, sticky="e", pady=5)
        self.ip_entry = tk.Entry(self.conn_frame, width=20)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=1, column=1, pady=5)

        tk.Label(self.conn_frame, text="Port:").grid(row=2, column=0, sticky="e", pady=5)
        self.port_entry = tk.Entry(self.conn_frame, width=20)
        self.port_entry.insert(0, "5555")
        self.port_entry.grid(row=2, column=1, pady=5)

        tk.Label(self.conn_frame, text="Username:").grid(row=3, column=0, sticky="e", pady=5)
        self.username_entry = tk.Entry(self.conn_frame, width=20)
        self.username_entry.grid(row=3, column=1, pady=5)

        connect_btn = tk.Button(self.conn_frame, text="Connect", command=self.handle_connect, bg="lightblue")
        connect_btn.grid(row=4, column=0, columnspan=2, pady=15, ipadx=20)

    def handle_connect(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        username = self.username_entry.get()

        if not ip or not port or not username:
            messagebox.showwarning("Error", "All fields are required!")
            return

        if self.on_connect:
            success = self.on_connect(ip, int(port), username)
            if success:
                self.conn_frame.destroy()
                self.setup_chat_screen()

    def setup_chat_screen(self):
        self.chat_frame = tk.Frame(self.root, padx=10, pady=10)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)

        # Left Side: Chat Area
        left_frame = tk.Frame(self.chat_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(left_frame, state='disabled', wrap=tk.WORD, width=40, height=20)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        input_frame = tk.Frame(left_frame)
        input_frame.pack(fill=tk.X)

        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", lambda event: self.handle_send()) 

        send_btn = tk.Button(input_frame, text="Send", command=self.handle_send, bg="lightgreen")
        send_btn.pack(side=tk.RIGHT)

        # Right Side: Users & Call Controls
        right_frame = tk.Frame(self.chat_frame, padx=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right_frame, text="Active Users").pack()
        
        self.user_listbox = tk.Listbox(right_frame, height=15, width=20)
        self.user_listbox.pack(pady=(0, 10))

        call_btn = tk.Button(right_frame, text="📞 Start Call", command=self.handle_call, bg="lightgreen", width=15)
        call_btn.pack(pady=5)

        end_call_btn = tk.Button(right_frame, text="🛑 End Call", command=self.handle_end_call, bg="salmon", width=15)
        end_call_btn.pack(pady=5)

    def handle_send(self):
        msg = self.msg_entry.get().strip()
        if msg and self.on_send_message:
            self.on_send_message(msg)
            self.msg_entry.delete(0, tk.END)

    def handle_call(self):
        if self.on_start_call:
            self.on_start_call()

    def handle_end_call(self):
        if self.on_end_call:
            self.on_end_call()

    def display_message(self, message):
        """use this to print incoming socket messages."""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END) 
        self.chat_display.config(state='disabled')

    def update_users(self, user_list):
        """use this to update the listbox with active usernames."""
        self.user_listbox.delete(0, tk.END)
        for user in user_list:
            self.user_listbox.insert(tk.END, user)

    def show_incoming_call_popup(self, caller_name):
        """use this when the server sends an INCOMING_CALL signal."""
        return messagebox.askyesno("Incoming Call", f"{caller_name} is calling you. Accept?")

    def show_error(self, message, title="Error"):
        """General purpose error popup."""
        messagebox.showerror(title, message)


# Running file + dummy functions 
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    
    # Dummy functions simulating network/audio actions
    def example_connect(ip, port, user):
        print(f"NETWORK: Connecting to {ip}:{port} as {user}...")
        return True # Tells GUI the connection was successful

    def example_send(msg):
        print(f"NETWORK: Sending -> {msg}")
        # Display the message locally so the user sees what they typed
        app.display_message(f"You: {msg}")
        
        # Simulate updating the user list after connecting
        app.update_users(["John", "Alice", "Bob"])

    def example_start_call():
        print("AUDIO: Starting voice stream...")
        # Simulating receiving a call from someone else
        app.show_incoming_call_popup("Teammate")

    def example_end_call():
        print("AUDIO: Ending voice stream...")

    #Attaching the functions to the GUI hooks
    app.on_connect = example_connect
    app.on_send_message = example_send
    app.on_start_call = example_start_call
    app.on_end_call = example_end_call

    root.mainloop()
