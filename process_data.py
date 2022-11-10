# process_data.py
import geopandas as gpd
import topojson as tp
import pandas as pd
import numpy as np
import config

vote_geo_map = {
    'Storkreds': 'storkredse',
    'Opstillingskreds': 'opstillingskredse',
    'Afstemningsområde': 'afstemningsomraader'
}

def data_geopandas(data):
    gdf = gpd.GeoDataFrame.from_features(data['features'])
    crs_init = 'EPSG:4326'
    if not gdf.crs:
        try:
            crs_init = data['crs']['properties']['name']
        except:
            print('Data CRS not found, assume EPSG:4326')
    
    gdf = gdf.set_crs(crs_init)
    gdf = gdf.to_crs(3857)
    
    gdf = tp.Topology(
        gdf,
        prequantize = False,
        toposimplify = 200,
        prevent_oversimplify = True
        ).to_gdf()

    return gdf

def process_geo_df(df):
    '''
    Make sure geo data identifers match vote data
    '''
    df['regionsnavn'] = df['regionsnavn'].str.replace('Region ', '')
    df['navn'] = df['navn'].str.replace('Århus', 'Aarhus')

    # add column to be used for heatmap of vote fraction
    df['value'] = 0.2

    return df

def process_vote_df(df):
    '''
    Align vote-df to geo-df naming etc.
    '''
    df = df.drop(columns = df.columns[df.isna().all()])
    df = df.rename(columns = {'Navn': 'Parti'})
    df = df.drop(columns = ['StemmerPct'])

    cols = ['Mandater', 'Kredsmandater', 'Tillaegsmandater']
    missing = [c for c in cols if c not in df]
    present = [c for c in cols if c not in missing]
    df[present] = df[present].fillna(0)
    df[missing] = None

    df['Id'] = df['Id'].replace('', -999)
    df = df.fillna(-999)
    
    df.insert(0, 'navn',  df['Sted'])
    df['navn'] = df['navn'].str.replace('s Storkreds', '')
    df['navn'] = df['navn'].str.replace('^\d{1,2}\. ', '', regex = True)
    df['navn'] = df['navn'].str.replace('Århus', 'Aarhus')
    df['Parti'] = df['Parti'].str.strip().str.replace('  ', ' ')
    df['Parti'] = df['Parti'].replace(config.PARTY_RENAME)

    df['Resultattype'] = df['Resultattype'].replace(vote_geo_map)

    df = df.apply(pd.to_numeric, errors = 'ignore')
    df['VoteFrac'] = df['StemmerAntal'] / df['IAltGyldigeStemmer']

    return df

def parse_parties(vote_df):
    data = {}
    cols = ['Bogstav', 'Parti']
    sub_df = vote_df.loc[vote_df[cols].duplicated() == False, cols]
    data['parties_incl_no_name'] = sub_df['Parti'].to_list()
    sub_df = sub_df[sub_df['Parti'] != 'Uden for partier']
    
    data['parties'] = sub_df['Parti'].to_list()
    data['party_letter'] = sub_df['Bogstav'].to_list()

    short_name = [p.split('.')[1].strip() for p in data['parties']]
    short_name = [p.split('-')[0].strip() for p in short_name]
    short_name = [p.split(',')[0].strip() for p in short_name]
    data['short_name'] = short_name

    return data


def vote_dict2df(data):
    meta = []
    rec_path = ['Stemmer']
    for i in data:
        [meta.append(k) for k in i.keys() 
        if k not in meta + rec_path]
    
    df = pd.json_normalize(
        data, record_path = rec_path, meta = meta, errors = 'ignore'
    )

    return pd.json_normalize(
        data, record_path = rec_path, meta = meta, errors = 'ignore'
    )

def map_geo_vote_data(geo_df, vote_df, resulttype):
    vote_df['geo_nr'] = np.nan

    geo_sub_df = geo_df[['navn', 'nummer']].copy()
    geo_sub_df = geo_sub_df.set_index('navn')

    mask = vote_df['Resultattype'] ==  resulttype
    vote_df.loc[mask, 'geo_nr'] = (
        vote_df.loc[mask, 'navn'].map(geo_sub_df['nummer'])
        )

    return vote_df

def votedata2dict(df):
    ignore_cols = ['Id', 'Bogstav', 'Parti']
    party_cols = [
        'Mandater', 'Kredsmandater', 'Tillaegsmandater',
        'StemmerAntal', 'VoteFrac'
        ]
    single_value_cols = ['Resultattype', 'ValgDato']
    data = {}
    for resulttype, result_grp in df.groupby('Resultattype'):
        sub_df = result_grp.copy()
        sub_df = sub_df.drop(columns = sub_df.columns[sub_df.isna().all()])
        
        resulttype_cols = [
            c for c in sub_df
            if c not in party_cols + single_value_cols + ignore_cols
            ]

        data[resulttype] = {
            i: grp.to_dict('list') for i, grp 
            in sub_df.groupby('Parti')[party_cols]
            }
        data[resulttype].update({
            i: sub_df[i].values[0] for i in single_value_cols
            })
        data[resulttype].update(
            sub_df.drop_duplicates('Sted')[resulttype_cols].to_dict('list')
            )

    return data

def region_districts_from_geodata(geo_df, mapping):
    items = {
        i: geo_df[mapping[i]].unique().tolist() 
        for i in mapping.keys()
        }
    
    return items
