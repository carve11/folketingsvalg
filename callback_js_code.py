# callback_js_code.py

map_select_js_cb_code = '''
  // Map select drop down callback JS code. 
  // Based on selected value and the chosen option in radio group widget
  // data source and color mapper are updated for patch glyph.
  const heatmap_type = heatmap_type_items[heatmap_type_wdg.active]['type'];
  const geo_data = geo_src.data;
  const patch_glyph = plot.select(name = 'patch_glyph')[0];
  const color_bar = plot.select(name = 'color_bar')[0];
  const factor_cmap = color_mapper['factorcmap'];

  if (heatmap_type == 'diff') {
    const years = heatmap_type_items[heatmap_type_wdg.active]['year'];
    const party_idx = vote_data[years[0]]['parties']['parties'].indexOf(map_select.value);
    const short_name = vote_data[years[0]]['parties']['short_name'][party_idx];
    geo_data['value'] = voteFrac2geoArrDiff(geo_data, vote_data, map_select.value, years);
    mapSelectPartyDiffTxt(years, vote_data, map_select.value, geo_data);
    updateColorbar(color_bar, color_mapper['diff_map'], 1);
    patch_glyph.glyph.fill_color = {field: 'value', transform: color_mapper['diff_map']};
    geo_src.change.emit();
  }
  if (heatmap_type == 'value') {
    const year = heatmap_type_items[heatmap_type_wdg.active]['year'];
    const party_idx = vote_data[year]['parties']['parties'].indexOf(map_select.value);
    const short_name = vote_data[year]['parties']['short_name'][party_idx];
    const votes_district = vote_data[year]['data']['opstillingskredse'];
    geo_data['value'] = voteFrac2geoArr(geo_data, votes_district, map_select.value);
    mapSelectPartyTxt(geo_data, vote_data[year]['data'], map_select.value);
    partyVoteShareMapper(vote_data, map_select.value, color_mapper['votefrac']['mapper'], color_mapper['votefrac']['whole_palette']);
    updateColorbar(color_bar, color_mapper['votefrac']['mapper'], 100);
    patch_glyph.glyph.fill_color = {field: 'value', transform: color_mapper['votefrac']['mapper']};
    geo_src.change.emit();
  }
  if (heatmap_type == 'district') {
    party_select_div.text = '';
    const options_idx = map_select.options.indexOf(map_select.value);
    const val = Object.keys(district_mapping)[options_idx];
    const items = district_items[val];
    const field = district_mapping[val];
    const transform = color_mapper['district'];
    transform.factors = items;
    patch_glyph.glyph.fill_color = {field: field, transform: transform};
    factor_cmap.palette = color_mapper['district'].palette;
    updateFakeSrcLegends(factor_cmap, items, plot, fake_coord, heatmap_type);
  }
  if (heatmap_type == 'voters_density') {
    party_select_div.text = '';
    var items = heatmap_type_items[heatmap_type_wdg.active]['lgnd_labels'];
    const transform = color_mapper['voters_density'];
    patch_glyph.glyph.fill_color = {field: 'value', transform: transform};
    factor_cmap.palette = color_mapper['voters_density'].palette;
    updateFakeSrcLegends(factor_cmap, items, plot, fake_coord, heatmap_type);
    const options_idx = map_select.options.indexOf(map_select.value);
    const year = map_select.tags[options_idx]['i18n-val']['str']['str'];
    const votes_district = vote_data[year]['data']['opstillingskredse'];
    const bins = heatmap_type_items[heatmap_type_wdg.active]['bins'];
    geo_data['value'] = voteDens2geoArr(geo_data, votes_district, bins);
    geo_src.change.emit();
  }
  mapTitle(heatmap_type, heatmap_type_wdg, map_select);
'''

map_info_js_cb_code = '''
  // Map hover callback JS code. 
  // Based on map patch glyph index show information in the map
  const idx = geo_src.inspected.indices;
  const geo_data = geo_src.data;
  const district_type = 'opstillingskredse';
  var txt = '';
  var r = plot.select(name = 'map_text')[0];

  if (idx.length > 0) {
    var idx_common = [];
    const district = geo_data['navn'][idx];
    var idx_new = geo_data['navn'].indexOf(district);
    while (idx_new !== -1) {
      idx_common.push(idx_new);
      idx_new = geo_data['navn'].indexOf(district, idx_new + 1);
    }
    geo_src.inspected.indices = idx_common;
    geo_src.change.emit();
    r.x = plot.inner_width - 225;
    r.y = plot.inner_height - 5;
    const heatmap_items = heatmap_type_items[heatmap_type_wdg.active];
    txt += hoverInfoDistrictTxt(idx, geo_data, district);
    txt += hoverInfoAddTxt(district, heatmap_items, vote_data, map_select, district_type)

    r.visible = true;
  } else {
    r.visible = false;
  }
  r.text = txt;
'''

heatmap_type_js_cb_code = '''
  // Radiogrp widget callback JS code. 
  // Based on option clicked prepare which map elements to show
  // and update select widget options and value
  const heatmap_type = heatmap_type_items[this.active]['type'];
  const color_bar = plot.select(name = 'color_bar')[0];
  const lgnd1 = plot.select(name = 'legend1')[0];
  const lgnd2 = plot.select(name = 'legend2')[0];

  if ((heatmap_type == 'district') || (heatmap_type == 'voters_density')) {
    color_bar.visible = false;
  }
  if ((heatmap_type == 'value') || (heatmap_type == 'diff')) {
    color_bar.visible = true;
    lgnd1.visible = false;
    lgnd2.visible = false;
  }
  map_select.options = heatmap_type_items[this.active]['options'];
  map_select.tags = heatmap_type_items[this.active]['tags'];

  if (map_select.tags.length > 0) {
    translateBokehWidgetItems(map_select);
  }
  var options = map_select.options;
  if (Array.isArray(options[0])) {
    options = [];
    map_select.options.forEach((item) => {
      options.push(item[0]);
    });
  }
  if (options.includes(map_select.value)) {
    let map_select_script = window.Bokeh.documents[0].get_model_by_name('map_select_script');
    map_select_script.execute();
  } else {
    map_select.value = options[0];
  }
'''

hover_histogram_js_cb_code = '''
  const count_txt = replaceTemplate("count");
  const interval_txt = replaceTemplate("interval");
  const tooltip = `
    <div>
     <span>${count_txt}</span>: @count<br>
     <span>${interval_txt}</span>: @bin_txt
    </div>`
    this.tooltips = tooltip;
'''