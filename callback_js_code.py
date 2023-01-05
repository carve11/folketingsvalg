# callback_js_code.py

mapper_js_cb_code = '''
  const val = Math.round(cb_obj.value*100)/100;
  mapper.high = val;
  mapper.palette = palette[Math.max(10, Math.trunc(val*100))];
'''

map_select_js_cb_code = '''
  // Map select drop down callback JS code. 
  // Based on selected value and the chosen option in radio group widget
  // data source and color mapper are updated for patch glyph.
  const heatmap_type = heatmap_type_items[heatmap_type_wdg.active]['type'];
  const geo_data = geo_src.data;
  const patch_glyph = plot.select(name = 'patch_glyph')[0];
  const color_bar = plot.select(name = 'color_bar')[0];
  const lgnd1 = plot.select(name = 'legend1')[0];
  const lgnd2 = plot.select(name = 'legend2')[0];
  const factor_cmap = color_mapper['factorcmap'];
  var title_txt = [];
  var main_title = '';
  var sub_title = '';
  
  if (heatmap_type == 'diff') {
    const years = heatmap_type_items[heatmap_type_wdg.active]['year'];
    const party_idx = vote_data[years[0]]['parties']['parties'].indexOf(map_select.value);
    const short_name = vote_data[years[0]]['parties']['short_name'][party_idx];
    geo_data['value'] = voteFrac2geoArrDiff(geo_data, vote_data, map_select.value, years);
    main_title += short_name + ' - ' + heatmap_type_wdg.labels[heatmap_type_wdg.active];
    sub_title += 'Ændring i procentpoint per opstillingskreds';
    party_select_div.text = mapSelectPartyDiffTxt(years, vote_data, map_select.value, geo_data);
    color_bar.color_mapper = color_mapper['diff_map'];
    color_bar.formatter.format = '0';
    patch_glyph.glyph.fill_color = {field: 'value', transform: color_mapper['diff_map']};
    geo_src.change.emit();
  }
  if (heatmap_type == 'value') {
    const year = heatmap_type_items[heatmap_type_wdg.active]['year'];
    const party_idx = vote_data[year]['parties']['parties'].indexOf(map_select.value);
    const short_name = vote_data[year]['parties']['short_name'][party_idx];
    const votes_district = vote_data[year]['data']['opstillingskredse'];
    geo_data['value'] = voteFrac2geoArr(geo_data, votes_district, map_select.value);
    main_title += short_name + ' - ' + heatmap_type_wdg.labels[heatmap_type_wdg.active];
    sub_title += 'Stemmeandel (%) per opstillingskreds';
    party_select_div.text = mapSelectPartyTxt(geo_data, vote_data[year]['data'], map_select.value);
    color_bar.color_mapper = color_mapper['votefrac']['mapper'];
    color_bar.formatter.format = '0 %';
    patch_glyph.glyph.fill_color = {field: 'value', transform: color_mapper['votefrac']['mapper']};
    geo_src.change.emit();
  }
  if (heatmap_type == 'district') {
    main_title += map_select.value + ' - opdelt i opstillingskredse';
    party_select_div.text = '';
    const items = district_items[map_select.value];
    const field = district_mapping[map_select.value];
    const transform = color_mapper['district'];
    transform.factors = items;
    patch_glyph.glyph.fill_color = {field: field, transform: transform};
    factor_cmap.palette = color_mapper['district'].palette;
    factor_cmap.factors = items;
    updateGlyphFillColor(plot, 'r_fake1', factor_cmap);
    updateGlyphFillColor(plot, 'r_fake2', factor_cmap);
    mapSelectDistrictSrc(items, fake1_src, fake2_src, fake_coord);
    mapLegendRows(lgnd1, lgnd2, items);
  }
  if (heatmap_type == 'voters_density') {
    main_title += map_select.value + ' - opdelt i opstillingskredse';
    sub_title += 'Antal stemmeberettigede per km²';
    party_select_div.text = '';
    const items = heatmap_type_items[heatmap_type_wdg.active]['lgnd_labels'];
    const transform = color_mapper['voters_density'];
    patch_glyph.glyph.fill_color = {field: 'value', transform: transform};
    factor_cmap.palette = color_mapper['voters_density'].palette;
    factor_cmap.factors = items;
    updateGlyphFillColor(plot, 'r_fake1', factor_cmap);
    updateGlyphFillColor(plot, 'r_fake2', factor_cmap);
    mapSelectDistrictSrc(items, fake1_src, fake2_src, fake_coord);
    mapLegendRows(lgnd1, lgnd2, items);
    const year = parseInt(map_select.value.split(' ')[1]);
    const votes_district = vote_data[year]['data']['opstillingskredse'];
    const bins = heatmap_type_items[heatmap_type_wdg.active]['bins'];
    geo_data['value'] = voteDens2geoArr(geo_data, votes_district, bins);
    geo_src.change.emit();
  }
  mapTitle([main_title, sub_title]);
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
    r.x = plot.inner_width - 215;
    r.y = plot.inner_height - 5;
    txt += 'Region: ' + geo_data['regionsnavn'][idx] + '\\n';
    txt += 'Storkreds: ' + geo_data['storkredsnavn'][idx] + '\\n';
    txt += 'Kommune: ' + geo_data['kredskommunenavn'][idx] + '\\n';
    txt += 'Opstillingskreds: ' + district + '\\n';
    const heatmap_type = heatmap_type_items[heatmap_type_wdg.active]['type'];
    if (heatmap_type == 'value') {
      const year = heatmap_type_items[heatmap_type_wdg.active]['year'];
      txt += votesDistrictTxt(year, vote_data, map_select.value, district_type, district);
    }
    if (heatmap_type == 'diff') {
      const years = heatmap_type_items[heatmap_type_wdg.active]['year'];
      txt += votesDistrictDiffTxt(years, vote_data, map_select.value, district_type, district);
    }
    if (heatmap_type == 'voters_density') {
      const year = parseInt(map_select.value.split(' ')[1]);
      txt += voteDensTxt(year, vote_data, district);
    }
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
    mapper_slider.visible = false;
    color_bar.visible = false;
  }
  if ((heatmap_type == 'value') || (heatmap_type == 'diff')) {
    color_bar.visible = true;
    mapper_slider.visible = heatmap_type == 'value';
    lgnd1.visible = false;
    lgnd2.visible = false;
  }
  map_select.options = heatmap_type_items[this.active]['options'];
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