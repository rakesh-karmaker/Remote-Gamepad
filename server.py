import socket
import os
from dotenv import load_dotenv
import sys
import vgamepad as vg
from controller.gamepad import apply_payload_to_gamepad
from controller.state import current_axis_values

# Load variables from .env into environment
load_dotenv()

SERVER_IP = os.getenv('SERVER_IP', '')
SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))

print(f"Starting server at {SERVER_IP}:{SERVER_PORT}")

# initialize the virtual gamepad
gamepad = vg.VX360Gamepad()

# Create a UDP socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the address and port
serverSocket.bind((SERVER_IP, SERVER_PORT))

try:
    while True:
        # Receive controllerInput from client
        payload, clientAddress = serverSocket.recvfrom(2048) # buffer size is 2048 bytes
        apply_payload_to_gamepad(gamepad, payload.decode(), current_axis_values)

except KeyboardInterrupt:
    print("Server is shutting down.")
    serverSocket.close()
    sys.exit(0)