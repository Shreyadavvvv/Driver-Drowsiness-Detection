import cv2
import numpy as np
import tensorflow as tf
import time

# ── Config ──────────────────────────────────────────────
MODEL_PATH     = 'student_float16.tflite'
IMG_SIZE       = (224, 224)
DROWSY_FRAMES  = 20   # consecutive drowsy frames before alerting
# ────────────────────────────────────────────────────────

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def predict_frame(face_img):
    """Run TFLite inference on a single face image."""
    img = cv2.resize(face_img, IMG_SIZE)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])

    prob = output[0][0]
    # class indices: 0=Drowsy, 1=Non Drowsy
    # so prob < 0.5 means Drowsy
    return 1 if prob < 0.5 else 0   # 1=Drowsy, 0=Alert

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam")
        return

    print("Running... Press Q to quit")
    print("-" * 30)

    drowsy_counter = 0
    current_signal = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        signal = 0  # default Alert

        if len(faces) > 0:
            # Use largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face_img    = frame[y:y+h, x:x+w]
            signal      = predict_frame(face_img)

            # Draw box
            color = (0, 0, 255) if signal == 1 else (0, 255, 0)
            label = "DROWSY" if signal == 1 else "ALERT"
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        # Consecutive frame smoothing
        if signal == 1:
            drowsy_counter += 1
        else:
            drowsy_counter = max(0, drowsy_counter - 1)

        # Only flip to drowsy after N consecutive frames
        current_signal = 1 if drowsy_counter >= DROWSY_FRAMES else 0

        # ── OUTPUT FOR PERSON 2 ──
        print(current_signal, flush=True)
        # ─────────────────────────

        # HUD
        status     = "DROWSY" if current_signal == 1 else "ALERT"
        hud_color  = (0, 0, 255) if current_signal == 1 else (0, 255, 0)
        cv2.putText(frame, f"Signal: {current_signal} | {status}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, hud_color, 2)
        cv2.putText(frame, f"Faces detected: {len(faces)}",
                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

        cv2.imshow('Drowsiness Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.1)  # ~10fps

    cap.release()
    cv2.destroyAllWindows()
    print("Stopped.")

if __name__ == '__main__':
    main()