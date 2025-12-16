<h1>Remote Gamepad</h1>
<p><strong>Remote Gamepad</strong> is a Python project that allows you to send gamepad (controller) input from one
    machine to another over a network using UDP sockets. It uses <code>vgamepad</code> to emulate a virtual Xbox 360
    controller on the server side.</p>

<h2>Features</h2>
<ul>
    <li>Send gamepad input from a client to a remote server</li>
    <li>Emulate a virtual Xbox 360 controller on the server</li>
    <li>Easy configuration using environment variables or <code>.env</code> file</li>
    <li>Cross-platform (Windows recommended for vgamepad)</li>
</ul>

<h2>How to Use</h2>
<ol>
    <li>
        <strong>Install dependencies:</strong><br>
        <pre>pip install -r requirements.txt</pre>
    </li>
    <li>
        <strong>Set up environment variables:</strong><br>
        Create a <code>.env</code> file or set environment variables for server and client IP/port.<br>
        Example <code>.env</code> for server:
        <pre>
SERVER_IP=0.0.0.0
SERVER_PORT=5000
      </pre>
        Example <code>.env</code> for client:
        <pre>
REMOTE_SERVER_IP=192.168.0.101
REMOTE_SERVER_PORT=5000
      </pre>
    </li>
    <li>
        <strong>Start the server:</strong><br>
        <pre>python server.py</pre>
    </li>
    <li>
        <strong>Start the client:</strong><br>
        <pre>python client.py</pre>
    </li>
    <li>
        <strong>Or use the helper script to run both:</strong><br>
        <pre>python run_pair.py --local-server-ip 0.0.0.0 --remote-server-ip 192.168.0.101 --local-port 5000 --remote-port 5000</pre>
    </li>
</ol>

<h2>Project Structure</h2>
<pre>
remote-gamepad/
├── client.py
├── server.py
├── run_pair.py
├── requirements.txt
├── controller/
│   ├── __init__.py
│   ├── gamepad.py
│   └── state.py
└── ...
  </pre>

<h2>Notes</h2>
<ul>
    <li>Requires <code>vgamepad</code> (Windows only) and a compatible virtual gamepad driver.</li>
    <li>Tested with Xbox 360 controller mappings.</li>
    <li>For custom IP/port, use environment variables or pass arguments to <code>run_pair.py</code>.</li>
</ul>

<h2>License</h2>
<p>MIT License</p>