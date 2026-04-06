import websocket
import time
import threading

# ---------------- CONFIG ----------------
SERVER_URL = "ws://localhost:8080"
SEND_INTERVAL = 0.5   # seconds (adjust if needed)
RECONNECT_DELAY = 2   # seconds

# Shared state
current_state = "0"   # default ALERT


# ---------------- WEBSOCKET HANDLER ----------------
class WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.connected = False

    def connect(self):
        while not self.connected:
            try:
                print("Connecting to server...")
                self.ws = websocket.WebSocket()
                self.ws.connect(self.url)
                self.connected = True
                print("✅ Connected to server")
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                time.sleep(RECONNECT_DELAY)

    def send(self, data):
        try:
            if self.connected:
                self.ws.send(data)
        except Exception as e:
            print(f"⚠ Send error: {e}")
            self.connected = False
            self.connect()

    def close(self):
        if self.ws:
            self.ws.close()


# ---------------- DETECTION INTERFACE ----------------
def get_drowsiness_state():
    """
    Replace this function with your CV/CNN logic.
    MUST return:
        "1" → Drowsy
        "0" → Alert
    """

    # 🔴 TEMP (REMOVE AFTER INTEGRATION)
    t = int(time.time())
    return "1" if (t % 6 < 3) else "0"


# ---------------- SENDER LOOP ----------------
def sender_loop(ws_client):
    global current_state

    while True:
        try:
            new_state = get_drowsiness_state()

            # Only send if state changes OR periodically
            if new_state != current_state:
                current_state = new_state
                ws_client.send(current_state)
                print(f"📡 Sent (state change): {current_state}")

            else:
                # periodic heartbeat (important for stability)
                ws_client.send(current_state)

            time.sleep(SEND_INTERVAL)

        except Exception as e:
            print(f"⚠ Loop error: {e}")
            time.sleep(1)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    ws_client = WebSocketClient(SERVER_URL)
    ws_client.connect()

    sender_thread = threading.Thread(target=sender_loop, args=(ws_client,))
    sender_thread.start()