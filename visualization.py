# visualization.py
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, ColumnDataSource
from bokeh.models import LinearColorMapper, CategoricalColorMapper
from bokeh.models import Legend, LegendItem, HoverTool, Label, FixedTicker
from bokeh.models import ColorBar, NumeralTickFormatter, FuncTickFormatter
from bokeh.models import Select, Div, RadioGroup, Span
from bokeh.palettes import d3, viridis, linear_palette, Reds3, Blues3
from bokeh.transform import factor_cmap, linear_cmap, dodge, transform
from bokeh.core.properties import value
from bokeh.layouts import gridplot, row, column
from matplotlib import cm as mp_cm, colors as mp_colors
import config
import numpy as np

INIT_MAPPER_HIGH = 0.4
INIT_PALETTE_SIZE = round(INIT_MAPPER_HIGH*100)
RADIO_WDG_MARGIN = (5, 10, 5, 15)
WDG_MARGIN = (5, 10, 5, 10)
WDG_MIN_WIDTH = 280

class Map:
    '''
    Map of districts
    '''
    def __init__(self, srcs):
        self.srcs = srcs
        self.mapper = color_mappers()
        self.plot = self.map_figure()

    def map_figure(self):
        self.p = figure(
            plot_width = config.MAP_WIDTH,
            plot_height = config.MAP_HEIGHT,
            x_axis_type = 'mercator',
            y_axis_type = 'mercator',
            match_aspect = True,
            tools = 'pan,wheel_zoom,reset',
            active_scroll = 'wheel_zoom',
            name = 'map'
            )
        self.p.grid.grid_line_color = None
        self.p.axis.visible = False
        self.p.toolbar.autohide = False
        self.p.outline_line_color = None
        self.p.min_border_right = 35
        self.p.toolbar.logo = None

        self.add_glyphs()
        self.color_bar()
        self.map_text()

        return self.p

    def add_glyphs(self):
        fill_color = {
            'field': 'value',
            'transform': self.mapper['votefrac']['mapper']
            }

        r_patch = self.p.patches(
            xs = 'xs',
            ys = 'ys',
            fill_color = fill_color,
            fill_alpha = 0.7,
            line_color = 'white',
            line_width = 0.5,
            hover_line_color = 'firebrick',
            hover_line_width = 1,
            hover_fill_color = 'orange',
            hover_fill_alpha = 1,
            source = self.srcs['geo'],
            name = 'patch_glyph',
            )

        hover = HoverTool(
            tooltips = None, 
            renderers = [r_patch],
            name = 'hover',
            toggleable = False
            )

        self.p.add_tools(hover)

        r_fake1 = rect_glyph(
            self.p,
            self.srcs['map_fake1'],
            self.mapper['district'],
            'r_fake1'
            )
        r_fake2 = rect_glyph(
            self.p,
            self.srcs['map_fake2'],
            self.mapper['district'],
            'r_fake2'
            )

        add_legend(self.p, r_fake1, 0, 'legend1')
        add_legend(self.p, r_fake2, 5, 'legend2')

    def color_bar(self):
        color_bar = ColorBar(
            color_mapper = self.mapper['votefrac']['mapper'],
            label_standoff = 4,
            orientation = 'horizontal',
            height = 10,
            width = config.MAP_WIDTH - 70,
            major_label_text_font_size = config.MAP_FONT_SIZE,
            major_label_text_font = config.MAP_FONT,
            ticker = FixedTicker(ticks=[0, 0.5]),
            name = 'color_bar',
            visible = False
            )
        color_bar.formatter = FuncTickFormatter(
            code = '''
            if (ticks[0] >= 0) {
              var digits = 0;
              const diff = ticks[ticks.length-1] - ticks[0];
              if (diff <= 0.05) digits = 1;
              if (diff <= 0.01) digits = 2;
              return pctTicker(tick, digits);
            } else {
              return formatAsIntl({num: tick, digits: 0});
            }'''
        )
        self.p.add_layout(color_bar, 'below')

    def map_text(self):
        label = Label(
            x = config.MAP_WIDTH - 215,
            y = config.MAP_HEIGHT - 40,
            x_units = 'screen',
            y_units = 'screen',
            text = '',
            border_line_color = None,
            background_fill_color = 'white',
            background_fill_alpha = 0.6,
            text_font_size = config.MAP_FONT_SIZE,
            text_baseline = 'top',
            text_font = config.MAP_FONT,
            name = 'map_text',
            visible = False,
            render_mode = 'css'
            )
        self.p.add_layout(label)

class ElectionBarCharts:
    '''
    2 side-by-side horizontal bar charts. Left chart shows party election
    results for 2 elections, and the chart to the right shows the difference
    between those 2 elections.
    Assume the source has been sorted correctly by plot_cols[0]
    '''
    def __init__(self, src, plot_cols, y_cat):
        self.src = src
        self.plot_cols = sorted(plot_cols, reverse = True)
        self.y_cat = y_cat
        self.plots = self.charts()

    def charts(self):
        self.df = self.src.to_df()
        self.y_plot_cat = self.df.loc[
            self.df[str(self.plot_cols[0])]>0, self.y_cat
            ]
        
        return row(
            children = [self.bar_chart(), self.diff_chart()],
            name = 'charts_election_results'
            )

    def bar_chart(self):
        '''
        Horizontal bar chart with value labels at bars.
        '''
        plot = figure(
            plot_width = 500,
            plot_height = 600,
            y_range = self.y_plot_cat,
            tools = '',
            toolbar_location = None,
            name = 'election_results'
            )

        plot_styling(plot, xgrid = False, ygrid = False, y_major_tick = False)
        plot.min_border_right = 15
        plot.xaxis[0].formatter = NumeralTickFormatter(format = "0 %")
        plot.x_range.start = 0
        plot.xaxis.visible = False
        max_val = self.df[[str(self.plot_cols[0]), str(self.plot_cols[1])]].max()
        plot.x_range.end = (int(max_val.max()*100/5)+2)/100*5
        
        self.add_result_glyphs(plot)
        plot.legend.location = 'center_right'
        plot.legend.border_line_color = None

        return plot

    def add_result_glyphs(self, plot):
        p_data = {
            self.plot_cols[0]: {},
            self.plot_cols[1]: {},
        }
        p_data[self.plot_cols[0]]['offset'] = 0.2
        p_data[self.plot_cols[0]]['color'] = 'navy'

        p_data[self.plot_cols[1]]['offset'] = -0.2
        p_data[self.plot_cols[1]]['color'] = 'olive'

        for year in self.plot_cols:
            y = dodge(self.y_cat, p_data[year]['offset'], range = plot.y_range)
            plot.hbar(
                y = y,
                right = str(year),
                left = 0,
                source = self.src,
                height = 0.38,
                fill_color = p_data[year]['color'],
                fill_alpha = 0.5,
                line_color = 'white',
                legend_label = str(year)
                )

            plot.text(
                y = y,
                x = str(year),
                text = f'{year}_label',
                source = self.src,
                text_font_size = '12px',
                text_baseline = 'middle',
                text_font = value(config.MAP_FONT),
                x_offset = 2
                )

    def diff_chart(self):
        '''
        Horizontal bar diff chart with labels
        '''
        plot = figure(
            width = 300,
            height = 600,
            y_range = self.y_plot_cat,
            tools = '',
            toolbar_location = None,
        )
        plot.title.align = 'center'
        plot_styling(plot, xgrid = False, ygrid = False, y_major_tick = False)
        plot.x_range.range_padding = 0.3
        plot.min_border_left = 15
        plot.yaxis.visible = False
        plot.xaxis.visible = False
        self.add_diff_glyph(plot)

        return plot

    def add_diff_glyph(self, plot):
        mapper = LinearColorMapper(
            palette = [Reds3[0], Blues3[0]], low = 0, high = 0
            )

        diff_col = f'{self.plot_cols[0]}-{self.plot_cols[1]}'
        plot.hbar(
            y = self.y_cat,
            right = diff_col,
            left = 0,
            source = self.src,
            height = 0.6,
            color = transform(diff_col, mapper),
            alpha = 1.0
            )
        plot.text(
            y = self.y_cat,
            x = diff_col,
            text = f'{diff_col}_label',
            source = self.src,
            text_font_size = '12px',
            text_font = value(config.MAP_FONT),
            text_baseline = 'middle',
            text_align = f'{diff_col}_align',
            x_offset = f'{diff_col}_offset'
            )

        zero_line = Span(
            location = 0,
            dimension = 'height',
            line_color = 'lightgrey',
            line_width = 0.5
            )
        plot.add_layout(zero_line)

class HistogramChart:
    '''
    Plot histogram barchart
    '''
    def __init__(
            self,
            src,
            x_label = None,
            y_label = None,
            xlog_scale = False):
        self.src = src
        self.xlog_scale = xlog_scale
        self.x_label = x_label
        self.y_label = y_label
        self.plot = self.chart()

    def chart(self):
        x_axis_type = 'linear'
        
        if self.xlog_scale:
            x_axis_type = 'log'

        plot = figure(
            width = 500,
            height = 250,
            tools = '',
            toolbar_location = None,
            x_axis_type = x_axis_type,
            margin = WDG_MARGIN,
            name = 'hist_voters_density'
        )

        plot.xaxis.axis_label = self.x_label
        plot.yaxis.axis_label = self.y_label
        plot.xaxis.name = 'hist_voters_density_xaxis'
        plot.yaxis.name = 'hist_voters_density_yaxis'

        plot.y_range.start = 0

        plot.yaxis.formatter = FuncTickFormatter(
            code = '''
              return formatAsIntl({num: tick, digits: 2});
            '''
        )

        plot_styling(plot)
        self.add_glyph(plot)

        return plot
        
    def add_glyph(self, plot):
        r_hist = plot.quad(
            top = 'hist',
            bottom = 0,
            left = 'left_edge',
            right = 'right_edge',
            fill_color = 'orange',
            line_color = 'white',
            fill_alpha = 0.7,
            source = self.src
            )

        hover = HoverTool(
            tooltips = [
                ('Antal', '@count'),
                ('Interval', '@bin_txt')
            ],
            renderers = [r_hist],
            name = 'hover_histogram',
            )

        plot.add_tools(hover)

class PartyDensityGridPlot:
    '''
    Grid layout of one chart per party showing election results per district
    for 2 elections.
    '''
    def __init__(self, vote_data, years):
        self.data = vote_data
        self.plot = self.grid(years)

    def grid(self, years):
        plots = []
        plot_cols = 3
        markers = {
            years[0]: {
            'marker': 'circle',
            'color': 'navy',
            'alpha': 0.5
            },
            years[1]: {
            'marker': 'square',
            'color': 'olive',
            'alpha': 0.5
            }
        }

        parties = self.data[years[0]]['parties']['parties']
        
        for i, party in enumerate(parties):
            p = figure(
                width = 240,
                height = 200,
                min_border = 5,
                y_axis_type = 'log',
                tools = '',
                toolbar_location = None
                )

            p.min_border_right = 10
            p.min_border_left = 10
            if i % plot_cols == 0:
                p.min_border_left = 40
            else:
                p.yaxis.visible = False

            p.width += p.min_border_left + p.min_border_right
            label_x = p.width-p.min_border_left-p.min_border_right-5

            for year in years[::-1]:
                if party not in self.data[year]['parties']['parties']:
                    continue

                y = self.data[year]['data']['opstillingskredse']['voters_density']
                x = self.data[year]['data']['opstillingskredse'][party]['VoteFrac']
                p.scatter(
                    x = x, y = y, 
                    marker = markers[year]['marker'],
                    color = markers[year]['color'],
                    alpha = markers[year]['alpha']
                )
                
            label = Label(
                text = self.data[years[0]]['parties']['short_name'][i],
                x = label_x, x_units = 'screen',
                y = 150, y_units = 'screen',
                text_align = 'right',
                text_font_size = '12px',
                text_font = config.MAP_FONT,
                render_mode = 'css'
            )
            p.add_layout(label)
            
            plot_styling(p)
            
            p.axis.major_label_text_font_size = '13px'
            p.axis.axis_line_color = None
            p.background_fill_color = '#efefef'
            p.xaxis[0].formatter = NumeralTickFormatter(format = "0 %")
            p.xaxis.ticker.desired_num_ticks = 5
            p.x_range.range_padding = 0.2
            p.y_range.update(start = 7, end = 35000)

            plots.append(p)

        gp = gridplot(plots, ncols = plot_cols, toolbar_location = None)

        grid_width = sum(plots[i].width for i in range(plot_cols))
        legend = dummy_legend_fig(grid_width, markers)
        layout = column(gp, legend, name = 'voters_density_grid')

        return layout


def plot_styling(plot, xgrid = True, ygrid = True, y_major_tick = True):
    plot.axis.major_label_text_font_size = '14px'
    plot.axis.axis_label_text_font_style = 'normal'
    plot.outline_line_color = None
    plot.xaxis.minor_tick_line_color = None
    plot.xaxis.major_tick_in = 0
    plot.yaxis.minor_tick_line_color = None
    plot.axis.major_tick_line_color = 'lightgrey'
    plot.axis.axis_line_color = 'lightgrey'
    plot.ygrid.grid_line_color = 'lightgrey'
    plot.xgrid.grid_line_color = 'lightgrey'

    if not y_major_tick:
        plot.yaxis.major_tick_line_color = None

    if not xgrid:
        plot.xgrid.grid_line_color = None

    if not ygrid:
        plot.ygrid.grid_line_color = None

def palettes():
    red256 = [mp_colors.to_hex(x) for x in mp_cm.Reds(np.arange(256) / 255)]
    red10 = linear_palette(red256, 11)[1:]
    blue256 = [mp_colors.to_hex(x) for x in mp_cm.Blues(np.arange(256) / 255)]
    blue10 = linear_palette(blue256, 11)[1:]

    blue_red = blue10[::-1] + red10

    pal_dict = {i: linear_palette(red256, i+1)[1:] for i in [4,5,6,7,8,9]}
    pal_dict.update({i: linear_palette(red256, i+1)[1:] for i in range(10,75,5)})

    return {'blue_red': blue_red, 'red256': red256, 'pal_dict': pal_dict}

def color_mappers():
    color_pal = palettes()

    diff_mapper = LinearColorMapper(
        palette = color_pal['blue_red'],
        low = -10,
        high = 10
        )

    votefrac_mapper = LinearColorMapper(
        palette = color_pal['pal_dict'][INIT_PALETTE_SIZE],
        low = 0,
        high = INIT_MAPPER_HIGH
        )

    district_mapper = CategoricalColorMapper(
        factors = [],
        palette = d3['Category20'][10]
    )

    voters_density = LinearColorMapper(
        palette = linear_palette(color_pal['red256'], 6)[1:],
        low = 0,
        high = 4
    )

    factorcmap = CategoricalColorMapper(
        palette = d3['Category20'][10],
        factors = [],
        name = 'factorcmap'
        )

    return {
        'district': district_mapper,
        'votefrac': {
            'mapper': votefrac_mapper,
            'whole_palette': color_pal['pal_dict']
            },
        'diff_map': diff_mapper,
        'voters_density': voters_density,
        'factorcmap': factorcmap
        }

def create_sources():
    sources = {}
    sources['geo'] = GeoJSONDataSource()

    sources['map_fake1'] = ColumnDataSource(
        data = {'x': [], 'y': [], 'legend': [], 'value': []},
        name = 'map_fake1_src'
        )
    sources['map_fake2'] = ColumnDataSource(
        data = {'x': [], 'y': [], 'legend': [], 'value': []},
        name = 'map_fake2_src'
        )

    sources['election_results'] = ColumnDataSource(name = 'src_results')
    sources['hist_voters_density'] = ColumnDataSource()
    sources['voters_density_grid'] = ColumnDataSource()

    return sources

def rect_glyph(plot, source, mapper, name):
    r = plot.rect(
        x = 'x',
        y = 'y',
        width = 1,
        height = 1,
        width_units = 'screen',
        height_units = 'screen',
        fill_color = {'field': 'value', 'transform': mapper},
        fill_alpha = 0.7,
        line_color = None,
        visible = False,
        name = name,
        source = source
        )

    return r

def add_legend(plot, renderer, margin, name):
    legend = Legend(
        items = [
            LegendItem(
                label = {'field': 'legend'},
                renderers = [renderer]
                )
            ],
        location = 'center',
        border_line_color = None,
        margin = margin,
        spacing = 5,
        orientation = 'horizontal',
        label_text_font_size = config.MAP_FONT_SIZE,
        label_text_font = config.MAP_FONT,
        name = name
        )
    plot.add_layout(legend, 'below')

def widgets(heatmap_type, tags):
    labels = [v['label'] for k,v in heatmap_type.items()]
    heatmap_type_active = 0
    options = heatmap_type[heatmap_type_active]['options']
    
    heatmap_type_wdg = RadioGroup(
        labels = labels,
        margin = RADIO_WDG_MARGIN,
        min_width = WDG_MIN_WIDTH,
        name = 'heatmap_type'
        )
    heatmap_type_wdg.tags = tags['l']

    map_select = Select(
        options = options,
        value = options[0],
        margin = WDG_MARGIN,
        min_width = WDG_MIN_WIDTH-WDG_MARGIN[1]-WDG_MARGIN[3],
        sizing_mode = 'stretch_width',
        name = 'map_select'
        )

    select_div = Div(
        text = '<div class="div-text">test</div>',
        margin = WDG_MARGIN,
        min_width = WDG_MIN_WIDTH-WDG_MARGIN[1]-WDG_MARGIN[3],
        sizing_mode = 'stretch_width',
        name = 'map_info'
        )

    return {
        'map_select': map_select,
        'select_div': select_div,
        'heatmap_type': heatmap_type_wdg
        }

def dummy_legend_fig(width, markers):
    '''
    In order to have legend outside grid layout a dummy figure is created
    and added to the layout.
    '''
    dummy_fig = figure(
        width = width,
        height = 50,
        toolbar_location = None,
        tools = ''
        )
    legend_items = []
    for key, value in markers.items():
        r = dummy_fig.scatter(
            x = [1], y = [1],
            size = 10,
            marker = value['marker'],
            color = value['color'],
            alpha = value['alpha'],
            visible = False
            )
        legend_items.append(LegendItem(label = str(key), renderers = [r]))

    legend = Legend(
        items = legend_items,
        orientation = 'horizontal',
        border_line_color = None,
        location = 'bottom_center',
        label_text_font_size = '13px'
    )

    dummy_fig.add_layout(legend)
    dummy_fig.axis.visible = False
    dummy_fig.grid.visible = False
    dummy_fig.outline_line_width = 0

    return dummy_fig
