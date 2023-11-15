# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import json

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
        self.wfile.write(bytes(self.get_mock_content(), "UTF-8"))

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

        content = {
            'path': self.path
        }

        self.wfile.write(bytes(json.dumps(content), 'UTF-8'))
        print("POST response sent")

    def get_mock_content(self):
        content = {
            'joints': {
                'angle': None,
                'velocity': None,
                'torque': None,
                'temperature': None
            },
            'position': {
                'robotSpace': {
                    'XYZRPW': None
                },
                'taskSpace': {
                    'XYZRPW': None
                }
            },
            'enabled': False,
            'mastered': False,
            'hasErrors': True,
            'safety': {
                'emergencyStopTP': False,
                'emergencyStopExt': False,
                'safeguardStop': False,
                'dmsEngaged': False
            },
            'mode': 0,
            'state': 'STOPPED',
            'bastionConnection': {
                'status': '',
                'secondsConnected': 0
            },
            'system': {
                'clock': datetime.now().isoformat()
            }
        }
        return json.dumps(content)

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")