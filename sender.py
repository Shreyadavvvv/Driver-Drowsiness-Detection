import cv2
import numpy as np
import tensorflow as tf
import websocket
import time
import sys

# ---------------- CONFIG ----------------
MODEL_PATH = "student_float16.tflite"
IMG_SIZE = (224, 224)
DROWSY_FRAMES = 20
WS_URL = "ws://localhost:8080/ws"   # matches server path
# ----------------------------------------

def connect_ws(url, retries=5):
    for i in range(retries):
        try:
            ws = websocket.WebSocket()
            ws.connect(url)
            print(f"✅ Connected to WebSocket: {url}")
            return ws
        except Exception as e:
            print(f"⚠️ WS connect failed ({i+1}/{retries}): {e}")
            time.sleep(2)
    print("❌ Could not connect to WebSocket server. Is server.js running?")
    sys.exit(1)

ws = connect_ws(WS_URL)

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("✅ Model loaded")

# Face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def predict_frame(face_img):
    img = cv2.resize(face_img, IMG_SIZE)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])

    prob = output[0][0]
    label = "DROWSY" if prob < 0.5 else "ALERT"
    print(f"  Model output: {prob:.3f} → {label}")
    return 1 if prob < 0.5 else 0

def send_signal(signal):
    global ws
    try:
        ws.send(str(signal))
        print(f"📤 Sent: {signal}")
    except Exception as e:
        print(f"⚠️ Send failed: {e} — reconnecting...")
        ws = connect_ws(WS_URL)

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        sys.exit(1)

    drowsy_counter = 0
    last_signal = -1   # track state changes

    print("🎥 Camera started. Press Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        signal = 0

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            face_img = frame[y:y+h, x:x+w]
            signal = predict_frame(face_img)

            color = (0, 0, 255) if signal else (0, 255, 0)
            label = "DROWSY" if signal else "ALERT"
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        else:
            cv2.putText(frame, "No Face", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)

        # Smoothing counter
        if signal == 1:
            drowsy_counter = min(drowsy_counter + 1, DROWSY_FRAMES + 5)
        else:
            drowsy_counter = max(0, drowsy_counter - 1)

        current_signal = 1 if drowsy_counter >= DROWSY_FRAMES else 0

        # ✅ Send only on state change (reduces noise)
        if current_signal != last_signal:
            send_signal(current_signal)
            last_signal = current_signal

        # UI overlay
        status = "🔴 DROWSY" if current_signal else "🟢 ALERT"
        color = (0, 0, 255) if current_signal else (0, 255, 0)
        cv2.putText(frame, status, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        cv2.putText(frame, f"Counter: {drowsy_counter}/{DROWSY_FRAMES}", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Driver Drowsiness Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.05)   # ~20fps

    send_signal(0)   # safety: turn off buzzer on exit
    cap.release()
    cv2.destroyAllWindows()
    ws.close()

if __name__ == "__main__":
    main()