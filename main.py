import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import CustomJS
from bokeh.transform import factor_cmap
from io_functions import retrieve_geo_data, read_index_template
from io_functions import retrieve_vote_results
from process_data import data_geopandas, process_geo_df, parse_parties
from process_data import vote_dict2df, votedata2dict, process_vote_df
from process_data import region_districts_from_geodata, map_geo_vote_data
from visualization import create_sources, Map, widgets
import callback_js_code
import config


output_file(config.INDEX_FNAME)

class Folketingsvalg:
    def __init__(self):
        self.district_type = 'opstillingskredse'
        self.district_mapping = config.DISTRICT_MAPPING
        self.fake_coord = (1400747.597, 7503240.297)
        self.vote_url = config.ELECTION_URL
        self.gdf, self.district_items = self.geo_data()
        self.vote = self.election_results()
        self.map_select_year_options()
        
        self.srcs = create_sources(self.gdf)

        self.p_map = Map(self.srcs)
        self.wdgs = widgets(self.heatmap_type_items)
        self.callbacks()

        index_template = read_index_template(config.INDEX_TEMPLATE)
        contents = [self.p_map.plot] + list(self.wdgs.values())
        save(contents, template = index_template, title = config.TITLE)

    def geo_data(self):
        geo_data = retrieve_geo_data(self.district_type, from_disk = False)
        gdf = data_geopandas(geo_data)
        gdf = process_geo_df(gdf)

        district_items = region_districts_from_geodata(gdf, self.district_mapping)

        return gdf, district_items

    def election_results(self):
        results = {}
        for y, url in self.vote_url.items():
            results[y] = {}
            data_json = retrieve_vote_results((y, url), from_disk = False)
            data = vote_dict2df(data_json)
            data = process_vote_df(data)
            data = map_geo_vote_data(self.gdf, data, self.district_type)

            results[y]['parties'] = parse_parties(data)
            results[y]['data'] = votedata2dict(data)

        return results

    def map_select_year_options(self):
        districts = list(self.district_items.keys())
        heatmap_type = {}
        heatmap_type[0] = {
            'label': 'Administrative inddelinger',
            'type': 'district',
            'options': districts
            }
        
        years = sorted(self.vote.keys(), reverse = True)
        for i, y in enumerate(years):
            date = self.vote[y]['data']['Land']['ValgDato']
            heatmap_type[i+1] = {
                'label': 'Folketingsvalg ' + date,
                'type': 'value',
                'year': y,
                'options': self.vote[y]['parties']['parties']
                }
        heatmap_type[3] = {
            'label': f'Ændring {years[0]}-{years[1]}',
            'type': 'diff',
            'year': (years[0], years[1]),
            'options': self.vote[years[0]]['parties']['parties']
            }
        
        self.heatmap_type_items = heatmap_type

    def callbacks(self):
        p = self.p_map.plot
        factorcmap = factor_cmap(
            field_name = 'legend',
            palette = self.p_map.mapper['district'].palette,
            factors = []
            )

        self.wdgs['map_select'].js_on_change(
            'value', 
            CustomJS(
                args = {
                    'geo_src': self.srcs['geo'],
                    'fake1_src': self.srcs['map_fake1'],
                    'fake2_src': self.srcs['map_fake2'],
                    'vote_data': self.vote,
                    'heatmap_type_wdg': self.wdgs['heatmap_type'],
                    'fake_coord': self.fake_coord,
                    'party_select_div': self.wdgs['select_div'],
                    'district_items': self.district_items,
                    'district_mapping': self.district_mapping,
                    'heatmap_type_items': self.heatmap_type_items,
                    'plot': p,
                    'factor_cmap': factorcmap,
                    'map_select': self.wdgs['map_select']
                },
                code = callback_js_code.map_select_js_cb_code,
                name = 'map_select_script'
                )
            )

        self.wdgs['mapper_slider'].js_on_change(
            'value', 
            CustomJS(
                args = {
                    'mapper': self.p_map.mapper['votefrac']['mapper'],
                    'palette': self.p_map.mapper['votefrac']['whole_palette']
                },
                code = callback_js_code.mapper_js_cb_code
                )
            )

        self.wdgs['heatmap_type'].js_on_click(
             CustomJS(
                args = {
                'plot': p,
                'diff_mapper': self.p_map.mapper['diff_map'],
                'value_mapper': self.p_map.mapper['votefrac']['mapper'],
                'mapper_slider': self.wdgs['mapper_slider'],
                'map_select': self.wdgs['map_select'],
                'heatmap_type_items': self.heatmap_type_items,
                },
                code = callback_js_code.heatmap_type_js_cb_code
                )
            )

        hover_cb = CustomJS(
            args = {
                'geo_src': self.srcs['geo'],
                'vote_data': self.vote,
                'heatmap_type_wdg': self.wdgs['heatmap_type'],
                'heatmap_type_items': self.heatmap_type_items,
                'map_select': self.wdgs['map_select'],
                'plot': p,
                },
            code = callback_js_code.map_info_js_cb_code
            )
        p.select(name = 'hover')[0].callback = hover_cb


if __name__ == '__main__':
    Folketingsvalg()

