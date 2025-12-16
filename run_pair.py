import os
import sys
import subprocess
import time
import argparse


def start_process(cmd: list[str], env: dict[str, str], cwd: str, new_console: bool = True) -> subprocess.Popen:
    creationflags = subprocess.CREATE_NEW_CONSOLE if new_console and os.name == 'nt' else 0
    return subprocess.Popen(cmd, env=env, cwd=cwd, creationflags=creationflags)


def main():
    parser = argparse.ArgumentParser(description="Start server and client with env vars")
    parser.add_argument("--local-server-ip", default="192.168.0.102", help="Server bind IP for local server.py")
    parser.add_argument("--remote-server-ip", default="192.168.0.101", help="Server IP that client.py will send to")
    parser.add_argument("--local-port", default="5000", help="Port for local server.py")
    parser.add_argument("--remote-port", default="5000", help="Port for remote client.py to send to")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Set up environment variables for server
    server_env = os.environ.copy()
    server_env.update({
        "SERVER_IP": args.local_server_ip,
        "SERVER_PORT": args.local_port,
    })

    # Set up environment variables for client
    client_env = os.environ.copy()
    client_env.update({
        "REMOTE_SERVER_IP": args.remote_server_ip,
        "REMOTE_SERVER_PORT": args.remote_port,
    })

    # Commands use the same Python interpreter
    py = sys.executable
    server_cmd = [py, "server.py"]
    client_cmd = [py, "client.py"]

    server_proc = start_process(server_cmd, server_env, cwd=base_dir)
    time.sleep(0.5) # Give server time to start

    client_proc = start_process(client_cmd, client_env, cwd=base_dir)

    try:
        # Keep parent alive and let child consoles run
        while True:
            time.sleep(1)
            # Optionally, check if either died
            if server_proc.poll() is not None:
                print("Server process exited.")
                break
            if client_proc.poll() is not None:
                print("Client process exited.")
                break
    except KeyboardInterrupt:
        print("Stopping processes...")
    finally:
        for p in (server_proc, client_proc):
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        time.sleep(1)
        for p in (server_proc, client_proc):
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass


if __name__ == "__main__":
    main()
