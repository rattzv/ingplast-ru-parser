import csv
import os
from collections import OrderedDict


from utils.utils import check_reports_folder_exist


def create_report_file(report_filename):
    reports_folder = check_reports_folder_exist()
    report_file = os.path.join(reports_folder, report_filename)
    file = open(report_file, 'w', newline='')
    writer = csv.writer(file, delimiter=';')
    writer.writerow([])
    return writer


def read_report_file(report_filename):
    reports_folder = check_reports_folder_exist()
    report_file = os.path.join(reports_folder, report_filename)
    file = open(report_file, 'r+', newline='')
    reader = csv.reader(file)
    return reader


def write_to_csv(characteristics, report_filename):
    reports_folder = check_reports_folder_exist()
    report_file = os.path.join(reports_folder, report_filename)

    unique_characteristics = OrderedDict()
    for chars in characteristics:
        unique_characteristics.update(chars)

    with open(report_file, "w", newline='', encoding='utf-8') as csvfile:
        fieldnames = list(unique_characteristics)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for chars in characteristics:
            writer.writerow(chars)


def extract_exists_from_csv(report_filename):
    reports_folder = check_reports_folder_exist()
    report_file = os.path.join(reports_folder, report_filename)

    rows = []
    with open(report_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            rows.append(row)
    return rows
