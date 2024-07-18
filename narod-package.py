# 💿 ИМПОРТ НЕОБХОДИМЫХ ЗАВИСИМОСТЕЙ

import requests
from bs4 import BeautifulSoup as Bs  # суп для парсинга html разметки
from urllib.parse import urlparse, urljoin, urlsplit
import concurrent.futures
import ast
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

USER_AGENTS = [
    # Список user-agent строк для случайного выбора
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0"

]


# ⚙️ СПИСОК ИСПОЛЬЗУЕМЫХ ФУНКЦИЙ

# Функция формирования домена
def extract_url(domain):
    """
    Формирует полный URL страницы для указанного домена.

    Args:
        domain (str): Доменное имя без протокола и пути.

    Returns:
        str: Полный URL страницы.
    """
    # Формируем полноценный адрес страницы
    url = f'https://{domain}.narod.ru'

    # Возвращаем сформированный URL страницы
    return url


# Функция для добавления случайной задержки
def random_delay():
    """Выполняет случайную задержку от 1 до 3 секунд."""
    time.sleep(random.uniform(1, 3))


def create_session():
    """Создает сессию с retries и cookies."""
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    return session


def get_internal_links(url):
    """Получает все внутренние ссылки для данного URL.

    Args:
        url (str): URL сайта для сбора внутренних ссылок.

    Returns:
        dict: Словарь с URL и их статусами.
    """
    urls = dict()
    origin_host = urlparse(url).netloc
    get_page_links(url, urls, origin_host)
    del urls[urlsplit(url)._replace(path='/').geturl()]
    return urls


def get_page_links(url, urls, origin_host):
    """Рекурсивно собирает все внутренние ссылки на данной странице.

    Args:
        url (str): URL страницы для анализа.
        urls (dict): Словарь для хранения URL и их статусов.
        origin_host (str): Исходный хост для проверки внутренних ссылок.
    """
    if url in urls:
        return

    try:
        session = create_session()
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = session.get(url, headers=headers, timeout=5)
        random_delay()

        if 'Content-Type' not in response.headers or not response.headers['Content-Type'].startswith('text/html'):
            return

        status = response.status_code
        if status != 200:
            urls[url] = status
            return

        urls[url] = status
        print(f'Parsing URL: {url}')

        html = response.content
        soup = Bs(html, 'html.parser')

        links = set()
        for a in soup.find_all(('a', 'area'), {'href': True}):
            href = a.attrs['href']

            if href.startswith(('javascript:', 'mailto:')) or '#' in href:
                continue

            if urlparse(href).netloc in (origin_host, ''):
                href_link = urljoin(url, href, allow_fragments=False)
                if urlparse(href_link).scheme != 'https':
                    href_link = urlsplit(href_link)._replace(
                        scheme='https').geturl()

                if not is_valid_link(href_link):
                    continue
                else:
                    links.add(href_link)

        for link in links:
            get_page_links(link, urls, origin_host)

    except requests.RequestException as e:
        print(f"Request error for {url}: {e}")
        urls[url] = 'Request error'

    except Exception as e:
        print(f"General error for {url}: {e}")
        urls[url] = 'General error'


def is_valid_link(href_link):
    """Проверяет валидность ссылки.

    Args:
        href_link (str): Ссылка для проверки.

    Returns:
        bool: True, если ссылка валидна, иначе False.
    """
    return not (urlparse(href_link).path in ('/index.html', '/register', '', '/') or
                urlparse(href_link).path.startswith(('/gb', '/panel')))


def scrape_site(url):
    """Получает внутренние ссылки для данного сайта.

    Args:
        url (str): URL сайта.

    Returns:
        dict: Словарь с внутренними ссылками и их статусами или None в случае ошибки.
    """
    try:
        return get_internal_links(url)
    except Exception as e:
        print(f"Error scraping site {url}: {e}")
        return None


def scrape_multiple_sites(input_df, url_column):
    """Запускает многопоточный сбор внутренних ссылок для сайтов из DataFrame.

    Args:
        input_df (pd.DataFrame): DataFrame с URL сайтов.
        url_column (str): Название колонки с URL.

    Returns:
        list: Список словарей с внутренними ссылками и их статусами.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(
            scrape_site, url): url for url in input_df[url_column]}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append(None)
    return results


def extract_domain_from_link(internal_links_dict):
    """Извлекает домен из словаря внутренних ссылок.

    Args:
        internal_links_dict (dict): Словарь внутренних ссылок.

    Returns:
        str: Доменное имя.
    """
    if internal_links_dict:
        domain = urlparse(list(internal_links_dict.keys())[0]).netloc[:-9]
        return domain


# Функция экстракта html из фреймов
def extract_frames_from_html(link, html_pages):
    """
    Извлекает HTML содержимое фреймов (frame и iframe) из основной страницы и добавляет их в html_pages.

    Args:
        link (str): URL страницы.
        html_pages (dict): Словарь, содержащий HTML основного документа.

    Returns:
        dict: Обновленный словарь с HTML содержимым страницы и ее фреймов.
    """
    # Формируем soup-объект для парсинга HTML-дерева страницы сайта
    try:
        for path in list(html_pages.keys()):
            soup = Bs(html_pages[path], 'html.parser')

            # Обработка элементов frame и iframe с атрибутом src
            frames_list = soup.find_all(['frame', 'iframe'], {'src': True})
            for frame in frames_list:
                frame_source = frame.attrs['src']
                frame_url = urljoin(link, frame_source)
                response = requests.get(frame_url)

                if response.status_code == 200:
                    frame_html = response.content.decode(
                        'utf-8', errors='ignore')
                    html_pages[f'{path}_{frame.name}_{
                        frame_source}'] = frame_html
                else:
                    html_pages[f'{path}_{frame.name}_{
                        frame_source}'] = response.status_code

            # Обработка элементов iframe с атрибутом srcdoc
            iframes_list = soup.find_all('iframe', {'srcdoc': True})
            for iframe in iframes_list:
                frame_html = iframe.attrs['srcdoc']
                html_pages[f'{path}_{iframe.name}_srcdoc'] = frame_html

        # Возвращаем словарь с HTML-структурой страницы и фреймов
        return html_pages

    except requests.RequestException as e:
        print(f"Request error for frame link:{link}: {e}")

    except Exception as e:
        print(f"General error for frame {link}: {e}")


def extract_html(links_dict):
    """
    Извлекает HTML содержимое страницы и ее фреймов (если имеются).

    Args:
        links_dict (dict): Словарь ссылок страницы.

    Returns:
        dict or int: Словарь с HTML содержимым страницы и фреймов, или код ошибки HTTP.
    """
    # Создаем сессию и задаем в заголовке запроса User-Agent для маскировки под браузер
    try:
        session = create_session()
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        # Создаем словарь для хранения HTML-документов страниц с содержанием домена страницы для дальнейшего мерджа данных с целевым датасетом
        html_pages = {'domain': extract_domain_from_link(links_dict)}

        # Делаем GET-запрос на получение данных страницы
        for link, status in list(links_dict.items()):
            if status == 200:
                response = session.get(
                    link, headers=headers, allow_redirects=False)
                random_delay()

                # Возвращаем контент страницы в кодировке UTF-8
                html = response.content.decode('utf-8', errors='ignore')
                link_path = urlparse(link).path
                html_pages[link_path] = html

        return extract_frames_from_html(link, html_pages)

    except requests.RequestException as e:
        print(f"Request error for {link}: {e}")

    except Exception as e:
        print(f"General error for {link}: {e}")


def delete_ucoz(html_dict):
    """
    Очищает HTML-структуры страницы от рекламы Ucoz.

    Args:
        html (str): Строка со структурой словаря htmlPages, содержащая информацию обо всех HTML-структурах страницы.

    Returns:
        dict or str: Словарь с очищенными HTML-структурами или исходная строка в случае HTTP-кода ошибки.
    """
    # Если длина строки > 3, т.е. значение не является HTTP-кодом ошибки, который состоит из 3 символов
    if len(html_dict) > 3:
        # Объявляем переменную - пустой словарь, в который будут складываться очищенные от рекламы Ucoz HTML-структуры страницы
        clean_dict = {}

        # Конвертируем строку со структурой словаря htmlPages в словарь с помощью библиотеки ast
        # html_to_dict = ast.literal_eval(html)

        # Для каждого ключа и его значения в словаре
        for k, v in html_dict.items():
            # Добавляем в словарь clean_dict результат функции delete_ucoz_html, которая очищает изначальный HTML-документ от рекламы Ucoz,
            # и присваиваем ему изначальный ключ
            clean_dict[k] = delete_ucoz_html(v)

        # Возвращаем словарь с HTML-содержимым страницы и ее фреймами (при наличии), очищенными от рекламы Ucoz
        return clean_dict
    else:
        # Иначе возвращаем входную переменную
        return html_dict


def delete_ucoz_html(html):
    """
    Очищает HTML от рекламных блоков Ucoz.

    Args:
        html (str or int): HTML-документ страницы/фрейма страницы или код HTTP ошибки.

    Returns:
        str or int: Очищенный HTML-документ или исходный код HTTP ошибки.
    """
    # Если переменная html - число, т.е. содержит код HTTP ошибки, возникшей при попытке запроса к странице
    if isinstance(html, int):
        # Возвращаем саму входную переменную html
        return html
    else:
        # Используем BeautifulSoup для парсинга HTML, чтобы выявить рекламные блоки
        soup = Bs(html, "html.parser")

        # Находим все тэги <script> в тэге <head>
        try:
            head_scripts = soup.head.find_all('script')
            if head_scripts:
                [tag.decompose() for tag in head_scripts]
        except AttributeError:
            # Если уже была произведена очистка, то просто не выполняем действия выше
            pass

        # Находим ссылку, которая используется в элементе Copyright (располагается внизу разметки)
        ucoz_copyright = soup.find("a", {"href": "https://www.ucoz.ru/"})

        # Если найдена строка copyright
        if ucoz_copyright:
            # Удаляем строку
            ucoz_copyright.parent.decompose()

        # Очищенный объект BeautifulSoup переводим в строку, удаляя все пробелы слева и справа
        # (whitespace образуются в результате удаления рекламных строк)
        no_ucoz_page = str(soup).strip()

        # Возвращаем результат
        return no_ucoz_page


def extract_text(html):
    """
    Извлекает текстовое содержимое HTML-документа.

    Args:
        html (dict or str): Значение колонки html из DataFrame, которое может быть словарем или строкой.

    Returns:
        dict or str: Словарь с текстовым содержимым HTML-документа или исходное значение, если входное значение не является словарем.
    """
    # Если значение имеет тип dict (словарь)
    if isinstance(html, dict):
        # Создаем пустой словарь для хранения текстового содержимого каждой HTML-структуры страницы
        text_dict = {}

        # Для каждого ключа и значения (HTML-документа) в словаре html
        for k, v in html.items():
            # Извлекаем текст с удалением пробелов с начала и конца строки
            # добавляем полученную строку с текстом HTML-документа в словарь text_dict
            text_dict[k + '_text'] = Bs(v, 'html.parser').get_text().strip()

        # Возвращаем словарь с текстовым содержимым для каждого HTML-документа страницы и ее фреймов (при наличии)
        return text_dict
    else:
        # Если значение не является словарем, возвращаем входную переменную без изменений
        return html


def scrape_site_html(url):
    """Получает HTML-документы для данного сайта.

    Args:
        url (str): URL сайта.

    Returns:
        dict: Словарь с html-документами и их статусами или None в случае ошибки.
    """
    try:
        return extract_html(url)
    except Exception as e:
        print(f"Error scraping site html {url}: {e}")
        return None


def scrape_multiple_sites_html(input_df, url_column):
    """Запускает многопоточный сбор html-документов для сайтов из DataFrame.

    Args:
        input_df (pd.DataFrame): DataFrame с URL сайтов.
        url_column (str): Название колонки с URL.

    Returns:
        list: Список словарей с html-документами и их статусами.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(
            scrape_site_html, url): url for url in input_df[url_column]}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append(None)
    return results


def delete_domain(input_dict):
    """Удаляет домен из входящего словаря 

    Args:
        input_dict (dict): Входящий словарь

    Returns:
        input_dict (dict): Словарь с удаленным объектом, имеющем ключ 'domain'
    """
    if isinstance(input_dict, dict):
        input_dict.__delitem__('domain')
    return input_dict


def convert_string_to_dict(string_dict):
    if isinstance(string_dict, str):
        string_dict = ast.literal_eval(string_dict)
    return string_dict


def extract_domain_from_dict(input_dict):
    return input_dict['domain']


def main():
    urls = get_internal_links('https://missterr.narod.ru/')
    for k, v in urls.items():
        print(k, v)


if __name__ == "__main__":
    main()
