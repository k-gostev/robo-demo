# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostName = "localhost"
serverPort = 3000


class MyServer(BaseHTTPRequestHandler):
    # noinspection PyTypeChecker
    def do_GET(self):
        if self.path != '/robot/state':
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes("""{
    "joints": {
        "angle": null,
        "velocity": null,
        "torque": null,
        "temperature": null
    },
    "position": {
        "robotSpace": {
            "XYZRPW": null
        },
        "taskSpace": {
            "XYZRPW": null
        }
    },
    "enabled": false,
    "mastered": false,
    "hasErrors": true,
    "safety": {
        "emergencyStopTP": false,
        "emergencyStopExt": false,
        "safeguardStop": false,
        "dmsEngaged": false
    },
    "mode": 0,
    "state": "",
    "bastionConnection": {
        "status": "",
        "secondsConnected": 0
    },
    "system": {
        "clock": "2023-09-13T20:55:01Z"
    }
}""", "UTF-8"))

    def do_POST(self):
        print(self.path)
        if '/execute' not in self.path:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes("{\"path\":" + self.path))
        print("POST response sent")


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")