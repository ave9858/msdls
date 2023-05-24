#!/usr/bin/env python3
import argparse
import json
import logging
import random
import uuid
from html.parser import HTMLParser

import requests

MICROSOFT_URL = "https://www.microsoft.com/en-us/api/controls/contentinclude/html"
MICROSOFT_REFERER = "https://www.microsoft.com/en-us/software-download/windows11"


def find_html_attribute(attrs, find):
    return next((x[1] for x in attrs if x[0] == find), False)


class ParseLanguages(HTMLParser):
    def __init__(self):
        super(ParseLanguages, self).__init__()
        self.languages = []
        self.name = "Invalid product"
        self.error = False

    def check_for_error(self, attrs):
        pId = find_html_attribute(attrs, "id")
        if pId == "errorModalMessage":
            self.error = True

    def append_language(self, attrs):
        data = find_html_attribute(attrs, "value")

        if data == "" or data == False:
            return

        self.languages.append(json.loads(data))

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.check_for_error(attrs)

        if tag != "option":
            return

        self.append_language(attrs)

    def handle_data(self, data):
        if "The product key is eligible for " not in data:
            return

        name = data.replace("The product key is eligible for ", "")
        name_clean = name.replace("  ", " ")

        if name_clean == "":
            name_clean = "Unknown"

        if "Insider" in name_clean:
            self.error = True

        self.name = name_clean


class ParseDownloads(HTMLParser):
    def __init__(self):
        super(ParseDownloads, self).__init__()
        self.error = False

    def handle_starttag(self, tag, attrs):
        if tag != "p":
            return

        pId = find_html_attribute(attrs, "id")
        if pId == "errorModalMessage":
            self.error = True


def get_data_from_ms(params):
    headers = {
        "Referer": MICROSOFT_REFERER,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0",
    }

    r = requests.get(MICROSOFT_URL, params=params, headers=headers)
    if not r.ok:
        return False

    r.encoding = "utf-8-sig"
    return r.text


def get_product(productId, sessionId):
    params = {
        "pageId": "cd06bda8-ff9c-4a6e-912a-b92a21f42526",
        "host": "www.microsoft.com",
        "segments": "software-download,windows11",
        "query": "",
        "action": "getskuinformationbyproductedition",
        "productEditionId": productId,
        "sessionId": sessionId,
        "sdVersion": "2",
    }

    html = get_data_from_ms(params)
    if html == False:
        return False

    parser = ParseLanguages()
    parser.feed(html)

    return parser


def check_download(skuId, language, sessionId):
    params = {
        "pageId": "cfa9e580-a81e-4a4b-a846-7b21bf4e2e5b",
        "host": "www.microsoft.com",
        "segments": "software-download,windows11",
        "query": "",
        "action": "GetProductDownloadLinksBySku",
        "skuId": skuId,
        "language": language,
        "sessionId": sessionId,
        "sdVersion": "2",
    }

    html = get_data_from_ms(params)
    if html == False:
        return False

    parser = ParseLanguages()
    parser.feed(html)

    return not parser.error


def check_product(productId):
    session = uuid.uuid4()
    product = get_product(productId, session)

    if product.error:
        return (product.name, False)

    lang = random.choice(product.languages)
    skuId = lang["id"]
    language = lang["language"]

    return (product.name, check_download(skuId, language, session))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Checks which product IDs of the Microsoft Software Download are available."
    )
    parser.add_argument(
        "--first", help="first product ID to check", required=True, type=int
    )
    parser.add_argument(
        "--last", help="last product ID to check", required=True, type=int
    )
    parser.add_argument(
        "--write",
        help="save results to the specified JSON file",
        type=argparse.FileType("w", encoding="UTF-8"),
    )
    parser.add_argument(
        "--update",
        help="update the specified JSON with results",
        type=argparse.FileType("r+", encoding="UTF-8"),
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.first < 1 or args.last < 1 or args.last < args.first:
        logging.critical("Invalid product IDs")
        exit(1)

    if args.update and args.write:
        logging.critical("Update and write cannot be used at the same time")
        exit(1)

    products = {}

    json_file = args.write
    if args.update:
        json_file = args.update
        from_json = json.loads(args.update.read())

        if "products" in from_json:
            products = from_json["products"]

    for i in range(args.first, args.last + 1):
        if str(i) in products:
            logging.warning(f"Skipping known product ID {i}")
            continue

        logging.info(f"Checking product ID {i}...")
        name, result = check_product(i)

        logging.info(f"Result: {name}. Available: {result}")

        if result == False:
            continue

        products[i] = name

    if json_file:
        logging.info("Writing the JSON file...")
        json_file.seek(0)
        json_file.truncate(0)
        json_file.write(json.dumps({"products": products}, indent=2))
        json_file.write("\n")

    logging.info("Done")
