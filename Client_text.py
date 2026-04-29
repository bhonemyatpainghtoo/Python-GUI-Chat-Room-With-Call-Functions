import socket
import threading
import time

# ─── Server Configuration ────────────────────────────────────────────────────
HOST = '127.0.0.1'  # Local testing IP
PORT = 5050         # Server port number
BUFFER_SIZE = 1024  # Max bytes per recv() call

# ─── Reconnect Configuration ─────────────────────────────────────────────────
MAX_RETRIES = 3    # Maximum number of reconnect attempts
RETRY_DELAY = 3    # Seconds to wait between retries

# ─── Signal Constants ─────────────────────────────────────────────────────────
# Confirm exact signal format with team leader (server side)
SIGNAL_INCOMING_CALL = "INCOMING_CALL"
SIGNAL_CALL_ACCEPTED = "CALL_ACCEPTED"
SIGNAL_CALL_DECLINED = "CALL_DECLINED"
SIGNAL_CALL_ENDED    = "CALL_ENDED"

# Use a set for fast lookup and easy extension
SIGNALS = {SIGNAL_INCOMING_CALL, SIGNAL_CALL_ACCEPTED, SIGNAL_CALL_DECLINED, SIGNAL_CALL_ENDED}


class TextClient:
    """
    Handles all text communication with the server.
    """

    def __init__(self):
        self.sock = None                      # Active socket object
        self.connected = False                # Connection status flag
        self._intentional_disconnect = False  # Prevents reconnect after manual disconnect
        self._host = HOST                     # Stored host for reconnect
        self._port = PORT                     # Stored port for reconnect
        self.username = None                  # Username sent to server on connect

        # Callbacks - must be set by main.py before calling start_receiving()
        self.on_message_received = None   # Fires when a regular chat message arrives
        self.on_signal_received  = None   # Fires when a call signal arrives
        self.on_error            = None   # Fires when any error occurs

    # ─── Connection ──────────────────────────────────────────────────────────

    def connect(self, host=HOST, port=PORT, username=None):
        """
        Attempts to establish a TCP socket connection to the server.

        Args:
            host (str):     Server IP address
            port (int):     Server port number
            username (str): Username to register with server

        Returns:
            bool: True if connected, False if failed
        """
        self._host = host
        self._port = port
        self._intentional_disconnect = False

        if username:
            self.username = username

        try:
            # Create TCP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to server
            self.sock.connect((host, port))
            self.connected = True

            # Send username to server - adjust format based on server protocol
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
        """
        Safely closes the connection to the server.
        """
        # Mark as intentional to prevent reconnect after loop exits
        self._intentional_disconnect = True
        self.connected = False

        if self.sock:
            try:
                # shutdown() forces the blocking recv() to raise an exception and exit cleanly
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass  # May already be closed
            try:
                self.sock.close()
                print("[Disconnected]")
            except Exception as e:
                print(f"[Disconnect Error] {e}")

    # ─── Receiving ───────────────────────────────────────────────────────────

    def start_receiving(self):
        """
        Starts the message receive loop in a background daemon thread.
        Must be called after connect() succeeds.
        """
        receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        receive_thread.start()
        print("[Receiving Started]")

    def _receive_loop(self):
        """
        Internal loop that continuously receives messages from the server.
        Do not call directly - use start_receiving() instead.
        """
        while self.connected:
            try:
                raw_data = self.sock.recv(BUFFER_SIZE)

                # Empty data means server closed the connection
                if not raw_data:
                    print("[Server Disconnected]")
                    self.connected = False
                    break

                # strip() removes whitespace/newlines to prevent signal mismatch
                message = raw_data.decode('utf-8').strip()

                if message:
                    self._handle_incoming(message)

            except Exception as e:
                # Only handle error if not an intentional disconnect
                if self.connected:
                    print(f"[Receive Error] {e}")
                    if self.on_error:
                        self.on_error(f"Receive Error: {e}")
                self.connected = False
                break

        # Attempt reconnect if disconnect was not intentional
        if not self._intentional_disconnect:
            self._reconnect()

    def _handle_incoming(self, message):
        """
        Routes received message as a call signal or regular chat message.
        Do not call directly - called automatically by _receive_loop().

        Args:
            message (str): Stripped message received from server
        """
        # startswith() used so signals with extra data (e.g. "INCOMING_CALL:username") still match
        for signal in SIGNALS:
            if message.startswith(signal):
                print(f"[Signal Detected] {signal}")
                if self.on_signal_received:
                    self.on_signal_received(signal)
                return

        # Not a signal - treat as regular chat message
        print(f"[Message Received] {message}")
        if self.on_message_received:
            self.on_message_received(message)

    # ─── Sending ─────────────────────────────────────────────────────────────

    def send_message(self, message):
        """
        Sends a plain text message to the server.

        Args:
            message (str): Message text to send

        Returns:
            bool: True if sent successfully, False otherwise
        """
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
        """
        Sends a special call-control signal to the server.
        Signal format may need adjustment based on server protocol.

        Args:
            signal (str): Signal to send - must be one of the signal constants

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Block unknown signals to prevent typos or invalid calls
        if signal not in SIGNALS:
            print(f"[Warning] Unknown signal: {signal}")
            return False

        return self.send_message(signal)

    # ─── Reconnect ───────────────────────────────────────────────────────────

    def _reconnect(self):
        """
        Automatically attempts to reconnect after an unexpected disconnection.
        Do not call directly - called automatically by _receive_loop().
        """
        print(f"[Preparing Reconnect] Attempting up to {MAX_RETRIES} times...")

        for attempt in range(1, MAX_RETRIES + 1):
            time.sleep(RETRY_DELAY)

            # Cancel if disconnect() was called during sleep
            if self._intentional_disconnect:
                print("[Reconnect Cancelled]")
                return

            print(f"[Reconnecting] {attempt}/{MAX_RETRIES}...")

            if self.connect(self._host, self._port, self.username):
                print("[Reconnected]")
                self.start_receiving()
                return

        # All attempts failed
        print("[Reconnect Failed] Max retries exceeded")
        if self.on_error:
            self.on_error("Reconnect failed. Please check server and restart.")


# ─── Usage Example ───────────────────────────────────────────────────────────
# Use like this in main.py:
#
# from Client_text import TextClient
#
# text_client = TextClient()
#
# # Connect callbacks
# text_client.on_message_received = gui.display_message    # Display message in GUI
# text_client.on_signal_received  = main.handle_signal     # Handle signal in main.py
# text_client.on_error            = gui.show_error         # Show error in GUI
#
# # Connect to server and start receiving
# text_client.connect(username="Alice")
# text_client.start_receiving()
#
# # Send a chat message
# text_client.send_message("Hello!")
#
# # Send a call signal
# text_client.send_signal("INCOMING_CALL")
#
# # Disconnect
# text_client.disconnect()
