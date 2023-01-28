# process_data.py
import geopandas as gpd
import topojson as tp
import pandas as pd
import numpy as np
import config

VOTE_GEO_MAP = {
    'Storkreds': 'storkredse',
    'Opstillingskreds': 'opstillingskredse',
    'Afstemningsområde': 'afstemningsomraader'
}

DROP_GEO_COLS = [
    'dagi_id', 'kode', 'regionskode', 'kredskommunekode', 'storkredsnummer',
    'valglandsdelsbogstav','valgkredsnummer', 'ændret', 'geo_ændret',
    'geo_version', 'visueltcenter_x', 'visueltcenter_y'
]

def data_geopandas(data):
    gdf = gpd.GeoDataFrame.from_features(data['features'])
    crs_init = 'EPSG:4326'
    if not gdf.crs:
        try:
            crs_init = data['crs']['properties']['name']
        except:
            print('Data CRS not found, assume EPSG:4326')
    
    gdf = gdf.set_crs(crs_init)
    # Bokeh uses Mercator projection (3857)
    gdf = gdf.to_crs(3857)

    return gdf

def multipolygon_explode(gdf):
    # Convert MultiPolygon to Polygon
    return gdf.reset_index().explode(ignore_index = True)

def geo_area(gdf):
    # Cylindrical equal-area format for area calculation
    gdf['area'] = gdf['geometry'].to_crs({'proj':'cea'}).area/10**6
    
    return gdf

def simplify_topology(df, epsilon):
    topo = tp.Topology(
        data = df,
        prequantize = False
    )
    topo = topo.toposimplify(
        epsilon = epsilon,
        simplify_with = 'shapely',
        simplify_algorithm = 'dp',
        prevent_oversimplify = True
    ).to_gdf()

    return topo

def simplify_geo(gdf):
    '''
    Simplify the geometry of the districts in order to reduce file size.
    Islands with low area are removed.
    '''
    low_area_districts = ['Indre By', 'Sundbyøster', 'Østerbro', 'Aakirkeby']
    query = (
        ((~gdf['navn'].isin(low_area_districts)) & (gdf['area'] > 1.0)) 
        | ((gdf['navn'].isin(low_area_districts)) & (gdf['area'] > 1.0e-2))
    )
    gdf = gdf[query]

    high_res = ['København', 'Københavns Omegn', 'Nordsjælland', 'Sjælland']

    gdf1 = simplify_topology(gdf[gdf['storkredsnavn'].isin(high_res)], 80)
    gdf2 = simplify_topology(gdf[~gdf['storkredsnavn'].isin(high_res)], 160)
    merge = pd.concat([gdf1, gdf2])

    return merge

def process_geo_df(df):
    '''
    Make sure geo data identifers match vote data and add new columns
    '''
    df['regionsnavn'] = df['regionsnavn'].str.replace('Region ', '')
    df['navn'] = df['navn'].str.replace('Århus', 'Aarhus')

    # add column to be used for heatmap of vote fraction
    df['value'] = 0.2

    df = multipolygon_explode(df)
    df = geo_area(df)

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

    df['Resultattype'] = df['Resultattype'].replace(VOTE_GEO_MAP)

    df = df.apply(pd.to_numeric, errors = 'ignore')
    df['VoteFrac'] = df['StemmerAntal'] / df['IAltGyldigeStemmer']

    return df

def voters_density(gdf, vote_df):
    district_area = gdf.groupby('navn')['area'].sum()
    vote_df['area'] = vote_df['navn'].map(district_area)
    vote_df['voters_density'] = vote_df['Stemmeberettigede'] / vote_df['area']

    return vote_df

def parse_parties(vote_df):
    data = {}
    cols = ['Bogstav', 'Parti']
    sub_df = vote_df.loc[vote_df[cols].duplicated() == False, cols]
    data['parties_incl_no_name'] = sub_df['Parti'].to_list()
    sub_df = sub_df[sub_df['Parti'] != 'Uden for partier']
    
    data['parties'] = sub_df['Parti'].to_list()
    data['party_letter'] = sub_df['Bogstav'].to_list()

    data['short_name'] = sub_df['Parti'].replace(config.PARTY_SHORTNAME).to_list()

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

def labels_from_bins(bins):
    labels = [f'{bins[i]}-{bins[i+1] - 1}' for i in range(len(bins)-1)]
    labels[-1] = f'{bins[-2]}-20000'

    return labels

def country_wide_results(vote_data):
    '''
    Create df of country wide election results (vote %) for the years
    in vote df.
    Calculate the percent point difference.
    Add columns for visualiztion adjustments of text labels.
    '''
    dfs = []
    years = sorted(vote_data.keys(), reverse = True)
    for y in years:
        parties = []
        result = []
        for p in vote_data[y]['parties']['parties']:
            parties.append(p)
            result.append(vote_data[y]['data']['Land'][p]['VoteFrac'][0])
        
        dfs.append(pd.DataFrame({str(y): result}, index = parties))
        dfs[-1][f'{y}_label'] = dfs[-1][str(y)].map(
            lambda x: "{0:.1f} %".format(x*100) if x > 0 else "")

    df = pd.concat(dfs, axis = 1)
    df = df.sort_values(by = str(years[0]), ascending = True)
    df = df.fillna(0)
    diff_txt = f'{years[0]}-{years[1]}'
    
    df[diff_txt] = (df[str(years[0])]-df[str(years[1])])*100
    df = df.replace(0, np.nan)
    
    df[f'{diff_txt}_label'] = df[diff_txt].map(
        lambda x: "{0:.1f}".format(x) if x != np.nan else "")
    
    df[f'{diff_txt}_align'] = 'left'
    df.loc[df[diff_txt]<0, f'{diff_txt}_align'] = 'right'
    
    df[f'{diff_txt}_offset'] = 2
    df.loc[df[diff_txt]<0, f'{diff_txt}_offset'] = -2

    df['party_shortname'] = df.index.values
    df['party_shortname'] = df['party_shortname'].replace(config.PARTY_SHORTNAME)

    return df

def data4histogram(xdata, xlog_scale = False, bins = 'auto', stat = None):
    '''
    Create data for histogram plot.
    '''
    if stat not in [None, 'count', 'density', 'probability']:
        raise ValueError(f'Invalid stat property "{stat}"')
        
    if not stat:
        stat = 'count'
        
    data = xdata.copy()
    if xlog_scale:
        data = np.log10(xdata)
    
    bin_edges = np.histogram_bin_edges(data, bins)
    hist, edges = np.histogram(data, density = False, bins = bin_edges)
    widths = np.diff(bin_edges)
    
    count = hist.copy()
    if stat == 'probability':
        hist = hist/hist.sum()
        
    if stat == 'density':
        hist = hist/(hist.sum()*widths)
        
    if xlog_scale:
        bin_edges = np.power(10, bin_edges)

    bin_txt = [
        '{:.0f}-{:.0f}'.format(bin_edges[i], bin_edges[i+1])
        for i in range(len(hist))
        ]

    plot_data = {
        'hist': hist,
        'left_edge': bin_edges[:-1],
        'right_edge': bin_edges[1:],
        'count': count,
        'bin_txt': bin_txt
    }

    return plot_data
