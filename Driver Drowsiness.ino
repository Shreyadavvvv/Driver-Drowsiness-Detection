#include <WiFi.h>
#include <WebSocketsClient.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";

WebSocketsClient webSocket;
#define BUZZER 13
bool buzzerState = false;

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.println("[WS] Connected");
      webSocket.sendTXT("ESP32_READY");
      break;

    case WStype_DISCONNECTED:
      Serial.println("[WS] Disconnected");
      break;

    case WStype_TEXT: {
      String msg = String((char*)payload);
      Serial.println("[WS] Got: " + msg);
      if (msg == "1" && !buzzerState) {
        tone(BUZZER, 1000, 500);
        buzzerState = true;
        Serial.println("BUZZER ON");
      } else if (msg == "0" && buzzerState) {
        noTone(BUZZER);
        buzzerState = false;
        Serial.println("BUZZER OFF");
      }
      break;
    }
    default: break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  pinMode(BUZZER, OUTPUT);
  noTone(BUZZER);

  // ✅ No channel number — plain Wokwi-GUEST connection
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");

  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) {
    delay(500);
    Serial.print(".");
    tries++;
  }

  if (WiFi.status() != WL_CONNECTED) {
    // ✅ Don't restart — just print and hang so you can see the error
    Serial.println("\nWiFi failed. Check SSID.");
    while(true) { delay(1000); }
  }

  Serial.println("\nWiFi OK: " + WiFi.localIP().toString());

  // ✅ Plain ws:// not SSL — Wokwi VS Code talks to your localhost directly
  webSocket.begin("192.168.1.102", 8080, "/ws");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(3000);
  webSocket.enableHeartbeat(15000, 3000, 2);

  Serial.println("Connecting to WebSocket...");
}

void loop() {
  webSocket.loop();
}