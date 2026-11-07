import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# Crea il socket UDP
udp_socket = socket.socket(socket.AF_INET, # Internet
                           socket.SOCK_DGRAM) # UDP

# Messaggio da inviare
messaggio = "Ciao!"

# Invia il messaggio al receiver
udp_socket.sendto(messaggio.encode(), (UDP_IP, UDP_PORT))
print(f"Messaggio inviato a {UDP_IP}:{UDP_PORT}")

# Chiude il socket
udp_socket.close()