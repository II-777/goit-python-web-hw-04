from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import json
import logging
import mimetypes
import socket
import urllib.parse
import pathlib

BASE_DIR = pathlib.Path('application')
DATA_DIR = BASE_DIR.joinpath('data')
DATA_FILE = DATA_DIR.joinpath('data.json')

HTTP_SERVER_IP = '0.0.0.0'
HTTP_PORT = 3000

UDP_SERVER_IP = '127.0.0.1'
UDP_SERVER_PORT = 5000


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (UDP_SERVER_IP, UDP_SERVER_PORT
                                ))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)

        self.send_response(302)
        self.send_header('Location', 'message.html')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)

        match route.path:
            case '/':
                self.send_html(BASE_DIR / 'static/html/index.html')
            case '/message.html':
                self.send_html(BASE_DIR / 'static/html/message.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html(BASE_DIR / 'static/html/error404.html', 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename):
        self.send_response(200)

        mt, *rest = mimetypes.guess_type(filename)[0]
        if not mt:
            mt = 'text/plain'

        self.send_header('Content-Type', mt)
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = (HTTP_SERVER_IP, HTTP_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())

    try:
        payload = {str(datetime.now()): {k: v.strip()
                                         for k, v in [el.split('=') for el in body.split('&')]}}

        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as fd:
                existing_data = json.load(fd)
                existing_data.update(payload)
                payload = existing_data
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        finally:
            with open(DATA_FILE, 'w', encoding='utf-8') as fd:
                json.dump(payload, fd, indent=2)

    except ValueError as err:
        logging.error(f'Failed to parse data {body} with error: {err}')
    except OSError as err:
        logging.error(f'Failed to write data {body} with error: {err}')


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)

    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(threadName)s %(message)s')

    with open(DATA_FILE, 'w', encoding='utf-8') as fd:
        json.dump({}, fd)

    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(UDP_SERVER_IP, UDP_SERVER_PORT
                                                    ))

thread_socket.start()
