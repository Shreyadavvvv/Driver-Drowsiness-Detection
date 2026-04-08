const WebSocket = require("ws");
const http = require("http");

// HTTP server (required for ngrok + path routing)
const server = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("Driver Drowsiness WebSocket Server\n");
});

// WebSocket server on /ws path
const wss = new WebSocket.Server({ server, path: "/ws" });

console.log("🚀 Server starting...");

const clients = {
  esp32: new Set(),
  python: new Set(),
};

wss.on("connection", (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`✅ New connection from ${ip}`);

  // Tag client type after first message
  let clientType = "unknown";

  ws.on("message", (message) => {
    const data = message.toString().trim();
    console.log(`📩 [${clientType}] Received: "${data}"`);

    // Identify client on first message
    if (data === "ESP32_READY") {
      clientType = "esp32";
      clients.esp32.add(ws);
      console.log("🔷 ESP32 registered");
      return;
    }

    // Python sender sends "0" or "1" — forward ONLY to ESP32 clients
    if (data === "0" || data === "1") {
      clientType = "python";
      clients.python.add(ws);

      let forwarded = 0;
      clients.esp32.forEach((esp) => {
        if (esp.readyState === WebSocket.OPEN) {
          esp.send(data);
          forwarded++;
        }
      });
      console.log(`📤 Forwarded "${data}" to ${forwarded} ESP32 client(s)`);
    }
  });

  ws.on("close", () => {
    clients.esp32.delete(ws);
    clients.python.delete(ws);
    console.log(`❌ [${clientType}] Disconnected`);
  });

  ws.on("error", (err) => {
    console.log(`⚠️ [${clientType}] Error: ${err.message}`);
  });
});

// Listen on port 8080
server.listen(8080, () => {
  console.log("✅ HTTP+WS Server on http://localhost:8080");
  console.log("📡 WebSocket path: ws://localhost:8080/ws");
});