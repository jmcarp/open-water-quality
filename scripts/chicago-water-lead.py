#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import xlrd
import urllib
import requests
import logging

logging.basicConfig(level=logging.INFO)

data_url = 'http://www.chicagowaterquality.org/Results.xlsx'
tamu_url = 'http://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsed_V04_01.aspx'

def download(path):
    resp = requests.get(data_url, stream=True)
    resp.raise_for_status()
    zip_path = os.path.join(path, os.path.split(data_url)[-1])
    with open(os.path.join(path, os.path.split(data_url)[-1]), 'wb') as fp:
        for chunk in resp.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)

masked = re.compile(r'(^\d*)XX')
def unmask(match):
    unmasked = match.groups()[0] + '00'
    if int(unmasked) == 0:
        return '1'
    return unmasked

def geocode(in_path, cache_path):
    xlsx_name = os.path.splitext(os.path.split(data_url)[-1])[0] + '.xlsx'
    xlsx_path = os.path.join(in_path, xlsx_name)
    book = xlrd.open_workbook(xlsx_path)
    sheet = book.sheet_by_name('First')
    headings = [each.strip().lower() for each in sheet.row_values(2)]
    rows = [dict(zip(headings, sheet.row_values(idx))) for idx in range(3, sheet.nrows)]
    os.makedirs(cache_path, exist_ok=True)
    masked = re.compile(r'(^\d*)XX')
    for row in rows:
        address = masked.sub(unmask, row['address'])
        address_label = row['address']
        key = urllib.parse.quote_plus(address_label)
        key_path = os.path.join(cache_path, key + '.json')
        if os.path.exists(key_path):
            logging.info('Found cached geodata for address {}; skipping'.format(address))
            continue
        logging.info('Geocoding address {}'.format(address))
        resp = requests.get(tamu_url, params={
            'apikey': os.getenv('TAMU_API_KEY'),
            'version': '4.01',
            'format': 'json',
            'census': 'true',
            'censusYear': '2000|2010',
            'streetAddress': address,
            'city': 'Chicago',
            'state': 'IL'})
        resp.raise_for_status()
        data = resp.json()
        with open(key_path, 'w') as fp:
            json.dump(data, fp)

if __name__ == "__main__":
    download('./data')
    geocode('./data', './geodata/chicago-water-lead')
