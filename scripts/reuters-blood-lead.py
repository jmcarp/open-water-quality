#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import requests
import mapbox_vector_tile

joint_pattern = re.compile(r'^(?:Census Tract (?P<tract>[\d\.]+), )?(?P<zip>\d{5})$')

def download(path):
    resp = requests.get('https://www.reuters.com/investigates/graphics/lead-water/v-3/lead-tiles-v3/1/0/0.pbf')
    resp.raise_for_status()
    with open(path, 'wb') as fp:
        fp.write(resp.content)

def process(in_path, out_path):
    layers = mapbox_vector_tile.decode(open(in_path, 'rb').read())
    rows = [process_row(each['properties']) for each in layers['lead-data']['features']]
    with open(out_path, 'w') as fp:
        json.dump(rows, fp)

def process_row(row):
    processed = {key.lower(): value for key, value in row.items()}
    processed.update(joint_pattern.search(processed['joint']).groupdict())
    return processed

if __name__ == '__main__':
    download('./data/reuters-blood-lead.pbf')
    process('./data/reuters-blood-lead.pbf', './data/reuters-blood-lead.json')
