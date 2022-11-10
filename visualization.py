# visualization.py
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, ColumnDataSource
from bokeh.models import LinearColorMapper, CategoricalColorMapper
from bokeh.models import Legend, LegendItem, HoverTool, Label
from bokeh.models import ColorBar, NumeralTickFormatter
from bokeh.models import Select, Slider, Div, RadioGroup
from bokeh.palettes import d3, viridis, diverging_palette, linear_palette
from bokeh.transform import factor_cmap, linear_cmap
from matplotlib import cm as mp_cm, colors as mp_colors
import config
import numpy as np

INIT_MAPPER_HIGH = 0.4
INIT_PALETTE_SIZE = round(INIT_MAPPER_HIGH*100)


class Map:
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
        self.p.toolbar.autohide = True
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
            line_color = 'black',
            line_width = 0.5,
            hover_line_color = 'firebrick',
            hover_line_width = 1,
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
            label_standoff = 2,
            formatter = NumeralTickFormatter(format = "0 %"),
            orientation = 'horizontal',
            height = 10,
            width = config.MAP_WIDTH - 70,
            major_label_text_font_size = config.MAP_FONT_SIZE,
            major_label_text_font = config.MAP_FONT,
            name = 'color_bar',
            visible = False
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
            visible = False
            )
        self.p.add_layout(label)


def color_mappers():
    colors_votefrac = {i: viridis(i)[::-1] for i in range(0,105,5)}

    red256 = [mp_colors.to_hex(x) for x in mp_cm.Reds(np.arange(256) / 255)]
    red10 = linear_palette(red256, 10)
    blue256 = [mp_colors.to_hex(x) for x in mp_cm.Blues(np.arange(256) / 255)]
    blue10 = linear_palette(blue256, 10)

    blue_red = blue10[::-1] + red10

    diff_mapper = LinearColorMapper(
        palette = blue_red,
        low = -10,
        high = 10
        )

    votefrac_mapper = LinearColorMapper(
        palette = colors_votefrac[INIT_PALETTE_SIZE],
        low = 0,
        high = INIT_MAPPER_HIGH
        )

    district_mapper = CategoricalColorMapper(
        factors = [],
        palette = d3['Category20'][10]
    )

    return {
        'district': district_mapper,
        'votefrac': {
            'mapper': votefrac_mapper,
            'whole_palette': colors_votefrac
            },
        'diff_map': diff_mapper
        }

def create_sources(gdf):
    sources = {}
    sources['geo'] = GeoJSONDataSource(geojson = gdf.to_json())

    sources['map_fake1'] = ColumnDataSource(
        data = {'x': [], 'y': [], 'legend': []}
        )
    sources['map_fake2'] = ColumnDataSource(
        data = {'x': [], 'y': [], 'legend': []}
        )

    return sources

def rect_glyph(plot, source, mapper, name):
    r = plot.rect(
        x = 'x',
        y = 'y',
        width = 1,
        height = 1,
        width_units = 'screen',
        height_units = 'screen',
        fill_color = {'field': 'legend', 'transform': mapper},
        fill_alpha = 0.7,
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
        orientation = 'horizontal',
        label_text_font_size = config.MAP_FONT_SIZE,
        label_text_font = config.MAP_FONT,
        name = name
        )
    plot.add_layout(legend, 'below')

def widgets(heatmap_type):
    labels = [v['label'] for k,v in heatmap_type.items()]
    heatmap_type_active = 0
    options = heatmap_type[heatmap_type_active]['options']
    
    map_select = Select(
        options = options,
        value = options[0],
        name = 'map_select'
        )

    select_div = Div(
        text = '<div class="div-text">test</div>',
        name = 'map_info'
        )

    mapper_slider = Slider(
        title = 'Maksimum værdi farveskala',
        show_value = False,
        start = 0.05,
        end = 1,
        step = 0.05,
        format = NumeralTickFormatter(format = "0 %"),
        value = 0.4,
        name = 'mapper_slider'
        )

    heatmap_type_wdg = RadioGroup(
        labels = labels,
        name = 'heatmap_type'
        )

    return {
        'map_select': map_select,
        'select_div': select_div,
        'mapper_slider': mapper_slider,
        'heatmap_type': heatmap_type_wdg
        }
