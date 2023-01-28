// functions.js
function formatAsPercent(num) {
  var digits = 1;
  var signi_digi = 3;
  if (num < 0.0995) {
    signi_digi = 2;
  }
  if (num < 0.00995) {
    signi_digi = 1;
  }
  if (num < 0.000995) {
    digits = 2;
  }
  return new Intl.NumberFormat(localeTags[locale], {
    style: 'percent',
    maximumFractionDigits: digits,
    maximumSignificantDigits: signi_digi,
    minimumSignificantDigits: signi_digi,
  }).format(num);
}

function pctTicker(num, digits) {
  var min_signi_digi = 1;

  if (digits == 1) {
    if (num < 0.00995) min_signi_digi = digits;
    else if (num < 0.0995) min_signi_digi += digits;
    else min_signi_digi = 3;
  }
  return new Intl.NumberFormat(localeTags[locale], {
    style: 'percent',
    minimumFractionDigits: digits,
    minimumSignificantDigits: min_signi_digi,
  }).format(num);
}

function formatAsIntl(value) {
  var digits = 1;
  var sign = 'auto';
  const {num, ...options} = value;
  
  if (Object.hasOwn(options, 'digits')) digits = options.digits;
  if (Object.hasOwn(options, 'sign')) sign = options.sign;
  
  var minFracDig = 0;
  if (num < 10) minFracDig = 1;
  if (num < 1) minFracDig = Math.min(digits, 2);
  if (digits == 0) minFracDig = 0;

  return new Intl.NumberFormat(localeTags[locale], {
    style: 'decimal',
    signDisplay: sign,
    minimumFractionDigits: minFracDig,
    maximumFractionDigits: digits,
  }).format(num);
}

function arrayFill(length, value) {
  var array = [];
  for(var i=0; i<length; ++i) array.push(value);
  return array;
}

function valuePcti18nAttr(num, pct_as_frac) {
  return {
    value: {num: num, style: "decimal"},
    pct: {num: pct_as_frac, style: "pct"}
  };
}

function valuei18nAttr(num, options = {}) {
  return {
    value: {num: num, style: "decimal", ...options},
  };
}

function stri18nAttr(str) {
  return {str: `${str}`};
}

function strStri18nAttr(str1, str2) {
  return {
    str1: {str: `${str1}`},
    str2: {str: `${str2}`},
  };
}

function strValPcti18nAttr(str, num, pct_as_frac) {
  return {
    str: {str: `${str}`},
    value: {num: num, style: "decimal"},
    pct: {num: pct_as_frac, style: "pct"}
  };
}

function i18nKeyValue(key, valObj) {
  return `i18n-key="${key}" i18n-val='${JSON.stringify(valObj)}'`;
}

function listPartyResultsNational(vote_data, party) {
  const {votes, votes_frac, votes_total} = votesDistrict(vote_data, party, 'Hele landet');
  const {eligible_voters, eligible_voters_vote} = districtVoteData(vote_data, 'Hele landet');
  const eligible_frac = eligible_voters_vote / eligible_voters;

  var txt = '';
  txt += '<ul class="list">';
  txt += `<li ${i18nKeyValue("votes", valuePcti18nAttr(votes, votes_frac))}'></li>`;
  txt += `<li ${i18nKeyValue("valid_votes", valuei18nAttr(votes_total))}'></li>`;
  txt += `<li ${i18nKeyValue("total_votes", valuePcti18nAttr(eligible_voters_vote, eligible_frac))}'></li>`;
  txt += `<li ${i18nKeyValue("entitled_voters", valuei18nAttr(eligible_voters))}'></li>`;
  txt += '</ul>';

  return txt;
}

function listPartyHighLowDistrict(geo_data, votes_district, party, min_max) {
  const {location, val} = geoDataLocationMinMax(geo_data, min_max);
  const {votes, votes_frac, votes_total} = votesDistrict(votes_district, party, location);

  var txt = '';
  txt += '<ul class="list">';
  txt += `<li ${i18nKeyValue("nomination_district", stri18nAttr(location))}'></li>`;
  txt += `<li ${i18nKeyValue("votes", valuePcti18nAttr(votes, votes_frac))}'></li>`;
  txt += `<li ${i18nKeyValue("valid_votes", valuei18nAttr(votes_total))}'></li>`;
  txt += '</ul>';

  return txt;
}

function mapSelectPartyTxt(geo_data, vote_data, party) {
  var txt = '<div class="bk-div-text">';
  txt += '<span i18n-key="country-result"></span>';
  txt += listPartyResultsNational(vote_data['Land'], party);

  txt += '<span i18n-key="highest-voteshare"></span>';
  txt += listPartyHighLowDistrict(geo_data, vote_data['opstillingskredse'], party, 'max');

  txt += '<span i18n-key="lowest-voteshare"></span>';
  txt += listPartyHighLowDistrict(geo_data, vote_data['opstillingskredse'], party, 'min');
  txt += '</div>';

  updateBokehDivTxt(txt);
}

function updateBokehDivTxt(txt) {
  party_select_div = window.Bokeh.documents[0].get_model_by_name('map_info');
  party_select_div.text = txt;

  const attr_name = attrNames(txt, "i18n-key");
  attr_name.forEach((item) => {
    const elements = document.querySelectorAll(`[i18n-key=${item}]`);
    
    elements.forEach((elm) => {
      updateElementTxt(elm);
    });
  });
}

function attrNames(string, attr_name) {
  const arr = [];
  const re = new RegExp(`${attr_name}="(.*?)"`, "g");
  for (const match of string.matchAll(re)) {
    arr.push(match[1]);
  }
  return arr;
}

function mapSelectPartyDiffTxt(years, vote_data, party, geo_data) {
  var txt = '<div class="bk-div-text">';
  txt += onlyHighLowTxt(geo_data);

  txt += '<span i18n-key="country-result"></span>';
  let diff_data = votesDiffDistrict(years, vote_data, party, 'Land', 'Hele landet');
  txt += listDiffTextNational(years, diff_data);

  var {heading, location} = districtHighDiffTxt(geo_data);
  diff_data = votesDiffDistrict(years, vote_data, party, 'opstillingskredse', location);
  txt += heading;
  txt += listDiffTextDistrict(years, diff_data, location);

  var {heading, location} = districtLowDiffTxt(geo_data);
  diff_data = votesDiffDistrict(years, vote_data, party, 'opstillingskredse', location);
  txt += heading;
  txt += listDiffTextDistrict(years, diff_data, location);

  txt += '</div>';

  updateBokehDivTxt(txt);
}

function onlyHighLowTxt(geo_data) {
  var txt = '';
  var {val} = geoDataLocationMinMax(geo_data, 'min');
  if (val > 0) {
    txt += '<span i18n-key="party-only-increase"></span>';
    txt += '\n';
  }
  var {val} = geoDataLocationMinMax(geo_data, 'max');
  if (val < 0) {
    txt += '<span i18n-key="party-only-setback"></span>';
    txt += '\n';
  }
  return txt;
}

function listDiffTextNational(years, data) {
  var txt = '';
  txt += '<ul class="list">';
  txt += `<li ${i18KeyValPartyNoData(years[0], data)}></li>`;
  txt += `<li ${i18KeyValPartyNoData(years[1], data)}></li>`;
  txt += `<li ${i18nKeyValue("change", valuei18nAttr(data.chg, {sign: 'exceptZero'}))}></li>`;
  txt += '</ul>';

  return txt;
}

function listDiffTextDistrict(years, data, location) {
  var txt = '';
  txt += '<ul class="list">';
  txt += `<li ${i18nKeyValue("nomination_district", stri18nAttr(location))}'></li>`;
  txt += `<li ${i18KeyValPartyNoData(years[0], data)}></li>`;
  txt += `<li ${i18KeyValPartyNoData(years[1], data)}></li>`;
  txt += `<li ${i18nKeyValue("change", valuei18nAttr(data.chg, {sign: 'exceptZero'}))}'></li>`;
  txt += '</ul>';

  return txt;
}

function i18KeyValPartyNoData(year, data) {
  const {key, valObj} = keyValPartyNoData(year, data);
  return i18nKeyValue(key, valObj);
}

function txtLineKeyValPartyNoData(year, data) {
  const {key, valObj} = keyValPartyNoData(year, data);
  return hoverInfoLineTxt(key, valObj);
}

function hoverInfoLineTxt(key, valObj) {
  const txt = replaceTemplate(key, valObj);
  return `${txt}\n`;
}

function keyValPartyNoData(year, data) {
  let key;
  let valObj;

  if (data[year].votes == -999) {
    key = 'new-party-no-data';
    valObj = stri18nAttr(year);
  } else {
    key = 'el-year-votes';
    valObj = strValPcti18nAttr(year, data[year].votes, data[year].votes_frac);
  }
  return {key, valObj}
}

function districtHighDiffTxt(geo_data) {
  const {location, val} = geoDataLocationMinMax(geo_data, 'max');
  var heading = '';
  if (val < 0) {
    heading += '<span i18n-key="smallest-setback"></span>';
  } else {
    heading += '<span i18n-key="largest-increase"></span>';
  }

  return {heading, location};
}

function districtLowDiffTxt(geo_data) {
  const {location, val} = geoDataLocationMinMax(geo_data, 'min');
  var heading = '';
  if (val < 0) {
    heading += '<span i18n-key="largest-setback"></span>';
  } else {
    heading += '<span i18n-key="smallest-increase"></span>';
  }

  return {heading, location};
}

function geoDataLocationMinMax(geo_data, min_max) {
  const values = geo_data['value'];
  var val = 0;
  if (min_max == 'min') {
    val = Math.min(...values);
  } else {
    val = Math.max(...values);
  }
  const location = geo_data['navn'][values.indexOf(val)];
  return {location, val};
}

function voteDensTxt(year, vote_data, district_name) {
  const votes_district = vote_data[year]['data']['opstillingskredse'];
  const idx = votes_district['navn'].indexOf(district_name);
  const entitled_voters = votes_district['Stemmeberettigede'][idx];
  const votes_dens = votes_district['voters_density'][idx];

  var txt = '';
  txt += hoverInfoLineTxt('entitled_voters', valuei18nAttr(entitled_voters));
  txt += hoverInfoLineTxt('voters_density_hover', valuei18nAttr(votes_dens, {digits: 0}));

  return txt;
}

function votesDistrict(vote_data, party, district_name) {
  const idx = vote_data['navn'].indexOf(district_name);
  const votes = vote_data[party]['StemmerAntal'][idx];
  const votes_frac = vote_data[party]['VoteFrac'][idx];
  const votes_total = vote_data['IAltGyldigeStemmer'][idx];
  
  return {votes, votes_frac, votes_total};
}

function districtVoteData(vote_data, district_name) {
  const idx = vote_data['navn'].indexOf(district_name);
  const eligible_voters = vote_data['Stemmeberettigede'][idx];
  const eligible_voters_vote = vote_data['IAltAfgivneStemmer'][idx];

  return {eligible_voters, eligible_voters_vote};
}

function votesDistrictTxt(year, vote_data, party, district_type, district_name) {
  const votes_district = vote_data[year]['data'][district_type];
  const {votes, votes_frac, votes_total} = votesDistrict(votes_district, party, district_name);

  var txt = '';
  txt += hoverInfoLineTxt('votes', valuePcti18nAttr(votes, votes_frac));
  txt += hoverInfoLineTxt('valid_votes', valuei18nAttr(votes_total));
  return txt;
}

function votesDistrictDiffTxt(years, vote_data, party, district_type, district) {
  const data = votesDiffDistrict(years, vote_data, party, district_type, district);

  var txt = '';
  txt += txtLineKeyValPartyNoData(years[0], data);
  txt += txtLineKeyValPartyNoData(years[1], data);
  txt += hoverInfoLineTxt("change", valuei18nAttr(data.chg, {sign: 'exceptZero'}));

  return txt;
}

function votesDiffDistrict(years, vote_data, party, district_type, district_name) {
  var data = {};
  var frac = [];
  years.forEach((year) => {
    var votes = -999;
    var votes_frac = -999;
    const yr_data = vote_data[year]['data'][district_type];
    if (Object.keys(yr_data).includes(party)) {
      var {votes, votes_frac} = votesDistrict(yr_data, party, district_name);
      frac.push(votes_frac);
    } else {
      frac.push(0);
    }
    data[year] = {votes, votes_frac};
  });
  const chg = (frac[0]-frac[1])*100;
  data['chg'] = chg;

  return data;
}

function hoverInfoDistrictTxt(idx, geo_data, district) {
  var txt = '';
  txt += hoverInfoLineTxt('region', stri18nAttr(geo_data['regionsnavn'][idx]));
  txt += hoverInfoLineTxt('constituency', stri18nAttr(geo_data['storkredsnavn'][idx]));
  txt += hoverInfoLineTxt('municipality', stri18nAttr(geo_data['kredskommunenavn'][idx]));
  txt += hoverInfoLineTxt('nomination_district', stri18nAttr(district));
  
  return txt;
}

function hoverInfoAddTxt(
  district, heatmap_items, vote_data,
  map_select, district_type
  ) {
  var txt = '';
  const heatmap_type = heatmap_items['type'];
  const map_select_val = map_select.value;

  if (heatmap_type == 'value') {
    const year = heatmap_items['year'];
    txt += votesDistrictTxt(year, vote_data, map_select_val, district_type, district);
  }

  if (heatmap_type == 'diff') {
    const years = heatmap_items['year'];
    txt += votesDistrictDiffTxt(years, vote_data, map_select_val, district_type, district);
  }

  if (heatmap_type == 'voters_density') {
    var options_idx = map_select.options.indexOf(map_select.value);
    if (options_idx === -1)
      options_idx = 0;
    
    const year = map_select.tags[options_idx]['i18n-val']['str']['str'];
    txt += voteDensTxt(year, vote_data, district);
  }

  return txt;
}

function mapTitle(data_type, heatmap_type_wdg, map_select_wdg) {
  const main_elm = document.getElementById("map-title");
  const sub_elm = document.getElementById("sub-title");

  const heatmap_type_wdg_tags = heatmap_type_wdg.tags;
  const heatmap_active = heatmap_type_wdg_tags[heatmap_type_wdg.active];
  const map_select_wdg_tags = map_select_wdg.tags;
  var options_idx;

  if ((data_type == 'district') || (data_type == 'voters_density')) {
    options_idx = map_select_wdg.options.indexOf(map_select_wdg.value);
  } else {
    for (var i = 0; i < map_select_wdg.options.length; i++) {
      if (map_select_wdg.options[i][0] != map_select_wdg.value)
        continue;
      
      options_idx = i;
      break;
    }
  }

  if (data_type == 'district') {
    const i18n_obj = map_select_wdg_tags[options_idx];
    main_elm.setAttribute('i18n-key', i18n_obj['i18n-key']);
    main_elm.removeAttribute('i18n-val');

    sub_elm.setAttribute('i18n-key', 'subtille-districts');
  }

  if (data_type == 'value') {
    main_elm.setAttribute('i18n-key', 'maintitle-election');
    const str2 = heatmap_active['i18n-val']['str']['str'];
    const party_name = map_select_wdg.options[options_idx][1];
    const val = JSON.stringify(strStri18nAttr(party_name, str2));
    main_elm.setAttribute('i18n-val', val);

    sub_elm.setAttribute('i18n-key', 'subtitle-election');
  }

  if (data_type == 'diff') {
    main_elm.setAttribute('i18n-key', 'maintitle-election-diff');
    const str2 = heatmap_active['i18n-val']['str']['str'];
    const party_name = map_select_wdg.options[options_idx][1];
    const val = JSON.stringify(strStri18nAttr(party_name, str2));
    main_elm.setAttribute('i18n-val', val);

    sub_elm.setAttribute('i18n-key', 'subtitle-election-diff');
  }

  if (data_type == 'voters_density') {
    const i18n_obj = map_select_wdg_tags[options_idx];
    main_elm.setAttribute('i18n-key', i18n_obj['i18n-key']);
    main_elm.setAttribute('i18n-val', JSON.stringify(i18n_obj['i18n-val']));

    sub_elm.setAttribute('i18n-key', 'subtitle-voters-density');
  }
  updateElementTxt(main_elm);
  updateElementTxt(sub_elm);
}

function localeDataSources() {
  formatElectionResultSrc();

  const heatmap_wdg = window.Bokeh.documents[0].get_model_by_name('heatmap_type');
  if (heatmap_wdg.active == 1)
    formatVotersDensityLegendSrc();
}

function formatElectionResultSrc() {
  const cds = window.Bokeh.documents[0].get_model_by_name('src_results');
  const data = cds.data;
  const cols = [];
  for (const key of Object.keys(data)) {
    if (key.endsWith('_label')) cols.push(key);
  }
  cols.forEach(elem => {
    const arr = [];
    const val_col = elem.split('_')[0];
    for (var i = 0; i < data[elem].length; i++) {
      const label = data[elem][i];
      const val = data[val_col][i];
      if (val_col.length == 4) {
        arr.push(formatAsPercent(val, 1));
      } else {
        const value = {num: val, digits: 1, sign: 'exceptZero'};
        arr.push(formatAsIntl(value));
      }
    }
    data[elem] = arr;
  });
  cds.change.emit();
}

function colorbarTicker(colorbar, scale = 1) {
  var high = colorbar.color_mapper.high;
  var low = colorbar.color_mapper.low;
  
  low *= scale;
  high *= scale;
  const scale_size = high - low;
  var no_ticks = 10;
  var intv = Math.trunc(scale_size / (no_ticks-1));
  for (const i of [0.5, 1, 2, 3, 5, 15]) {
    if (scale_size % i != 0) continue;

    no_ticks = Math.trunc(scale_size / i)+1;
    intv = i;
    if ((no_ticks > 9) & (low >= 0)) continue;
    if ((no_ticks > 11) & (low < 0)) continue;
    else break;
  }
  const ticker = [];
  for (i = 0; i < no_ticks; i ++) {
    ticker.push((low + intv*i)/scale);
  }
  return ticker;
}

function mapperHighLow(min_val, max_val) {
  var low = Math.floor(min_val * 100);
  var high = Math.ceil(max_val * 100);
  var scale_size = high - low;
  var pal_size = 10
  
  if (scale_size <= 10) {
    if ([1, 2].includes(scale_size)) pal_size = 8;
    else if ([3, 6].includes(scale_size)) pal_size = 6;
    else if ([4, 8].includes(scale_size)) pal_size = 8;
    else pal_size = Math.trunc(scale_size);
  }

  if (scale_size > 10) {
    if (low % 5 == 4) low += 1;
    else if (low % 5 != 0) low = (Math.trunc(low/5))*5;

    if (high % 5 == 1) high -= 1;
    else if (high % 5 != 0) high = (Math.trunc(high/5)+1)*5;

    pal_size = high-low;
  }
  low = Math.trunc(low)/100;
  high = Math.trunc(high)/100;

  return {low, high, pal_size};
}

function partyVoteShareMapper(vote_data, party, mapper, palette) {
  var min_val = 1.0;
  var max_val = 0.0;
  for (const year of Object.keys(vote_data)) {
    if (vote_data[year]['parties']['parties'].includes(party)) {
      const data = vote_data[year]['data']['opstillingskredse'][party]['VoteFrac'];
      min_val = Math.min(...data, min_val);
      max_val = Math.max(...data, max_val);
    }
  }

  const {low, high, pal_size} = mapperHighLow(min_val, max_val);
  mapper.low = low;
  mapper.high = high;
  mapper.palette = palette[pal_size];
}

function updateColorbar(colorbar, mapper, tick_scale) {
  colorbar.color_mapper = mapper;
  colorbar.ticker.ticks = colorbarTicker(colorbar, tick_scale);
}

function updateFakeSrcLegends(factor_cmap, items, plot, coord, heatmap_type) {
  const lgnd1 = plot.select(name = 'legend1')[0];
  const lgnd2 = plot.select(name = 'legend2')[0];
  const src1 = window.Bokeh.documents[0].get_model_by_name('map_fake1_src');
  const src2 = window.Bokeh.documents[0].get_model_by_name('map_fake2_src');

  factor_cmap.factors = items;
  updateGlyphFillColor(plot, 'r_fake1', factor_cmap);
  updateGlyphFillColor(plot, 'r_fake2', factor_cmap);
  mapSelectDistrictSrc(items, src1, src1, coord, heatmap_type);
  mapLegendRows(lgnd1, lgnd2, items);
}

function updateGlyphFillColor(plot, glyphName, transform) {
  const r = plot.select(name = glyphName)[0];
  r.glyph.fill_color = {field: 'value', transform: transform};
}

function mapSelectDistrictSrc(items, fake1_src, fake2_src, fake_coord, heatmap_type) {
  const f1_data = fake1_src.data;
  const f2_data = fake2_src.data;
  const max_items_row = 5;
  const value = items;
  var legend_labels = items; 
  
  if (heatmap_type == 'voters_density') {
    legend_labels = formatVotersDensityItems(items);
  }

  f2_data['legend'] = [];
  f2_data['value'] = [];
  f2_data['x'] = [];
  f2_data['y'] = [];

  f1_data['legend'] = legend_labels.slice(0, Math.min(items.length, max_items_row));
  f1_data['value'] = value.slice(0, Math.min(items.length, max_items_row));
  f1_data['x'] = arrayFill(f1_data['legend'].length, fake_coord[0]);
  f1_data['y'] = arrayFill(f1_data['legend'].length, fake_coord[1]);

  if (items.length > max_items_row) {
    f2_data['legend'] = legend_labels.slice(max_items_row);
    f2_data['value'] = value.slice(max_items_row);
    f2_data['x'] = arrayFill(f2_data['legend'].length, fake_coord[0]);
    f2_data['y'] = arrayFill(f2_data['legend'].length, fake_coord[1]);
  }
  fake1_src.change.emit();
  fake2_src.change.emit();
}

function formatVotersDensityItems(items) {
  const labels = [];
  for (var i = 0; i < items.length; i++) {
    const label_split = items[i].split('-');
    const low = {num: parseInt(label_split[0]), digits: 0};
    const high = {num: parseInt(label_split[1]), digits: 0};

    labels.push(`${formatAsIntl(low)}-${formatAsIntl(high)}`);
  }
  return labels;
}

function formatVotersDensityLegendSrc() {
  const src_names = ['map_fake1_src', 'map_fake2_src'];
  src_names.forEach((src_name) => {
    const src = window.Bokeh.documents[0].get_model_by_name(src_name);
    src.data['legend'] = formatVotersDensityItems(src.data['value']);
    src.change.emit();
  });
}

function mapLegendRows(legend1, legend2, items) {
  legend1.visible = true;
    if (items.length > 5) {
      legend1.margin = 0;
      legend2.visible = true;
      legend1.spacing = 5;
      legend2.spacing = 5;
    } else {
      legend1.margin = 15;
      legend2.visible = false;
      legend1.spacing = 5;
    }
}

function voteFrac2geoArrDiff(geo_data, vote_data, party, years) {
  const year0 = Number(years[0]);
  const year1 = Number(years[1]);
  const votes_y0 = vote_data[year0]['data']['opstillingskredse'];
  const votes_y1 = vote_data[year1]['data']['opstillingskredse'];
  const geo_votefrac_y0 = voteFrac2geoArr(geo_data, votes_y0, party);
  var chg = [];
  if (vote_data[year1]['parties']['parties'].includes(party)) {
    const geo_votefrac_y1 = voteFrac2geoArr(geo_data, votes_y1, party);
    for (i = 0; i < geo_votefrac_y0.length; i++) {
      chg.push((geo_votefrac_y0[i] - geo_votefrac_y1[i])*100);
    }
  } else {
    for (const element of geo_votefrac_y0) {
      chg.push(element*100);
    }
  }
  return chg;
}

function voteDens2geoArr(geo_data, vote_data, bins) {
  var geo_val = [];
  for (const district of geo_data['navn']) {
    const idx = vote_data['navn'].indexOf(district);
    const voters_density = vote_data['voters_density'][idx];
    var i = 0;
    var i_adj = 0;
    if (bins[0] === 0) {
      i = 1;
      i_adj = 1;
    }
    var loop_bins_bool = true;
    while (loop_bins_bool) {
      if (voters_density < bins[i]) {
        geo_val.push(i-i_adj);
        loop_bins_bool = false;
      } else {
        i += 1;
      }
    }
  }
  return geo_val;
}

function voteFrac2geoArr(geo_data, vote_data, party) {
  var geo_val = [];
  for (const district of geo_data['navn']) {
    const idx = vote_data['navn'].indexOf(district);
    geo_val.push(vote_data[party]['VoteFrac'][idx]);
  }
  return geo_val;
}

function runBkScript() {
    if ((window.Bokeh.documents[0] !== undefined)) {
        let heatmap_type_wdg = window.Bokeh.documents[0].get_model_by_name('heatmap_type');
        heatmap_type_wdg.active = 0;
        localeDataSources()
    } else {
        setTimeout(runBkScript, 1000);
    }
}
window.onload = function() {
    runBkScript();
}