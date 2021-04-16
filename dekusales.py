from lxml import html
from pathlib import Path
from string import Template
from urllib import parse

import argparse
import requests
import sys
import os

def process_url(url_string, deku_game_id):
    parsed_url = parse.urlsplit(url_string)
    query = parsed_url.query

    if len(parsed_url.query) > 0:
        query = parsed_url.query + '&format=digital'
    else:
        query = 'format=digital'


    digital_format_url = parse.urlunsplit(parse.SplitResult(parsed_url.scheme,
                                                            parsed_url.netloc,
                                                            parsed_url.path,
                                                            query,
                                                            parsed_url.fragment))
    r = requests.get(digital_format_url)

    game_information = {}

    if r.status_code == requests.codes.ok:
        html_tree = html.fromstring(r.content)

        game_name = html_tree.xpath('//span[@class="display-5"]/text()')
        if len(game_name) ==  0:
            print('Kann Spielename für ' + deku_game_id + ' nicht finden. Abbruch.')

            return game_information

        game_name = game_name[0].strip()

        pricing_table = html_tree.xpath('//table[contains(@class, "item-price-table")]')
        if len(pricing_table) == 0:
            print('Kann Preistabelle für ' + game_name + ' nicht finden. Abbruch.')

            return game_information

        pricing_table = pricing_table[0]
        eshop_line = pricing_table.xpath('tr[td[@class="version" = "Digital"]]')

        if len(eshop_line) == 0:
            print('Kann eShop-Preis für ' + game_name + ' nicht finden. Abbruch.')

            return game_information

        eshop_line = eshop_line[0]

        eshop_url = eshop_line.xpath('td[position() = 3]/a/@href')
        if len(eshop_url) > 0:
            eshop_url = eshop_url[0].strip()
        else:
            eshop_url = None

        eshop_price = eshop_line.xpath('td[position() = 3]/a/div/text()')
        if len(eshop_price) > 0:
            eshop_price = eshop_price[0].strip()
        else:
            eshop_price = None

        eshop_rebate = eshop_line.xpath('td[position() = 3]/a/div/span/text()')
        if len(eshop_rebate) > 0:
            eshop_rebate = eshop_rebate[0].strip()
        else:
            eshop_rebate = None

        sales_end_date = pricing_table.xpath('tr/td/a[contains(text(), "Sale")]/text()')
        if len(sales_end_date) > 0:
            sales_end_date = sales_end_date[0].strip()
        else:
            sales_end_date = None

        publisher = html_tree.xpath('//li[contains(strong/text(), "Publisher")]/a/text()')
        if len(publisher) > 0:
            publisher = publisher[0].strip()
        else:
            publisher = None

        developer = html_tree.xpath('//li[contains(strong/text(), "Developer")]/a/text()')
        if len(developer) > 0:
            developer = developer[0].strip()
        else:
            developer = None

        game_information['game_name'] = game_name
        game_information['eshop_url'] = eshop_url
        game_information['eshop_price'] = eshop_price
        game_information['eshop_rebate'] = eshop_rebate
        game_information['sales_end_date'] = sales_end_date

        if game_name != None:
            game_information['game_hashtag'] = '#' + ''.join(game_name.split())

        if developer != None:
            game_information['publisher_hashtag'] = '#' + ''.join(developer.split())
        elif publisher != None:
            game_information['publisher_hashtag'] = '#' + ''.join(publisher.split())
        else:
            game_information['publisher_hashtag'] = None


    return game_information


def find_template(template_dir, deku_game_id):
    template_file = template_dir + '/' + deku_game_id

    if not os.path.isfile(template_file):
        template_file = template_dir + "/__default"

    p = Path(template_file)
    template = p.read_text()

    return template

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', required=True)
    parser.add_argument('-o', '--output-file')
    parser.add_argument('-v', dest='verbose', action='store_true')
    args = parser.parse_args()

    output_filename = args.output_file
    output_file = None

    if output_filename != None:
        output_file = open(output_filename, 'w')

    with open(args.input_file, 'r') as f:
        for url_string in f:
            url_string = url_string.strip()

            #
            # Die URL hat die Form
            #   https://www.dekudeals.com/items/katana-zero
            #
            # Wir brauchen den Teilstring 'katana-zero'

            parsed_url = parse.urlsplit(url_string)
            deku_game_id = parsed_url.path.rpartition('/')[2]
            print("Verarbeite " + deku_game_id)

            game_information = process_url(url_string, deku_game_id)
            template_str = find_template("templates", deku_game_id)
            template = Template(template_str)

            sales_information = template.substitute(game_information)

            if output_file != None:
                output_file.write(sales_information)
                output_file.write('\n')
            else:
                print(sales_information)

    if output_file != None:
        output_file.close()


if __name__ == "__main__":
    # execute only if run as a script
    main()
