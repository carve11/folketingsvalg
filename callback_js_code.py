# callback_js_code.py

mapper_js_cb_code = '''
  const val = Math.round(cb_obj.value*100)/100;
  mapper.high = val;
  mapper.palette = palette[Math.max(10, Math.trunc(val*100))];
'''

map_select_js_cb_code = '''
  const heatmap_type = heatmap_type_items[heatmap_type_wdg.active]['type'];
  const geo_data = geo_src.data;
  const patch_glyph = plot.select(name = 'patch_glyph')[0];
  const color_bar = plot.select(name = 'color_bar')[0];
  const lgnd1 = plot.select(name = 'legend1')[0];
  const lgnd2 = plot.select(name = 'legend2')[0];
  var title_txt = [];
  var main_title = '';
  var sub_title = '';
  
  if (heatmap_type == 'diff') {
    const years = heatmap_type_items[heatmap_type_wdg.active]['year'];
    const party_idx = map_select.options.indexOf(map_select.value);
    const short_name = vote_data[years[0]]['parties']['short_name'][party_idx];
    geo_data['value'] = resultDiff(vote_data, map_select.value, years);
    main_title += short_name + ' - ' + heatmap_type_wdg.labels[heatmap_type_wdg.active];
    sub_title += 'Ændring i procentpoint per opstillingskreds';
    party_select_div.text = mapSelectPartyDiffTxt(years, vote_data, map_select.value, geo_data);
    geo_src.change.emit();
  }
  if (heatmap_type == 'value') {
    const year = heatmap_type_items[heatmap_type_wdg.active]['year'];
    const party_idx = map_select.options.indexOf(map_select.value);
    const short_name = vote_data[year]['parties']['short_name'][party_idx];
    main_title += short_name + ' - ' + heatmap_type_wdg.labels[heatmap_type_wdg.active];
    sub_title += 'Stemmeandel (%) per opstillingskreds';
    party_select_div.text = mapSelectPartyTxt(vote_data[year]['data'], map_select.value);
    const votes_district = vote_data[year]['data']['opstillingskredse'];
    const party_vote_frac = votes_district[map_select.value]['VoteFrac'];
    geo_data['value'] = party_vote_frac;
    geo_src.change.emit();
  }
  if (heatmap_type == 'district') {
    main_title += map_select.value + ' - opdelt i opstillingskredse';
    const items = district_items[map_select.value];
    factor_cmap.transform.factors = items;
    updateGlyphFillColor(plot, 'r_fake1', factor_cmap);
    updateGlyphFillColor(plot, 'r_fake2', factor_cmap);
    mapSelectDistrictSrc(items, fake1_src, fake2_src, fake_coord);
    
    lgnd1.visible = true;
    if (items.length > 5) {
      lgnd1.margin = 0;
      lgnd2.visible = true;
    } else {
      lgnd1.margin = 15;
      lgnd2.visible = false;
    }
    party_select_div.text = '';
    var field = district_mapping[map_select.value];
    const transform = factor_cmap.transform;
    patch_glyph.glyph.fill_color = {field: field, transform: transform};
  }
  mapTitle([main_title, sub_title]);
'''

map_info_js_cb_code = '''
  const idx = geo_src.inspected.indices;
  const geo_data = geo_src.data;
  var txt = '';
  var r = plot.select(name = 'map_text')[0];

  if (idx.length > 0) {
    r.x = plot.inner_width - 215;
    r.y = plot.inner_height - 5;
    txt += 'Region: ' + geo_data['regionsnavn'][idx] + '\\n';
    txt += 'Storkreds: ' + geo_data['storkredsnavn'][idx] + '\\n';
    txt += 'Kommune: ' + geo_data['kredskommunenavn'][idx] + '\\n';
    txt += 'Opstillingskreds: ' + geo_data['navn'][idx] + '\\n';
    const heatmap_type = heatmap_type_items[heatmap_type_wdg.active]['type'];
    if (heatmap_type == 'value') {
      const year = heatmap_type_items[heatmap_type_wdg.active]['year'];
      txt += votesDistrictTxt(year, vote_data, map_select.value, geo_data['navn'][idx]);
    }
    if (heatmap_type == 'diff') {
      const years = heatmap_type_items[heatmap_type_wdg.active]['year'];
      const txt_items = votesDistrictDiffTxt(years, vote_data, map_select.value, geo_data['navn'][idx]);
      txt += diffDistrictTxt(txt_items, 'no_bullet');
    }
    r.visible = true;
  } else {
    r.visible = false;
  }
  r.text = txt;
'''

heatmap_type_js_cb_code = '''
  const heatmap_type = heatmap_type_items[this.active]['type'];
  const patch_glyph = plot.select(name = 'patch_glyph')[0];
  const color_bar = plot.select(name = 'color_bar')[0];
  const lgnd1 = plot.select(name = 'legend1')[0];
  const lgnd2 = plot.select(name = 'legend2')[0];

  if (heatmap_type == 'district') {
    mapper_slider.visible = false;
    color_bar.visible = false;
  }
  if (heatmap_type == 'value') {
    color_bar.visible = true;
    mapper_slider.visible = true;
    const transform = value_mapper;
    color_bar.color_mapper = transform;
    color_bar.formatter.format = '0 %';
    patch_glyph.glyph.fill_color = {field: 'value', transform: transform};
    lgnd1.visible = false;
    lgnd2.visible = false;
  }
  if (heatmap_type == 'diff') {
    color_bar.visible = true;
    lgnd1.visible = false;
    lgnd2.visible = false;
    mapper_slider.visible = false;
    color_bar.color_mapper = diff_mapper;
    color_bar.formatter.format = '0';
    patch_glyph.glyph.fill_color = {field: 'value', transform: diff_mapper};
  }
  map_select.options = heatmap_type_items[this.active]['options'];
  if (map_select.options.includes(map_select.value)) {
    let map_select_script = window.Bokeh.documents[0].get_model_by_name('map_select_script');
    map_select_script.execute();
  } else {
    map_select.value = map_select.options[0];
  }
'''