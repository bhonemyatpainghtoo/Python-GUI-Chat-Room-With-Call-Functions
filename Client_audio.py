import threading
from vidstream import AudioSender, AudioReceiver

sender = None
receiver = None
send_thread = None
receive_thread = None

def start_voice(target_ip, my_receive_port, target_send_port):
    global sender, receiver, send_thread, receive_thread
    
    if sender or receiver:
        stop_voice()

    try:
        receiver = AudioReceiver('0.0.0.0', my_receive_port)
        sender = AudioSender(target_ip, target_send_port)
        
        receive_thread = threading.Thread(target=receiver.start_server, daemon=True)
        send_thread = threading.Thread(target=sender.start_stream, daemon=True)

        receive_thread.start()
        send_thread.start()

        return True
    except Exception as e:
        print(f"[Audio Error] {e}");
        return False

def stop_voice():
    global sender, receiver, send_thread, receive_thread

    if sender:
        try:
            sender.stop_stream()
        except Exception:
            pass
        sender = None

    if receiver:
        try:
            receiver.stop_server()
        except Exception:
            pass
        receiver = None
        
    send_thread = None
    receive_thread = None

