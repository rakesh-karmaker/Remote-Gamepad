import socket
import os
from dotenv import load_dotenv
import vgamepad as vg
from inputs import get_gamepad
from controller.gamepad import apply_payload_to_gamepad
from controller.state import current_axis_values

# Load variables from .env into environment
load_dotenv()

REMOTE_SERVER_IP = os.getenv('REMOTE_SERVER_IP', '')
REMOTE_SERVER_PORT = int(os.getenv('REMOTE_SERVER_PORT', '5000'))

print(f"Connecting to server at {REMOTE_SERVER_IP}:{REMOTE_SERVER_PORT}")

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# initialize the virtual gamepad
gamepad = vg.VX360Gamepad()

while True:
    # send the user's virtual gamepad input to the server
    events = get_gamepad()
    for event in events:
        controller_input = f"{event.ev_type},{event.code},{event.state}"
        client_socket.sendto(controller_input.encode(), (REMOTE_SERVER_IP, REMOTE_SERVER_PORT))
    
