# Python GUI ChatRoom With Call Functions

A lightweight, chat and voice application built with Python. This project features a server for broadcasting group text messages and a Peer to peer (P2P) routing protocol for voice calls. It utilizes TCP sockets for text communication and the `vidstream` library for voice calls, all in a custom Tkinter GUI.

## Features

*   **Group Text Chat:** Users can join a central server chatroom and broadcast text messages to all connected clients instantly.
*   **Peer to Peer Voice Calling:** Users can select a specific active user from the interface and start a private voice call.
*   **Server Routing & IP Injection:** The server acts as a router. When a call is started, it intercepts the signal, puts the sender's IP address onto the packet, and routes it only to the target user. 
*   **Dynamic Port Allocation:** To prevent OS-level socket lockouts (like Windows `TIME_WAIT`), the client generates randomized, unique audio ports for every single voice call.
*   **Auto-Updating User List:** The server automatically detects client connections/disconnections and broadcasts updated active user lists to all clients.
*   **Very Modular:** The codebase separates the Model (Socket Networking), View (Tkinter UI), and Audio subsystems, using a central Controller (`Main.py`) to manage threads and calls safely.

## Limitations

*   **User to User Audio Only:** Because the application uses direct Peer to Peer connections for voice data, audio calls are limited to two users. Group voice calling is not supported.
*   **No NAT Traversal:** The application does not utilize STUN/TURN servers. So it can only work in a local setting on 1 network.
*   **Enterprise Network Restrictions:** When running on massive networks (like Company or University Wi-Fi), clients must be on the exact same subnet for P2P audio to connect.
