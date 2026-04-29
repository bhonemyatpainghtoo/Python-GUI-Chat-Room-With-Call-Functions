from vidstream import AudioSender
from vidstream import AudioReceiver
import threading

sender = None
receiver = None
send_thread = None
receive_thread = None

def start_voice(ip, port):
    global sender, receiver, send_thread, receive_thread
    
    # create instances of AudioSender and AudioReceiver
    receiver = AudioReceiver(ip, port)
    sender = AudioSender(ip, port)
    
    # create threads for sending and receiving audio
    receive_thread = threading.Thread(target=receiver.start_server)
    send_thread = threading.Thread(target=sender.start_stream)

    # start threads for sending and receiving audio
    receive_thread.start()
    send_thread.start()

    print("Voice communication started.")


def stop_voice():
    global sender, receiver

    if sender:
        sender.stop_stream()
        sender = None

    if receiver:
        receiver.stop_server()
        receiver = None

    print("Voice communication stopped.")
