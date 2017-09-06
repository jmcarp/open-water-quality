#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import xlrd
import urllib
import zipfile
import requests
import logging

logging.basicConfig(level=logging.INFO)

data_url = 'http://apps.pittsburghpa.gov/pwsa/PWSA_LeadLabResults_July2017_CustomerRequests.zip'
tamu_url = 'http://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsed_V04_01.aspx'

def download(path):
    resp = requests.get(data_url, stream=True)
    resp.raise_for_status()
    zip_path = os.path.join(path, os.path.split(data_url)[-1])
    with open(os.path.join(path, os.path.split(data_url)[-1]), 'wb') as fp:
        for chunk in resp.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(path)

def geocode(in_path, cache_path):
    xlsx_name = os.path.splitext(os.path.split(data_url)[-1])[0] + '.xlsx'
    xlsx_path = os.path.join(in_path, xlsx_name)
    book = xlrd.open_workbook(xlsx_path)
    sheet = book.sheet_by_name('Sheet1')
    headings = [each.strip().lower() for each in sheet.row_values(0)]
    rows = [dict(zip(headings, sheet.row_values(idx))) for idx in range(1, sheet.nrows)]
    os.makedirs(cache_path, exist_ok=True)
    for row in rows:
        address = '{} {}'.format(int(row['block']) or 1, row['street'])
        address_label = '{} {}'.format(int(row['block']), row['street'])
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
            'city': row['city'],
            'state': 'PA'})
        resp.raise_for_status()
        data = resp.json()
        with open(key_path, 'w') as fp:
            json.dump(data, fp)

if __name__ == '__main__':
    download('./data')
    geocode('./data', './geodata/pittsburgh-water-lead')
