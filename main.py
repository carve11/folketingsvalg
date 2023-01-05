import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import CustomJS
from bokeh.transform import factor_cmap
from io_functions import retrieve_geo_data, read_index_template
from io_functions import retrieve_vote_results
from process_data import data_geopandas, process_geo_df, parse_parties
from process_data import vote_dict2df, votedata2dict, process_vote_df
from process_data import region_districts_from_geodata, country_wide_results
from process_data import simplify_geo, voters_density, labels_from_bins
from process_data import data4histogram
from visualization import create_sources, Map, widgets, ElectionBarCharts
from visualization import HistogramChart, PartyDensityGridPlot
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
        self.map_select_options()
        
        self.srcs = self.data_sources()

        self.p_map = Map(self.srcs)

        self.p_election_results = ElectionBarCharts(
            srcs = self.srcs,
            plot_cols = list(self.vote.keys()),
            y_cat = 'party_shortname'
            )

        self.p_histogram = HistogramChart(
            src = self.srcs['hist_voters_density'],
            x_label = 'Stemmeberettigede per km²',
            y_label = 'Sandsynlighed',
            xlog_scale = True
            )

        self.voters_density_grid = PartyDensityGridPlot(self.vote, self.years)

        self.wdgs = widgets(self.heatmap_type_items)
        self.callbacks()

        index_template = read_index_template(config.INDEX_TEMPLATE)
        contents = [
            self.p_map.plot,
            self.p_election_results.plots,
            self.p_histogram.plot,
            self.voters_density_grid.plot
            ]
        contents += list(self.wdgs.values())

        save(contents, template = index_template, title = config.TITLE)

    def geo_data(self):
        geo_data = retrieve_geo_data(
            self.district_type, from_disk = config.DATA_FROM_DISK
            )
        gdf = data_geopandas(geo_data)
        gdf = process_geo_df(gdf)
        gdf = simplify_geo(gdf)

        district_items = region_districts_from_geodata(gdf, self.district_mapping)

        return gdf, district_items

    def election_results(self):
        results = {}
        for y, url in self.vote_url.items():
            results[y] = {}
            data_json = retrieve_vote_results(
                (y, url), from_disk = config.DATA_FROM_DISK
                )
            data = vote_dict2df(data_json)
            data = process_vote_df(data)
            data = voters_density(self.gdf, data)

            results[y]['parties'] = parse_parties(data)
            results[y]['data'] = votedata2dict(data)

        return results

    def map_select_options(self):
        '''
        Options that define what data the map is displaying
        '''
        districts = list(self.district_items.keys())
        heatmap_type = {}
        heatmap_type[0] = {
            'label': 'Administrative inddelinger',
            'type': 'district',
            'options': districts
            }
        
        bins = [0, 50, 100, 400, 1000, 100000]
        self.years = sorted(self.vote.keys(), reverse = True)
        voters_density = [f'Vælgertæthed {i}' for i in self.years]
        heatmap_type[1] = {
            'label': 'Vælgertæthed',
            'type': 'voters_density',
            'options': voters_density,
            'bins': bins,
            'lgnd_labels': labels_from_bins(bins)
            }

        curr_item = len(heatmap_type.keys())
        for i, y in enumerate(self.years):
            date = self.vote[y]['data']['Land']['ValgDato']
            options = tuple(zip(
                self.vote[y]['parties']['parties'],
                self.vote[y]['parties']['short_name']
                ))
            heatmap_type[i+curr_item] = {
                'label': 'Folketingsvalg ' + date,
                'type': 'value',
                'year': y,
                'options': options
                }

        curr_item = len(heatmap_type.keys())-1
        options = tuple(zip(
            self.vote[self.years[0]]['parties']['parties'],
            self.vote[self.years[0]]['parties']['short_name']
            ))
        heatmap_type[curr_item+1] = {
            'label': f'Ændring {self.years[0]}-{self.years[1]}',
            'type': 'diff',
            'year': (self.years[0], self.years[1]),
            'options': options
            }
        
        self.heatmap_type_items = heatmap_type

    def callbacks(self):
        p = self.p_map.plot

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
                    'color_mapper': self.p_map.mapper,
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

    def data_sources(self):
        srcs = create_sources()
        srcs['geo'].geojson = self.gdf.to_json()
        srcs['election_results'].data = country_wide_results(self.vote)

        voters_conc = (
            self.vote[self.years[0]]['data']
            ['opstillingskredse']['voters_density']
            )
        srcs['hist_voters_density'].data = data4histogram(
            voters_conc, xlog_scale = True, bins = 12, stat = 'probability'
            )

        return srcs

if __name__ == '__main__':
    Folketingsvalg()

