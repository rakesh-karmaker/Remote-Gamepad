from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Thread, Event
import vgamepad as vg
from time import sleep
from inputs import get_gamepad
import os
import uuid
import socketio as socketio_client

# Optional: load variables from a .env file if present.
# Supports selecting a specific file via ENV_FILE.
try:
    from dotenv import load_dotenv  # type: ignore
    ENV_FILE = os.environ.get('ENV_FILE')
    if ENV_FILE:
        load_dotenv(dotenv_path=ENV_FILE, override=True)
    else:
        load_dotenv()
except Exception:
    pass

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Background poller control
_poller_thread: Thread | None = None
_stop_event = Event()
_gamepad = vg.VX360Gamepad()

# Peer server configuration & client
PEER_URL = os.environ.get('PEER_URL')  # e.g. http://127.0.0.1:5001
SERVER_ID = os.environ.get('SERVER_ID') or str(uuid.uuid4())
_peer_client = socketio_client.Client(reconnection=True, reconnection_attempts=0)

print(f"[startup] SERVER_ID={SERVER_ID}")
print(f"[startup] PEER_URL={PEER_URL}")

current_axis_values = {
    0: 0.0,  # Left joystick X
    1: 0.0,  # Left joystick Y
    2: 0.0,  # Right joystick X
    3: 0.0,  # Right joystick Y
}

@app.route('/')
def index():
    return render_template('index.html')

def _poll_gamepad_loop():
    while not _stop_event.is_set():
        try:
            events = get_gamepad()
        except Exception as e:
            # Emit an error event to clients and back off briefly
            socketio.emit('gamepad_error', {'message': str(e)})
            sleep(0.05)
            continue

        for event in events:
            payload = {
                'type': event.ev_type,
                'code': event.code,
                'state': event.state,
                'origin': SERVER_ID,
            }
            # Broadcast raw event to all clients
            socketio.emit('gamepad_event', payload)
            print(f"Event: {payload}")

            # Apply locally to virtual gamepad
            # match event.ev_type:
            #     case "Key":
            #         handle_button(_gamepad, event.code, event.state == 1)
            #     case "Absolute":
            #         if event.code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY", "ABS_Z", "ABS_RZ"]:
            #             axis_map = {
            #                 "ABS_X": 0,
            #                 "ABS_Y": 1,
            #                 "ABS_RX": 2,
            #                 "ABS_RY": 3,
            #                 "ABS_Z": 4,
            #                 "ABS_RZ": 5,
            #             }
            #             axis = axis_map[event.code]
            #             # Normalize
            #             if event.code in ["ABS_Z", "ABS_RZ"]:
            #                 value = (event.state / 255.0) * 2 - 1
            #             else:
            #                 value = event.state / 32767.0
            #             handle_axis(_gamepad, axis, value, current_axis_values)
            #         elif event.code == "ABS_HAT0X":
            #             hat_value = (event.state, 0)
            #             handle_hat(_gamepad, hat_value)
            #         elif event.code == "ABS_HAT0Y":
            #             hat_value = (0, event.state * -1)
            #             handle_hat(_gamepad, hat_value)

            # Forward to peer server, if configured and connected
            print(f"Peer connected: {_peer_client.connected} {PEER_URL}")
            if PEER_URL and _peer_client.connected:
                try:
                    _peer_client.emit('gamepad_event', payload)
                except Exception as e:
                    socketio.emit('peer_error', {'message': str(e)})

        # Small sleep to prevent tight loop hogging CPU
        # sleep(0.001)

@socketio.on('connect')
def on_connect():
    global _poller_thread
    # Start poller once when first client connects
    if _poller_thread is None or not _poller_thread.is_alive():
        _stop_event.clear()
        _poller_thread = Thread(target=_poll_gamepad_loop, daemon=True)
        _poller_thread.start()
    # Connect to peer server if configured
    if PEER_URL and not _peer_client.connected:
        try:
            _peer_client.connect(PEER_URL)
            # Identify this server to peer (optional)
            _peer_client.emit('server_hello', {'server_id': SERVER_ID})
        except Exception as e:
            socketio.emit('peer_error', {'message': f'Peer connect failed: {e}'})

@socketio.on('disconnect')
def on_disconnect():
    # Do not stop on each disconnect; poller runs globally.
    # If you want to stop when no clients remain, track client count.
    pass

@socketio.on('gamepad_event')
def handle_gamepad_event_from_peer(payload):
    """Receive events from any client (including peer server client) and
    apply locally without re-forwarding to avoid echo loops."""
    try:
        origin = payload.get('origin')
        if origin == SERVER_ID:
            return  # Ignore our own events
        # Rebroadcast to local browser clients
        socketio.emit('gamepad_event', payload)
        print(f"Peer Event: {payload}")
        # Apply to local virtual gamepad
        # _apply_payload_to_gamepad(payload)
    except Exception as e:
        socketio.emit('gamepad_error', {'message': str(e)})

# def _apply_payload_to_gamepad(payload: dict):
#     ev_type = payload.get('type')
#     code = payload.get('code')
#     state = payload.get('state')
#     if ev_type == 'Key':
#         handle_button(_gamepad, code, state == 1)
#     elif ev_type == 'Absolute':
#         if code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY", "ABS_Z", "ABS_RZ"]:
#             axis_map = {
#                 "ABS_X": 0,
#                 "ABS_Y": 1,
#                 "ABS_RX": 2,
#                 "ABS_RY": 3,
#                 "ABS_Z": 4,
#                 "ABS_RZ": 5,
#             }
#             axis = axis_map[code]
#             if code in ["ABS_Z", "ABS_RZ"]:
#                 value = (state / 255.0) * 2 - 1
#             else:
#                 value = state / 32767.0
#             handle_axis(_gamepad, axis, value, current_axis_values)
#         elif code == "ABS_HAT0X":
#             handle_hat(_gamepad, (state, 0))
#         elif code == "ABS_HAT0Y":
#             handle_hat(_gamepad, (0, state * -1))


def handle_button(gamepad, button, pressed):
    vg_button = {
        "BTN_SOUTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "BTN_EAST": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "BTN_WEST": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "BTN_NORTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "BTN_TL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        "BTN_TR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "BTN_START": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        "BTN_SELECT": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        "BTN_THUMBL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
        "BTN_THUMBR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    }.get(button, None)

    if vg_button is not None:
        if pressed:
            gamepad.press_button(vg_button)
        else:
            gamepad.release_button(vg_button)
        gamepad.update()

def handle_axis(gamepad, axis, value, current_axis_values):

    if axis == 0:  # Left joystick X
        gamepad.left_joystick_float(x_value_float=value, y_value_float=current_axis_values[1])
        current_axis_values[0] = value
    elif axis == 1:  # Left joystick Y
        gamepad.left_joystick_float(x_value_float=current_axis_values[0], y_value_float=(value))
        current_axis_values[1] = value
    elif axis == 2:  # Right joystick X
        gamepad.right_joystick_float(x_value_float=value, y_value_float=current_axis_values[3])
        current_axis_values[2] = value
    elif axis == 3:  # Right joystick Y
        gamepad.right_joystick_float(x_value_float=current_axis_values[2], y_value_float=(value))
        current_axis_values[3] = value
    elif axis == 4:  # Left trigger
        trigger_value = int((value + 1) / 2 * 255)  # Scale from -1.0 to 1.0 to 0 to 255
        gamepad.left_trigger(value=trigger_value)
    elif axis == 5:  # Right trigger
        trigger_value = int((value + 1) / 2 * 255)  # Scale from -1.0 to 1.0 to 0 to 255
        gamepad.right_trigger(value=trigger_value)

    gamepad.update()

def handle_hat(gamepad, value):
    x, y = value
    if x == -1:
        gamepad.left_joystick(x_value=-32767, y_value=0)
    if x == 1:
        gamepad.left_joystick(x_value=32767, y_value=0)
    if y == -1:
        gamepad.left_joystick(x_value=0, y_value=-32767)
    if y == 1:
        gamepad.left_joystick(x_value=0, y_value=32767)
    if x == 0 and y == 0:
        gamepad.left_joystick(x_value=0, y_value=0)
    gamepad.update()


if __name__ == '__main__':
    try:
        # Optionally connect to peer before starting server
        if PEER_URL and not _peer_client.connected:
            try:
                _peer_client.connect(PEER_URL)
                _peer_client.emit('server_hello', {'server_id': SERVER_ID})
            except Exception as e:
                print(f"Peer connect failed at startup: {e}")
        socketio.run(app, debug=True)
    finally:
        _stop_event.set()
