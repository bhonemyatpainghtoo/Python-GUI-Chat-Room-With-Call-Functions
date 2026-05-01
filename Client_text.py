import socket
import threading
import time

#testing
HOST = '127.0.0.1'
PORT = 5555
BUFFER_SIZE = 1024

# reconnect incase connecting fails
MAX_RETRIES = 3
RETRY_DELAY = 3

# SIGNAL NAMES FINAL
SIGNAL_INCOMING_CALL = "INCOMING_CALL"
SIGNAL_CALL_ACCEPTED = "CALL_ACCEPTED"
SIGNAL_CALL_DECLINED = "CALL_DECLINED"
SIGNAL_CALL_ENDED    = "CALL_ENDED"

#set for signal names
SIGNALS = {SIGNAL_INCOMING_CALL, SIGNAL_CALL_ACCEPTED, SIGNAL_CALL_DECLINED, SIGNAL_CALL_ENDED}


class TextClient:

    def __init__(self):
        self.sock = None
        self.connected = False                # Connection status
        self._intentional_disconnect = False  # prevents reconnecting if the user closes the app intentionally
        self._host = HOST                     # host
        self._port = PORT                     # port
        self.username = None                  # Username to connect

        # Callbacks
        self.on_message_received = None   # chat message arrives call
        self.on_signal_received  = None   #call signal arrives call
        self.on_error            = None   #if any error occurs

    #Connecting

    def connect(self, host=HOST, port=PORT, username=None):
        # establishing TCP connection
        self._host = host
        self._port = port
        self._intentional_disconnect = False

        if username:
            self.username = username

        try:
            #TCP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to server
            self.sock.connect((host, port))
            self.connected = True

            # Send username to the server
            if self.username:
                self.sock.send(self.username.encode('utf-8'))

            print(f"[Connected] {host}:{port}  User: {self.username}")
            return True

        except Exception as e:
            print(f"[Connection Failed] {e}")
            self.connected = False
            if self.on_error:
                self.on_error(f"Connection Failed: {e}")
            return False

    def disconnect(self):
        #close the connection to the server
        self._intentional_disconnect = True   # Mark as intentional to prevent reconnect after loop exits
        self.connected = False

        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass  # May already be closed
            try:
                self.sock.close()
                print("[Disconnected]")
            except Exception as e:
                print(f"[Disconnect Error] {e}")

    # receiving function

    def start_receiving(self):
        # starts the receive loop after successful connection
        receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        receive_thread.start()
        print("[Receiving Started]")

    def _receive_loop(self):
        while self.connected:
            try:
                raw_data = self.sock.recv(BUFFER_SIZE)

                # if no data then server closed
                if not raw_data:
                    print("[Server Disconnected]")
                    self.connected = False
                    break

                # strip to remove spaces and new lines for message to arrive correctly
                message = raw_data.decode('utf-8').strip()

                if message:
                    self._handle_incoming(message)

            except Exception as e:
                if self.connected:
                    print(f"[Receive Error] {e}")
                    if self.on_error:
                        self.on_error(f"Receive Error: {e}")
                self.connected = False
                break

        # Attempt reconnect
        if not self._intentional_disconnect:
            self._reconnect()

    def _handle_incoming(self, message):
        # makes sure the message recieved is either a normal message or a signal call
        # startswith() used so signals with extra data (e.g. "INCOMING_CALL:username") still match
        for signal in SIGNALS:
            if message.startswith(signal):
                print(f"[Signal Detected] {signal}")
                if self.on_signal_received:
                    self.on_signal_received(message)
                return

        print(f"[Message Received] {message}")
        if self.on_message_received:
            self.on_message_received(message)

 # sending messages

    def send_message(self, message):
        if not self.connected:
            print("[Send Failed] Not connected to server")
            if self.on_error:
                self.on_error("Send Failed: Not connected to server")
            return False

        try:
            self.sock.send(message.encode('utf-8'))
            print(f"[Message Sent] {message}")
            return True

        except Exception as e:
            print(f"[Send Error] {e}")
            if self.on_error:
                self.on_error(f"Send Error: {e}")
            return False

    def send_signal(self, signal):
        # Block unknown signals to prevent typos or invalid calls
        if signal not in SIGNALS:
            print(f"[Warning] Unknown signal: {signal}")
            return False

        return self.send_message(signal)

    def _reconnect(self):
        # reconnecting if connection fails for 3 times.
        print(f"[Preparing Reconnect] Attempting up to {MAX_RETRIES} times...")

        for attempt in range(1, MAX_RETRIES + 1):
            time.sleep(RETRY_DELAY)

            if self._intentional_disconnect:
                print("[Reconnect Cancelled]")
                return

            print(f"[Reconnecting] {attempt}/{MAX_RETRIES}...")

            if self.connect(self._host, self._port, self.username):
                print("[Reconnected]")
                self.start_receiving()
                return

        # All attempts fail
        print("[Reconnect Failed] Max retries exceeded")
        if self.on_error:
            self.on_error("Reconnect failed. Please check server and restart.")
