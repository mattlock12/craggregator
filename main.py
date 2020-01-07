import collections
import csv
import re
import requests
from bs4 import BeautifulSoup
from datetime import date
from sys import argv

CL_URL_BASE = "https://sandiego.craigslist.org"
SEARCH_STRING_BASE = "/search/cta?"

def parse_page(soup):
    results = []
    p_tags = soup.find_all('p', class_='result-info')
    for p_tag in p_tags:
        result_dict = {
            'year': '',
            'price': ''
        }

        result_text = p_tag.find('a', 'result-title').text
        probably_year = re.match('[0-9]{4}', result_text)
        if probably_year:
            probably_year = probably_year.group()
        result_price = p_tag.find('span', 'result-price').text.replace("$", "")

        if result_price and int(result_price) > 1000 and probably_year:
            result_dict['year'] = probably_year
            result_dict['price'] = result_price
            results.append(result_dict)

    return results

def main():
    if len(argv) < 2:
        print("Must add a query as second argument like 'toyota+tacoma'")
        return

    query = argv[1]
    max_price = 15000
    if len(argv) > 2:
        max_price = argv[2]

    results = []
    next_uri = SEARCH_STRING_BASE  + "query=%s&max_price=%s" % (query, max_price)
    file_name = "%s_max_price_%s_%s.csv" % (query.replace("+", "_"), max_price, date.today().strftime('%Y_%m_%d'))
    while next_uri:
        resp = requests.get(CL_URL_BASE + next_uri)
        soup = BeautifulSoup(resp.content)
        results += parse_page(soup)
        next_tag = soup.find('a', class_='button next')
        next_uri = next_tag['href']

    aggregate_results = collections.defaultdict(list)
    for r_dict in results:
        aggregate_results[r_dict['year']].append(r_dict['price'])

    results_file = csv.writer(open(file_name, 'w+'))
    results_file.writerows([['Year', 'Total for Sale', 'Min', 'Avg', 'Max'],])

    sorted_years = sorted(year for year in aggregate_results if year)
    for year in sorted_years:
        prices = aggregate_results[year]
        results_file.writerows([[
            year,
            len(prices),
            min([int(p) for p in prices]),
            sum([int(p) for p in prices]) / len(prices),
            max([int(p) for p in prices])
        ]])


if __name__ == '__main__':
    main()
