from bs4 import BeautifulSoup as BS
import requests
from requests.adapters import HTTPAdapter, Retry

from PIL import Image
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from tqdm import tqdm
import re

# Создаем сессию для запросов
session = requests.Session()

# Настраиваем параметры повторных попыток в случае неудачи
retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])

# Монтируем адаптеры для HTTP и HTTPS с заданными параметрами повторных попыток
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

def scrap_gif(url_list):
    """
    Основная функция для скрапинга GIF-файлов с заданного списка URL-адресов.
    """
    global GIF_URL_LIST
    GIF_URL_LIST = []

    # Создаем прогресс-бар для отслеживания процесса
    pbar = tqdm(url_list, position=0, leave=True)
    print("Processing URL's")
    for url in pbar:
        pbar.set_description("Processing %s" % url)
        find_gifs(url)

    # Определяем анимированные GIF-файлы из найденных ссылок
    animated_gifs = detect_animated_gifs(GIF_URL_LIST)
    # Сохраняем пути к анимированным GIF-файлам
    save_gifs_path(animated_gifs)

    return 'Scrapping is completed'

def find_gifs(url):
    """
    Находит все GIF-файлы на указанном URL и добавляет их в глобальный список GIF_URL_LIST.
    """
    # Получаем HTML-содержимое страницы
    html = session.get(url).content.decode('utf-8', errors='ignore')

    # Парсим HTML с помощью BeautifulSoup
    soup = BS(html, "html.parser")
    # Ищем все изображения с расширением .gif
    gifs = soup.findAll('img', {'src': re.compile(r'\.gif$',)})

    if len(gifs) > 0:
        for gif in gifs:
            # Пропускаем изображения, если они содержат 'ucoz' или 'narod.yandex' в URL
            if re.search(r'ucoz', gif['src']) is not None or re.search(r'narod\.yandex', gif['src']) is not None:
                continue
            else:
                # Добавляем абсолютные URL к списку GIF_URL_LIST
                if re.match(r'^http', gif['src']):
                    GIF_URL_LIST.append(gif['src'])
                else:
                    # Преобразуем относительные URL в абсолютные
                    GIF_URL_LIST.append(url + gif['src'])

def detect_animated_gifs(gif_links):
    """
    Определяет, какие из найденных GIF-файлов являются анимированными.
    """
    animated_gifs = set()
    
    # Создаем прогресс-бар для отслеживания процесса
    pbar = tqdm(gif_links[:901], position=0, leave=True)
    print('Detecting animated gifs')
    for gif in pbar:
        pbar.set_description("Processing %s" % gif)
        try:
            # Открываем изображение по URL
            img = Image.open(urlopen(gif))
            try:
                # Пытаемся перейти на следующий кадр изображения
                img.seek(1)
            except EOFError:
                # Если не удается перейти, значит это не анимированный GIF
                continue
            else:
                # Если удалось перейти на следующий кадр, добавляем URL к списку анимированных GIF
                animated_gifs.add(gif)
        except (HTTPError, URLError, IOError):
            # Игнорируем ошибки, возникающие при открытии URL
            continue
    
    return animated_gifs

def save_gifs_path(animated_gifs):
    """
    Сохраняет анимированные GIF-файлы в локальную папку /gifs.
    """
    # Создаем прогресс-бар для отслеживания процесса
    pbar = tqdm(enumerate(animated_gifs), position=0, leave=True)
    print('Saving gifs in /gifs folder')
    for i, link in pbar:
        pbar.set_description("Processing %s" % link)
        # Получаем содержимое GIF-файла
        gif_content = session.get(link).content
        # Сохраняем содержимое в файл с именем {i}.gif
        with open(f'gifs/{i}.gif', 'wb') as f:
            f.write(gif_content)
            f.close()