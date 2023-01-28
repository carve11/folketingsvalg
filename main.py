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
        self.wdg_attributes()
        
        self.srcs = self.data_sources()

        self.p_map = Map(self.srcs)

        self.p_election_results = ElectionBarCharts(
            src = self.srcs['election_results'],
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

        self.wdgs = widgets(self.heatmap_type_items, self.wdg_tags)
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

    def wdg_attributes(self):
        '''
        Setup labels and options for map categories widget 
        and associated labels.
        Define translation tags for locale switcher.
        Order in list defines displayed order.
        '''
        self.years = sorted(self.vote.keys(), reverse = True)
        attr_list = []
        tags_list = {'o': [], 'l': []}
        for func in [
            self.district_choice, self.voters_density_choice, 
            self.election_choice, self.election_diff_choice
            ]:
            items = func()
            tags_list['o'].extend(items['o'])
            tags_list['l'].extend(items['l'])
            attr_list.extend(items['a'])
        
        self.heatmap_type_items = {i: attr for i, attr in enumerate(attr_list)}
        self.wdg_tags = tags_list


    def district_choice(self):
        options_tags = [
            {'i18n-key': 'leveling_regions'},
            {'i18n-key': 'regions'},
            {'i18n-key': 'constituencies'},
        ]
        label_tags = [{'i18n-key': 'admin_devision'}]

        attr = {
            'label': label_tags[0]['i18n-key'],
            'type': 'district',
            'options': [i['i18n-key'] for i in options_tags],
            'tags': options_tags
            }

        return {'o': options_tags, 'l': label_tags, 'a': [attr]}

    def voters_density_choice(self):
        bins = [0, 50, 100, 400, 1000, 100000]
        
        options_tags = []
        for y in self.years:
            item = {
                'i18n-key': 'voters_density',
                'i18n-val': {'str': {'str': f'{y}'}}
            }
            options_tags.append(item)
            
        label_tags = [{'i18n-key': 'voters_density_label'}]

        attr = {
            'label': label_tags[0]['i18n-key'],
            'type': 'voters_density',
            'options': [i['i18n-key'] for i in options_tags],
            'bins': bins,
            'lgnd_labels': labels_from_bins(bins),
            'tags': options_tags
            }

        return {'o': options_tags, 'l': label_tags, 'a': [attr]}

    def election_choice(self):
        options_tags = []
        label_tags = []
        attr = []

        for i, y in enumerate(self.years):
            date = self.vote[y]['data']['Land']['ValgDato']
            options = tuple(zip(
                self.vote[y]['parties']['parties'],
                self.vote[y]['parties']['short_name']
                ))

            label_tags.append({
                'i18n-key': 'election_result',
                'i18n-val': {'str': {'str': date}}
            })
                
            attr.append({
                'label': label_tags[-1]['i18n-key'],
                'type': 'value',
                'year': y,
                'options': options,
                'tags': options_tags
                })

        return {'o': options_tags, 'l': label_tags, 'a': attr}

    def election_diff_choice(self):
        options_tags = []

        options = tuple(zip(
            self.vote[self.years[0]]['parties']['parties'],
            self.vote[self.years[0]]['parties']['short_name']
            ))

        label_tags = [{
            'i18n-key': 'election_diff',
            'i18n-val': {'str': {'str': f'{self.years[1]}-{self.years[0]}'}}
        }]

        attr = {
            'label': label_tags[0]['i18n-key'],
            'type': 'diff',
            'year': (self.years[0], self.years[1]),
            'options': options,
            'tags': options_tags
            }

        return {'o': options_tags, 'l': label_tags, 'a': [attr]}

    def callbacks(self):
        p_map = self.p_map.plot

        self.wdgs['map_select'].js_on_change(
            'value', 
            CustomJS(
                args = {
                    'geo_src': self.srcs['geo'],
                    'vote_data': self.vote,
                    'heatmap_type_wdg': self.wdgs['heatmap_type'],
                    'fake_coord': self.fake_coord,
                    'party_select_div': self.wdgs['select_div'],
                    'district_items': self.district_items,
                    'district_mapping': self.district_mapping,
                    'heatmap_type_items': self.heatmap_type_items,
                    'plot': p_map,
                    'color_mapper': self.p_map.mapper,
                    'map_select': self.wdgs['map_select']
                },
                code = callback_js_code.map_select_js_cb_code,
                name = 'map_select_script'
                )
            )

        self.wdgs['heatmap_type'].js_on_click(
             CustomJS(
                args = {
                'plot': p_map,
                'map_select': self.wdgs['map_select'],
                'heatmap_type_items': self.heatmap_type_items,
                },
                code = callback_js_code.heatmap_type_js_cb_code
                )
            )

        hover_map_cb = CustomJS(
            args = {
                'geo_src': self.srcs['geo'],
                'vote_data': self.vote,
                'heatmap_type_wdg': self.wdgs['heatmap_type'],
                'heatmap_type_items': self.heatmap_type_items,
                'map_select': self.wdgs['map_select'],
                'plot': p_map,
                },
            code = callback_js_code.map_info_js_cb_code
            )
        p_map.select(name = 'hover')[0].callback = hover_map_cb

        hover_histogram_cb = CustomJS(
            code = callback_js_code.hover_histogram_js_cb_code
            )
        p_histogram = self.p_histogram.plot
        hover_histogram = p_histogram.select(name = 'hover_histogram')[0]
        hover_histogram.callback = hover_histogram_cb

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

