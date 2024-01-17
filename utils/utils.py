import os
import sys
import random
import time
import requests

from typing import Union
from datetime import datetime


def print_template(message) -> str:
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"\r{current_date}: {message}"
    return message


def update_progress(processed_lines, total_lines, current_line):
    progress = int((processed_lines / total_lines) * 100)
    sys.stdout.write(print_template(f"Progress: {progress}% ({processed_lines}/{total_lines}), current element: {current_line})"))
    sys.stdout.flush()


def check_reports_folder_exist() -> Union[str, bool]:
    try:
        root_folder = os.environ.get('PROJECT_ROOT')
        reports_folder = os.path.join(root_folder, "reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)
        return reports_folder
    except Exception as e:
        print(print_template("Could not find or create reports folder: {}".format(e)))
        return False


def download_sitemap(sitemap_url: str,) -> Union[bytes, bool]:
    reports_folder = check_reports_folder_exist()
    sitemap_xml_file = os.path.join(reports_folder, "sitemap-iblock-66.xml")
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        if "urlset xmlns" in response.text:
            with open(sitemap_xml_file, 'wb') as file:
                file.write(response.content)
            return response.content
    except Exception as e:
        return False


def is_first_run(report_filename) -> bool:
    reports_folder = check_reports_folder_exist()
    reports_file = os.path.join(reports_folder, report_filename)
    return False if os.path.isfile(reports_file) else True


def random_sleep(seconds: int):
    random_value = random.uniform(0.5, 2)
    time.sleep(seconds + random_value)