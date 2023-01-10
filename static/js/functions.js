// functions.js
function formatAsPercent(num, digits = 2) {
  var signi_digi = 3;
  if (num < 0.00995) {
    signi_digi = 2;
  }
  if (num < 0.00095) {
    signi_digi = 1;
  }
  if (digits == 0) signi_digi = 3;
  return new Intl.NumberFormat('default', {
    style: 'percent',
    maximumFractionDigits: digits,
    maximumSignificantDigits: signi_digi,
    minimumSignificantDigits: signi_digi,
  }).format(num);
}

function pctTicker(num, digits) {
  var min_signi_digi = 1;
  var max_signi_digi = 10;
  if (digits == 1) {
    if (num < 0.00995) min_signi_digi = digits;
    else if (num < 0.0995) min_signi_digi += digits;
    else min_signi_digi = 3;
  }
  return new Intl.NumberFormat('default', {
    style: 'percent',
    minimumFractionDigits: digits,
    //maximumSignificantDigits: signi_digi,
    minimumSignificantDigits: min_signi_digi,
  }).format(num);
}

function formatAsIntl(num, digits = 2, sign = 'auto') {
  var minFracDig = 0;
  if (num < 10) minFracDig = 1;
  if (num < 1) minFracDig = Math.min(digits, 2);
  if (digits == 0) minFracDig = 0;
  return new Intl.NumberFormat('default', {
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

function votesAndPct(votes, vote_pct) {
  const str1 = formatAsIntl(votes);
  const str2 = formatAsPercent(vote_pct);
  return `${str1} (${str2})`;
}

function arrElem2Text(str_arr, list_type = 'bullet') {
  var txt = '';
  if (list_type == 'bullet') {
    txt += '<ul class="list">';
    txt += '<li>';
    txt += str_arr.join('</li><li>');
    txt += '</li></ul>';
  } else {
    txt += str_arr.join('\n');
  }
  return txt;
}

function listPartyResults(party_votes, party_frac, total_votes) {
  const str_arr = [];
  str_arr.push(`Stemmer: ${votesAndPct(party_votes, party_frac)}`);
  str_arr.push(`Stemme grundlag: ${formatAsIntl(total_votes)}`);

  return arrElem2Text(str_arr, 'list');
}

function listPartyResultsNational(vote_data, party) {
  const {votes, votes_frac, votes_total} = votesDistrict(vote_data, party, 'Hele landet');
  const {eligible_voters, eligible_voters_vote} = districtVoteData(vote_data, 'Hele landet');
  const eligible_frac = eligible_voters_vote / eligible_voters;
  const str_arr = [];
  str_arr.push(`Stemmer: ${votesAndPct(votes, votes_frac)}`);
  str_arr.push(`Gyldige stemmer: ${formatAsIntl(votes_total)}`);
  str_arr.push(`Afgivne stemmer: ${votesAndPct(eligible_voters_vote, eligible_frac)}`);
  str_arr.push(`Stemmeberettigede: ${formatAsIntl(eligible_voters)}`);

  return arrElem2Text(str_arr, 'bullet');
}

function highLowDistrictTxt(geo_data, votes_district, party, min_max) {
  const {location, val} = geoDataLocationMinMax(geo_data, min_max);
  const {votes, votes_frac, votes_total} = votesDistrict(votes_district, party, location);
  const str_arr = [];
  str_arr.push(`Opstillingskreds: ${location}`);
  str_arr.push(`Stemmer: ${votesAndPct(votes, votes_frac)}`);
  str_arr.push(`Stemme grundlag: ${formatAsIntl(votes_total)}`);

  return arrElem2Text(str_arr, 'bullet');
}

function mapSelectPartyTxt(geo_data, vote_data, party) {
  var txt = '<div class="div-text">';
  txt += 'Landsresultat';
  txt += listPartyResultsNational(vote_data['Land'], party);
  txt += 'Højeste stemmeandel'
  txt += highLowDistrictTxt(geo_data, vote_data['opstillingskredse'], party, 'max')
  txt += 'Laveste stemmeandel'
  txt += highLowDistrictTxt(geo_data, vote_data['opstillingskredse'], party, 'min')
  txt += '</div>'

  return txt;
}

function mapSelectPartyDiffTxt(years, vote_data, party, geo_data) {
  const str_arr = votesDiffDistrict(years, vote_data, party, 'Land', 'Hele landet');
  var txt = '<div class="div-text">'
  txt += onlyHighLowTxt(geo_data);
  txt += 'Landsresultat';
  txt += arrElem2Text(str_arr, 'bullet');
  txt += districtHighestDiffChg(years, vote_data, party, geo_data);
  txt += districtLowestDiffChg(years, vote_data, party, geo_data);
  txt += '</div>'
  
  return txt;
}

function onlyHighLowTxt(geo_data) {
  var txt = '';
  var {val} = geoDataLocationMinMax(geo_data, 'min');
  if (val > 0) {
    txt += 'Parti har kun oplevet fremgang.<br>';
  }
  var {val} = geoDataLocationMinMax(geo_data, 'max');
  if (val < 0) {
    txt += 'Parti har kun oplevet tilbagegang.<br>';
  }
  return txt;
}

function districtHighestDiffChg(years, vote_data, party, geo_data) {
  const {location, val} = geoDataLocationMinMax(geo_data, 'max');
  const diff_str_arr = votesDiffDistrict(years, vote_data, party, 'opstillingskredse', location);
  const str_arr = [`Opstillingskreds: ${location}`];
  str_arr.push(...diff_str_arr);

  var txt = '';
  if (val < 0) {
    txt += 'Mindste tilbagegang';
  } else {
    txt += 'Største fremgang';
  }
  txt += arrElem2Text(str_arr, 'bullet')

  return txt;
}

function districtLowestDiffChg(years, vote_data, party, geo_data) {
  const {location, val} = geoDataLocationMinMax(geo_data, 'min');
  const diff_str_arr = votesDiffDistrict(years, vote_data, party, 'opstillingskredse', location);
  const str_arr = [`Opstillingskreds: ${location}`];
  str_arr.push(...diff_str_arr);

  var txt = '';
  if (val < 0) {
    txt += 'Største tilbagegang';
  } else {
    txt += 'Mindste fremgang';
  }
  txt += arrElem2Text(str_arr, 'bullet')

  return txt;
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

function mapSelectDistrictSrc(items, fake1_src, fake2_src, fake_coord) {
  const f1_data = fake1_src.data;
  const f2_data = fake2_src.data;
  const max_items_row = 5;
  if (items.length > max_items_row) {
    f1_data['legend'] = items.slice(0, max_items_row);
    f2_data['legend'] = items.slice(max_items_row);
    f1_data['x'] = arrayFill(max_items_row, fake_coord[0]);
    f2_data['x'] = arrayFill(f2_data['legend'].length, fake_coord[0]);
    f1_data['y'] = arrayFill(max_items_row, fake_coord[1]);
    f2_data['y'] = arrayFill(f2_data['legend'].length, fake_coord[1]);
  } else {
    f1_data['legend'] = items;
    f1_data['x'] = arrayFill(items.length, fake_coord[0]);
    f1_data['y'] = arrayFill(items.length, fake_coord[1]);
    f2_data['legend'] = [];
    f2_data['x'] = [];
    f2_data['y'] = [];
  }
  fake1_src.change.emit();
  fake2_src.change.emit();
}

function updateGlyphFillColor(plot, glyphName, transform) {
  const r = plot.select(name = glyphName)[0];
  r.glyph.fill_color = {field: 'legend', transform: transform};
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

function voteFrac2geoArr(geo_data, vote_data, party) {
  var geo_val = [];
  for (const district of geo_data['navn']) {
    const idx = vote_data['navn'].indexOf(district);
    geo_val.push(vote_data[party]['VoteFrac'][idx]);
  }
  return geo_val;
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

function voteDensTxt(year, vote_data, district_name) {
  const votes_district = vote_data[year]['data']['opstillingskredse'];
  const idx = votes_district['navn'].indexOf(district_name);
  const entitled_voters = votes_district['Stemmeberettigede'][idx];
  const votes_dens = votes_district['voters_density'][idx];
  const str_arr = [];
  str_arr.push(`Stemmeberettigede: ${formatAsIntl(entitled_voters)}`);
  str_arr.push(`Vælgertæthed per km²: ${formatAsIntl(votes_dens, 0)}`);

  return arrElem2Text(str_arr, 'list');
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

  return listPartyResults(votes, votes_frac, votes_total);
}

function votesDistrictDiffTxt(years, vote_data, party, district_type, district) {
  const str_arr = votesDiffDistrict(years, vote_data, party, district_type, district);
  return arrElem2Text(str_arr, 'list');
}

function votesDiffDistrict(years, vote_data, party, district_type, district_name) {
  var str_arr = [];
  var frac = [];
  years.forEach((year) => {
    var txt = '';
    const yr_data = vote_data[year]['data'][district_type];
    if (Object.keys(yr_data).includes(party)) {
      const {votes, votes_frac} = votesDistrict(yr_data, party, district_name);
      txt = votesAndPct(votes, votes_frac);
      frac.push(votes_frac);
    } else {
      txt = 'nyt parti, ingen data' 
      frac.push(0);
    }
    str_arr.push(`${year}: ${txt}`);
  });
  const chg = formatAsIntl((frac[0]-frac[1])*100, 2, 'exceptZero');
  str_arr.push(`Ændring (procentpoint): ${chg}`);

  return str_arr;
}

function mapTitle(txt) {
  document.getElementById("map-title").innerHTML = txt[0];
  document.getElementById("sub-title").innerHTML = txt[1];
}

function localeDataSources() {
  const cds = window.Bokeh.documents[0].get_model_by_name('src_results');
  const data = cds.data;
  const cols = [];
  for (const [key, value] of Object.entries(data)) {
    if (key.endsWith('_label')) cols.push(key);
  }
  cols.forEach(elem => {
    const arr = [];
    for (var i = 0; i < data[elem].length; i++) {
      const label = data[elem][i];
      const suffix = '';
      const val = parseFloat(label);
      if (label.endsWith('%')) {
        arr.push(formatAsPercent(val/100));
      } else {
        arr.push(formatAsIntl(val, 1, 'exceptZero'));
      }
    }
    data[elem] = arr;
  });
  cds.change.emit();
}

function colorbarFormat(colorbar, format) {
  // const diff_high_low = colorbar.color_mapper.high - colorbar.color_mapper.low;
  // var format = '0 %';
  // if (diff_high_low <= 0.05) format = '0.0 %';
  // if (diff_high_low <= 0.01) format = '0.00 %';
  if (format == 'num') {
    colorbar.formatter.code = 'return formatAsIntl(tick);'
  }
  if (format == 'pct') {
    colorbar.formatter.code = 'return formatAsPercent(tick);'
  }
  const cbscript = window.Bokeh.documents[0].get_model_by_name('color_bar_cb_code');
  console.log(cbscript);
  cbscript.execute();
  //colorbar.formatter.format = format;
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

// function updateMapper(vote_data, ) {
//   partyVoteShareMapper(vote_data, map_select.value, color_mapper['votefrac']['mapper'], color_mapper['votefrac']['whole_palette']);
//     color_bar.color_mapper = color_mapper['votefrac']['mapper'];
//     colorbarFormat(color_bar);
//     color_bar.ticker.ticks = colorbarTicker(color_bar, 100);

function updateColorbar(colorbar, mapper, format, tick_scale) {
  colorbar.color_mapper = mapper;
  //colorbarFormat(format);
  colorbar.ticker.ticks = colorbarTicker(colorbar, tick_scale);
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