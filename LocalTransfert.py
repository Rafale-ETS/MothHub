import http.server
import socketserver
import os

PORT = 8000
FILENAME = '.\modules\data1.json'  # Name of the file to be sent

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            with open(FILENAME, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(f.read())
                
            # Delete the file after sending
            os.remove(FILENAME)
            print(f"{FILENAME} deleted after sending")
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found')

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()