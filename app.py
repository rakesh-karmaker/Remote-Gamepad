from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Thread, Event
import vgamepad as vg
from time import sleep
from inputs import get_gamepad
import os
import uuid
import socketio as socketio_client
from controller.gamepad import apply_payload_to_gamepad
from controller.state import current_axis_values

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

# Log startup configuration
print(f"[startup] SERVER_ID={SERVER_ID}")
print(f"[startup] PEER_URL={PEER_URL}")

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
            continue

        # Process each event
        for event in events:
            payload = {
                'type': event.ev_type, # 'Key' or 'Absolute'
                'code': event.code, # e.g. 'BTN_SOUTH', 'ABS_X'
                'state': event.state, # e.g. 1 (pressed), 0 (released), or axis value
                'origin': SERVER_ID, # Identify source server
            }
            
            # Broadcast raw event to all clients from server context
            socketio.emit('gamepad_event', payload)

            # Forward to peer server, if configured and connected
            if PEER_URL and _peer_client.connected:
                try:
                    _peer_client.emit('gamepad_event', payload)
                except Exception as e:
                    socketio.emit('peer_error', {'message': str(e)})

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
    try:
        origin = payload.get('origin')
        if origin == SERVER_ID:
            return  # Ignore our own events
        
        # Rebroadcast to local browser clients
        # socketio.emit('gamepad_event', payload)
        # print(f"Peer Event: {payload}")
        # Apply to local virtual gamepad
        apply_payload_to_gamepad(_gamepad, payload, current_axis_values)
    except Exception as e:
        socketio.emit('gamepad_error', {'message': str(e)})


if __name__ == '__main__':
    try:
        # Optionally connect to peer before starting server
        if PEER_URL and not _peer_client.connected:
            try:
                _peer_client.connect(PEER_URL)
                _peer_client.emit('server_hello', {'server_id': SERVER_ID})
            except Exception as e:
                print(f"Peer connect failed at startup: {e}")
        ## Bind to LAN so other machines can reach this server
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', '5000'))
        print(f"[startup] binding host={host} port={port}")
        # Disable reloader to avoid duplicate initialization/gamepad instances
        socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
    finally:
        _stop_event.set()
