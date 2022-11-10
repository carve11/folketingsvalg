# io_functions.py
import pandas as pd
import requests
import os
import json
from xml.etree import ElementTree
import config


def retrieve_geo_data(address, from_disk = True):
    if from_disk:
        data = read_json_disk(f'{address}_geodata.json')
    else:
        data = request_geo_data(config.URL_GEO, address)
        save_json_disk(data, f'{address}_geodata.json')

    return data

def request_geo_data(url, address):
    req_url = f'{url}/{address}?format=geojson'
    print('Requesting data at ', req_url)
    response = requests.get(req_url)
    status = response.status_code
    if status != 200:
        print(req_url)
        raise ValueError(f'Response status code: {status}')
    data = response.json()
    print('Done')

    return data

def read_json_disk(fname):
    print(f'Reading data from disk, {fname}...')
    f = os.path.join(config.ROOT_DIR, config.DATA_DIR, fname)

    with open(f, 'r') as fin:
        data = json.load(fin)

    print('Done')

    return data

def save_json_disk(data, fname):
    data_folder = os.path.join(config.ROOT_DIR, config.DATA_DIR)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    f = os.path.join(data_folder, fname)
    with open(f, 'w') as fout:
        json.dump(data, fout)

def read_csv2df(fname, sep = ','):
    f = os.path.join(config.ROOT_DIR, config.DATA_DIR, fname)

    return pd.read_csv(f, sep = sep, encoding = 'ISO-8859-1')

def read_index_template(fname):
    f = os.path.join(config.ROOT_DIR, 'templates', fname)
    with open(f, 'r') as fin:
        template = fin.read()

    return template

def request_response(url):
    response = requests.get(url)
    status = response.status_code
    if status != 200:
        print(url)
        raise ValueError(f'Response status code: {status}')

    return response

def retrieve_vote_results(year_url, from_disk = True):
    year = year_url[0]
    url = year_url[1]

    if from_disk:
        data = read_json_disk(f'{year}_voteresult.json')
    else:
        data = request_vote_results(url)
        save_json_disk(data, f'{year}_voteresult.json')

    return data

def request_vote_results(url):
    '''
    Vote results are as XML at a given URL.
    Each district result are again an XML at a given URL.
    Parse the data and return a list of dictionaries for each district.
    '''
    print('Requesting xml data at', url)
    tree = request_xml_data(url)
    
    district_vote_data = []
    
    for k,v in config.DISTRICT_ATTRIB.items():
        for x in tree.iter(k):
            data = {}
            data['Resultattype'] = k
            data['Sted'] = x.text
            
            for i in v:
                data[i] = x.get(i)  

            result_xml = x.get('filnavn')
            result_tree = request_xml_data(result_xml)
            data.update(parse_votexml_result(result_tree))
            
            district_vote_data.append(data)
            
    print('Done')

    return district_vote_data

def request_xml_data(url):
    response = request_response(url)
    
    return ElementTree.fromstring(response.content)

def parse_votexml_result(tree):
    '''
    Parse xml tree representing a specific district vote result.
    Return dict of specific data configured in VOTE_ATTRIB
    '''
    data = {}
    for k,v in config.VOTE_ATTRIB.items():
        for x in tree.iter(k):
            if v == 'nochildren':
                data[x.tag] = x.text
            else:
                if k not in data:
                    data[k] = []
                    
            for child in x:
                if child.tag == 'Parti':
                    data[k].append(child.attrib)
                else:
                    data.update({child.tag: child.text})
    return data
