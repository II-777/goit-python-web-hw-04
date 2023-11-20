# Ми реалізували прості `HTTP` та `UDP` сервери. `HTTP`-сервер використовує клас `BaseHTTPRequestHandler`
# із модуля `http.server`. `HTTP`-сервер може обробляти запити `GET` і `POST`
# і використовує бібліотеку `Jinja2` для створення шаблону HTML-сторінки блогу, яку він надсилає браузеру.
#
# Для обробки вхідних запитів `POST` за маршрутом `/contact` `HTTP` сервер надсилає тіло запиту на вказану `IP`
# -адресу `SERVER_IP` та порт `SERVER_PORT` через `UDP` протокол. Застосунок також запускає сервер `UDP`, в окремому
# потоці, він прослуховує вхідні дані з цієї `IP`-адреси на порту `SERVER_PORT` та зберігає отримані дані у файлі `JSON`.
#
# Код класу `HTTPHandler` містить кілька методів обробки вхідних запитів `HTTP`:
#
# - `do_GET`: обробляє запити `GET` і надсилає відповідний вміст `HTML` клієнту на основі запитуваного `URL`-шляху.
# - `send_html`: надсилає вказаний файл HTML клієнту з указаним кодом статусу `HTTP`.
# - `render_template`: рендерить файл HTML за допомогою `Jinja2` і надсилає його клієнту з указаним кодом статусу HTTP.
# - `send_static`: надсилає вказаний статичний файл (в нашому випадку, зображення, `CSS`, `JavaScript`) клієнту.
#
# Крім того, код застосунку також містить такі допоміжні функції:
#
# - `run`: запускає `HTTP`-сервер і прослуховує вхідні запити.
# - `save_data`: аналізує вхідні дані з `UDP`-сокета та зберігає їх у файлі JSON.
# - `run_socket_server`: запускає сервер `UDP` і прослуховує вхідні дані.
#
# Код запускає сервери `HTTP` та `UDP` в окремих потоках.

import json
import logging
import pathlib
import socket
import urllib.parse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import pathlib

from jinja2 import Environment, FileSystemLoader

# Коренева директорія проекту
BASE_DIR = pathlib.Path()
# Завантаження шаблонів Jinja2 з папки 'templates'
env = Environment(loader=FileSystemLoader('templates'))
# IP-адреса та порт для HTTP-сервера
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
# Розмір буфера для UDP-сервера
BUFFER = 1024


def send_data_to_socket(body):
    # Відправлення даних на вказаний IP та порт через UDP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Обробка POST-запитів, відправка даних на вказаний IP та порт через UDP
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
# Перенаправлення користувача на /blog після успішної обробки POST-запиту
        self.send_response(302)
        self.send_header('Location', '/blog')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                # Відправлення головної сторінки
                self.send_html('index.html')
            case "/contact":
                # Відправлення сторінки контактів
                self.send_html('contact.html')
            case "/blog":
                # Відображення шаблону блогу за допомогою Jinja2
                self.render_template('blog.html')
            case _:
                # Надсилання статичного файлу або 404, якщо файл не знайдено
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('404.html', 404)

    def send_html(self, filename, status_code=200):
        # Відправлення HTML-файлу з вказаним кодом статусу
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

# Метод `render_template` використовує механізм шаблонів `Jinja2` для рендерингу HTML-шаблону з
# файлу `templates/blog.html`. Він починається з
# надсилання заголовка відповіді з указаним кодом статусу та типом вмісту, встановленим як `"text/html"`. Потім він
# відкриває файл під назвою `"blog.json"` і завантажує вміст за допомогою бібліотеки `json`. Потім метод використовує
# об’єкт `env = Environment(loader=FileSystemLoader('templates'))` `Jinja2`, щоб отримати шаблон із вказаною назвою файлу
# та показати його з даними з `"blog.json"`. Потім відтворений HTML кодується у вигляді байтів і надсилається клієнту як
# тіло відповіді.

    def render_template(self, filename, status_code=200):
        # Рендеринг шаблону за допомогою Jinja2 та відправлення його клієнту
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open('blog.json', 'r', encoding='utf-8') as fd:
            r = json.load(fd)
        template = env.get_template(filename)
        print(template)
        html = template.render(blogs=r)
        self.wfile.write(html.encode())

# Цей код є частиною обробника запитів HTTP класу `HTTPHandler`, який обслуговує відправку статичних файлів для браузеру.
#
# 1. Надсилає код статусу відповіді HTTP 200, щоб вказати, що запит виконано успішно `self.send_response(200)`.
# 2. Визначає тип MIME файлу за допомогою модуля `mimetypes` і додає заголовок `Content-Type` до відповіді з відповідним
#    типом `MIME`. Якщо тип `MIME` не вдається визначити, за замовчуванням він має значення `"text/plain"`.
# 3. Завершує заголовки відповідей `self.end_headers()`.
# 4. Відкриває файл із вказаним іменем у бінарному режимі `with open(filename, 'rb') as f:`.
# 5. Записує вміст файлу в тіло відповіді `self.wfile.write(f.read())`.

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


def save_data(data):
    # Зберігання даних у файл JSON
    body = urllib.parse.unquote_plus(data.decode())
    try:
        payload = {key: value for key, value in [
            el.split('=') for el in body.split('&')]}
        with open(BASE_DIR.joinpath('data/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(payload, fd, ensure_ascii=False)
    except ValueError as err:
        logging.error(f"Failed to parse data {body} with error {err}")
    except OSError as err:
        logging.error(f"Failed to write data {body} with error {err}")


# Функція `run_socket_server` це дуже проста реалізація сокет-сервера, який використовує протокол `UDP`. Сервер
# прослуховує вхідні повідомлення на заданій `IP`-адресі та порту `(ip, port)`, отримує вхідні дані, а потім викликає
# функцію `save_data` з отриманими даними як аргументом. Сервер продовжуватиме прослуховувати вхідні дані, доки не буде
# викликано переривання клавіатури (наприклад, користувач натискає `CTRL + C`), у цьому випадку він зареєструє
# повідомлення 'Socket server stopped' та закриє сокет. Константа `BUFFER` це розмір буфера, що визначає максимальний
# обсяг даних, який можна отримати за один виклик метод `recvfrom`.

def run_socket_server(ip, port):
    # Запуск UDP-сервера
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            # Прослуховування вхідних даних та виклик функції збереження
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        # Закриття UDP-сокета при завершенні роботи
        server_socket.close()


if __name__ == '__main__':
    # Налаштування рівня логування та шляху до файлу JSON для зберігання даних
    logging.basicConfig(level=logging.INFO,
                        format="%(threadName)s %(message)s")
    STORAGE_DIR = pathlib.Path().joinpath('data')
    FILE_STORAGE = STORAGE_DIR / 'data.json'
# Якщо файл зберігання даних не існує, створити його з порожнім об'єктом JSON
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False)

# Запуск HTTP-сервера та UDP-сервера в окремих потоках
    thread_server = Thread(target=run)
    thread_server.start()
    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()
