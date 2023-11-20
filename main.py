from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import urllib.parse
import mimetypes
import pathlib

# Коренева директорія проекту
BASE_DIR = pathlib.Path()


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                # Відправлення головної сторінки
                self.send_html('static/html/index.html')
            case "/contact":
                # Відправлення сторінки контактів
                self.send_html('static/html/message.html')
            case _:
                # Надсилання статичного файлу або 404, якщо файл не знайдено
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('static/html/error404.html', 404)

    def send_html(self, filename, status_code=200):
        # Відправлення HTML-файлу з вказаним кодом статусу
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        # Відправлення статичного файлу (зображення, CSS, JavaScript)
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    # Запуск HTTP-сервера на адресі 0.0.0.0 та порту 3000
    address = ('0.0.0.0', 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        # Зупинка сервера при натисканні Ctrl+C
        http_server.server_close()


if __name__ == '__main__':
    # Запуск HTTP-сервера в окремому потоці
    thread_server = Thread(target=run)
    thread_server.start()
