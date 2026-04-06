const WebSocket = require("ws");

const wss = new WebSocket.Server({ port: 8080 });

console.log("Server running on ws://localhost:8080");

wss.on("connection", function connection(ws) {
  console.log("Client connected");

  ws.on("message", function message(data) {
    console.log("Received:", data.toString());
  });
});