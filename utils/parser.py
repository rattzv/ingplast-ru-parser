import os
import time

from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from models.product import Product
from utils.csv_exporter import extract_exists_from_csv, write_to_csv
from utils.utils import is_first_run, print_template, random_sleep, update_progress


report_filename = "products-ingplast-ru.csv"


def parse_sitemap_xml(sitemap_content: bytes) -> []:
    root = ET.fromstring(sitemap_content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    links = [element.text for element in root.findall('ns:url/ns:loc', namespace)
             if 'https://ingplast.ru/element' in element.text]

    return links


def parse_characteristics_selenium(link, product, options):
    root_folder = os.environ.get('PROJECT_ROOT')
    chrome_driver_path = os.path.join(root_folder, "chromedriver.exe")

    all_characteristics = []
    characteristics = {}

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    service = Service(chrome_driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(link)

    for option in options:
        driver.execute_script(f"var c = document.getElementsByTagName('select')[0].value = '{option.get('value')}';")
        driver.execute_script("this.ChangeSelect(document.querySelectorAll('.select_property')[0])")

        time.sleep(0.2)

        price_element = driver.find_element(By.CLASS_NAME, "goods_price_val").find_element(By.CLASS_NAME,
                                                                                           "goods_price_val_inf")
        span_price = price_element.find_element(By.CLASS_NAME, 'in_price')
        if span_price:
            characteristics = {"price": span_price.text.strip()}
            if price_element.find_elements(By.CLASS_NAME, 'mash01'):
                unit = price_element.find_element(By.CLASS_NAME, 'mash01')
                characteristics["unit"] = unit.text.strip().replace('/ ', '')

        if driver.find_elements(By.CLASS_NAME, 'har_mob'):
            html_characteristics = driver.find_elements(By.CLASS_NAME, 'har_mob div')

            characteristics.update(
                {html_characteristics[i].text.strip(): html_characteristics[i + 1].text.strip()
                 for i in range(0, len(html_characteristics), 2)}
            )

        change_property_elements = driver.find_elements(By.CLASS_NAME, 'change_property')
        for element in change_property_elements:
            if element.is_displayed():
                characteristics[element.text.strip().split('\n')[0].rstrip(":")] = element.text.strip().split('\n')[1]

        full_characteristics = {**vars(product), **characteristics}
        all_characteristics.append(full_characteristics)

    return all_characteristics


def start_site_parsing(links):
    success_count = 0
    failure_count = 0
    skipped_count = 0

    all_characteristics = []

    first_run_status = is_first_run(report_filename)
    exists_urls = []
    if not first_run_status:
        rows = extract_exists_from_csv(report_filename)
        if len(rows) > 0 and 'url' in rows[0]:
            headers = rows[0]
            for row in rows[1:]:
                exists_urls.append(row[4])
                restore_row = dict(zip(headers, row))
                all_characteristics.append(restore_row)
    for iteration, link in enumerate(links):
        try:
            product = Product()
            product.url = link

            update_progress(iteration, len(links), product.url)

            if product.url in exists_urls:
                skipped_count += 1
                print(print_template("Link has been checked before, skip ({})".format(product.url)))
                continue

            response = requests.get(product.url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            if soup.find('div', 'bx_breadcrumbs') is None or soup.find('div', 'bx_item_detail') is None:
                failure_count += 1
                print(print_template("Error loading html page, key elements not found ({}).".format(product.url)))
                random_sleep(10)
                continue

            product_card = soup.find('div', 'bx_item_detail')

            if product_card.find('div', 'h1_cart_2'):
                product.name = product_card.find('div', 'h1_cart_2').text.strip()
            elif product_card.find('h1', 'h1_cart'):
                product.name = product_card.find('h1', 'h1_cart').text.strip()
            else:
                failure_count += 1
                print(print_template("Error find H1, key elements not found ({}).".format(product.url)))
                continue

            categories_elements = soup.find('div', 'br_catalog bk').find_all('div',
                                                                             attrs={'itemprop': 'itemListElement'})
            product.categories = ', '.join(
                [li_item.find('a').find('span').text.strip() for li_item in categories_elements])

            select_elements = product_card.find('div', 'change_property')

            if select_elements and len(select_elements.find_all("option")) > 1:
                options = select_elements.find_all("option")
                new_all_characteristics = parse_characteristics_selenium(link, product, options)
                all_characteristics.extend(new_all_characteristics)
            else:
                if product_card.find('div', 'goods_price_val'):
                    product.price = \
                        product_card.find('div', 'goods_price_val').find('div', 'goods_price_val_inf').find('meta',
                                                                                                            attrs={
                                                                                                                'itemprop': 'price'})[
                            'content']
                    unit = product_card.find('div', 'goods_price_val').find('div', 'goods_price_val_inf').find(
                        'span', 'mash01')
                    if unit:
                        product.unit = unit.text.strip().replace('/ ', '')

                    characteristics = {}

                    if soup.find('div', 'har_mob'):
                        html_characteristics = soup.find('div', 'har_mob').find_all('div')
                        for i in range(0, len(html_characteristics), 2):
                            characteristics[html_characteristics[i].text.strip()] = html_characteristics[
                                i + 1].text.strip()

                    characteristics = {**vars(product), **characteristics}
                    all_characteristics.append(characteristics)

            write_to_csv(all_characteristics, report_filename)
            success_count += 1
        except Exception as e:
            failure_count += 1
            print(print_template("Unhandled exception: {}".format(e)))
            random_sleep(10)

    return success_count, failure_count, skipped_count
