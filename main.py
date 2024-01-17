import os

from utils.parser import parse_sitemap_xml, start_site_parsing
from utils.utils import download_sitemap, print_template


os.environ['PROJECT_ROOT'] = os.path.dirname(os.path.abspath(__file__))
sitemap_url = 'https://ingplast.ru/sitemap-iblock-66.xml'


def start():
    print(print_template("Loading the contents of a sitemap ({}) file...".format(sitemap_url)))

    sitemap_content = download_sitemap(sitemap_url)
    if not sitemap_content:
        print(print_template("Sitemap loading error!"))
        return False
    print(print_template("Download completed!"))

    links = parse_sitemap_xml(sitemap_content)

    print(print_template("Found {} links.".format(len(links))))

    print(print_template("Start parsing..."))
    success_count, failure_count, skipped_count = start_site_parsing(links)
    print(print_template("Parsing completed! Total links: {}, "
                         "of them successful: {}, with an error: {}, links skipped: {}".format(len(links), success_count, failure_count, skipped_count)))


if __name__ == '__main__':
    start()
