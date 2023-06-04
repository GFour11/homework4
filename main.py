from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
from datetime import datetime
import json
from threading import Thread
import logging

HOST = "127.0.0.1"
PORT = 5000
DATA = None

with open('storage/data.json', 'r') as file:
    DATA = json.load(file)


def send_to_socket(mess):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(mess, (HOST,PORT))
    client.close()


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        send_to_socket(data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

def run_server(ip, port):
    global DATA
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            sock.sendto(data, address)
            data = urllib.parse.unquote_plus(data.decode())
            data_dict = {key: value for key, value in [el.split('=') for el in data.split('&')]}
            date = datetime.now()
            DATA.update({str(date):data_dict})
            with open('storage/data.json', 'w') as fj:
                json.dump(DATA, fj)
    except KeyboardInterrupt:
        logging.info(f'Destroy server')
    finally:
        sock.close()




def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('127.0.0.1', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()




if __name__ == '__main__':
    logging = logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')
    th = Thread(target=run)
    th.start()
    the = Thread(target=run_server, args=(HOST, PORT, ))
    the.start()

