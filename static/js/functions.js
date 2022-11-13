// functions.js

function formatAsPercent(num) {
  return new Intl.NumberFormat('default', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

function formatAsIntl(num) {
  return new Intl.NumberFormat('default', {
    style: 'decimal',
    maximumFractionDigits: 2,
  }).format(num);
}

function votesAndPct(votes, vote_pct) {
  const str1 = formatAsIntl(votes);
  const str2 = formatAsPercent(vote_pct);
  return `${str1} (${str2})`;
}

function listPartyResultsBullet(party_votes, party_frac, total_votes) {
  const str1 = votesAndPct(party_votes, party_frac);
  const str2 = formatAsIntl(total_votes);

  return `<ul class="list"><li>Stemmer: ${str1}</li>
    <li>Stemme grundlag: ${str2}</li></ul>`;
}

function listPartyResults(party_votes, party_frac, total_votes) {
  const str1 = votesAndPct(party_votes, party_frac);
  const str2 = formatAsIntl(total_votes);

  return `Stemmer: ${str1}\nStemme grundlag: ${str2}`;
}

function listPartyResultsNational(data) {
  const {votes, votes_frac, votes_total, eligible_voters, eligible_voters_vote} = data;
  const str1 = votesAndPct(votes, votes_frac);
  const str2 = formatAsIntl(votes_total);
  const str3 = votesAndPct(eligible_voters_vote, eligible_voters_vote/eligible_voters);
  const str4 = formatAsIntl(eligible_voters);

  return `<ul class="list"><li>Stemmer: ${str1}</li>
    <li>Gyldige stemmer: ${str2}</li>
    <li>Afgivne stemmer: ${str3}</li>
    <li>Stemmeberettigede: ${str4}</li>
    </ul>`;
}

function arrayFill(length, value) {
  var array = [];
  for(var i=0; i<length; ++i) array.push(value);
  return array;
}

function mapSelectPartyTxt(vote_data, party) {
  var txt = '<div class="div-text">Lands resultat';
  txt += listPartyResultsNational(votesNational(vote_data['Land'], party));
  txt += districtMaxVotesTxt(vote_data['opstillingskredse'], party);
  txt += districtMaxVoteFracTxt(vote_data['opstillingskredse'], party);
  txt += '</div>'
  
  return txt;
}

function maxLocation(votes_district, party, max_key_lookup) {
  const arr_for_max = votes_district[party][max_key_lookup];
  const max_val = Math.max(...arr_for_max);
  const idx = arr_for_max.indexOf(max_val);
  const location = votes_district['navn'][idx];
  const votes = votes_district[party]['StemmerAntal'][idx];
  const vote_frac = votes_district[party]['VoteFrac'][idx];
  const votes_total = votes_district['IAltGyldigeStemmer'][idx];
  
  return {location, votes, vote_frac, votes_total}
}

function districtMaxVotesTxt(vote_data, party) {
  const {location, votes, vote_frac, votes_total} = maxLocation(vote_data, party, 'StemmerAntal')
  var txt = 'Kreds, flest antal stemmer: ' + location;
  txt += listPartyResultsBullet(votes, vote_frac, votes_total);

  return txt;
}

function districtMaxVoteFracTxt(vote_data, party) {
  const {location, votes, vote_frac, votes_total} = maxLocation(vote_data, party, 'VoteFrac')
  var txt = 'Kreds, højeste stemmeandel: ' + location;
  txt += listPartyResultsBullet(votes, vote_frac, votes_total);

  return txt;
}

function mapSelectPartyDiffTxt(years, vote_data, party, geo_data) {
  var txt = '<div class="div-text">'
  txt += onlyHighLowTxt(geo_data);
  txt += 'Lands resultat';
  const national_diff = votesNationalDiffTxt(years, vote_data, party);
  txt += diffDistrictTxt(national_diff, 'bullet')
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
  const str = votesDistrictDiffTxt(years, vote_data, party, location);
  var txt = '';
  if (val < 0) {
    txt += 'Kreds, mindste tilbagegang: ';
  } else {
    txt += 'Kreds, største fremgang: ';
  }
  txt += location;
  txt += diffDistrictTxt(str, 'bullet')

  return txt;
}

function districtLowestDiffChg(years, vote_data, party, geo_data) {
  const {location, val} = geoDataLocationMinMax(geo_data, 'min');
  const str = votesDistrictDiffTxt(years, vote_data, party, location);
  var txt = '';
  if (val < 0) {
    txt += 'Kreds, største tilbagegang: ';
  } else {
    txt += 'Kreds, mindste fremgang: ';
  }
  txt += location;
  txt += diffDistrictTxt(str, 'bullet')

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

function diffDistrictTxt(str, list_type) {
  if (list_type == 'bullet') {
    return `<ul class="list">
      <li>${str[0]}</li>
      <li>${str[1]}</li>
      <li>${str[2]}</li></ul>`;
  } else {
    return `${str[0]}\n${str[1]}\n${str[2]}`;
  }
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

function updateGlyphFillColor(plot, glyphName, mapper) {
  const r = plot.select(name = glyphName)[0];
  r.glyph.fill_color = mapper;
}

function resultDiff(vote_data, party, years) {
  const year0 = Number(years[0]);
  const year1 = Number(years[1]);
  const votes_y0 = vote_data[year0]['data']['opstillingskredse'];
  const votes_y1 = vote_data[year1]['data']['opstillingskredse'];
  var chg = [];
  if (vote_data[year1]['parties']['parties'].includes(party)) {
    for (i = 0; i < votes_y0[party]['VoteFrac'].length; i++) {
      const y0_i = votes_y0[party]['VoteFrac'][i];
      const y1_i = votes_y1[party]['VoteFrac'][i];
      chg.push((y0_i - y1_i)*100);
    }
  } else {
    for (i = 0; i < votes_y0[party]['VoteFrac'].length; i++) {
      const y0_i = votes_y0[party]['VoteFrac'][i];
      chg.push(y0_i*100);
    }
  }
  return chg;
}

function votesDistrict(vote_data, party, district_name) {
  const idx = vote_data['navn'].indexOf(district_name);
  const votes = vote_data[party]['StemmerAntal'][idx];
  const votes_frac = vote_data[party]['VoteFrac'][idx];
  const votes_total = vote_data['IAltGyldigeStemmer'][idx];
  
  return {votes, votes_frac, votes_total};
}

function votesNational(vote_data, party) {
  const votes = vote_data[party]['StemmerAntal'][0];
  const votes_frac = vote_data[party]['VoteFrac'][0];
  const votes_total = vote_data['IAltGyldigeStemmer'][0];
  const eligible_voters = vote_data['Stemmeberettigede'][0];
  const eligible_voters_vote = vote_data['IAltAfgivneStemmer'][0];

  return {votes, votes_frac, votes_total, eligible_voters, eligible_voters_vote};
}

function votesDistrictTxt(year, vote_data, party, district_name) {
  const votes_district = vote_data[year]['data']['opstillingskredse'];
  const {votes, votes_frac, votes_total} = votesDistrict(votes_district, party, district_name);

  return listPartyResults(votes, votes_frac, votes_total);
}

function votesDistrictDiffTxt(years, vote_data, party, district_name) {
  var str = [];
  var frac = [];
  years.forEach((year) => {
    var txt = year.toString() + ': '
    const votes_district = vote_data[year]['data']['opstillingskredse'];
    if (Object.keys(votes_district).includes(party)) {
      const {votes, votes_frac, votes_total} = votesDistrict(votes_district, party, district_name);
      txt += formatAsIntl(votes);
      txt += ' (' + formatAsPercent(votes_frac) + ')';  
      frac.push(votes_frac);
    } else {
      txt += 'nyt parti, ingen data'
      frac.push(0);
    }
    str.push(txt);
  });
  str.push('Ændring (procentpoint): ' + formatAsIntl((frac[0]-frac[1])*100));
  return str;
}

function votesNationalDiffTxt(years, vote_data, party) {
  var str = [];
  var frac = [];
  years.forEach((year) => {
    var txt = year.toString() + ': '
    const votes_national = vote_data[year]['data']['Land'];
    if (Object.keys(votes_national).includes(party)) {
      const {votes, votes_frac} = votesNational(votes_national, party);
      txt += formatAsIntl(votes);
      txt += ' (' + formatAsPercent(votes_frac) + ')';  
      frac.push(votes_frac);
    } else {
      txt += 'nyt parti, ingen data' 
      frac.push(0);
    }
    str.push(txt);
  });

  str.push('Ændring (procentpoint): ' + formatAsIntl((frac[0]-frac[1])*100));
  return str;
}

function mapTitle(txt) {
  document.getElementById("map-title").innerHTML = txt[0];
  document.getElementById("sub-title").innerHTML = txt[1];
}

function runBkScript() {
    if ((window.Bokeh.documents[0] !== undefined)) {
        let heatmap_type_wdg = window.Bokeh.documents[0].get_model_by_name('heatmap_type');
        heatmap_type_wdg.active = 0;
    } else {
        setTimeout(runBkScript, 1000);
    }
}
window.onload = function() {
    runBkScript();
}