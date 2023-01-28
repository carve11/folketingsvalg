// local-scripts.js
const defaultLocale = "da";
const supportedLocales = ["da", "en"];

const localeTags = {
  da: "da-DK",
  en: "en-US",
};

let locale;

document.addEventListener("DOMContentLoaded", () => {
  const initialLocale = defaultLocale;

  updateLocale(initialLocale);
  localeSelectCallback(initialLocale);
});

function localeSelectCallback(initialValue) {
  const select = document.querySelector("[i18n-select]");
  select.value = initialValue;
  select.onchange = (e) => {
    updateLocale(e.target.value);
  };
}

function updateLocale(newLocale) {
  locale = newLocale;

  document
   .querySelectorAll("[i18n-key]")
   .forEach(updateElementTxt);

  translateBokehObjScript();
}

function translateBokehObjScript() {
  if ((window.Bokeh.documents[0] !== undefined)) {
    translateBokehWidgets();
    localeDataSources();
    translateBokehPlots();
  } else {
    setTimeout(translateBokehObjScript, 2000);
  }
}

function updateElementTxt(element) {
  const key = element.getAttribute("i18n-key");
  const valueObj = JSON.parse(element.getAttribute("i18n-val")) || {};

  element.innerText = replaceTemplate(key, valueObj);
}

function replaceTemplate(key, replaceObj = {}) {
  const translation = translations[locale][key];
  if (translation == undefined) {
    return '';
  }

  if (Object.keys(replaceObj).length == 0) return translation;

  return Object.keys(replaceObj).reduce(
      (acc, cur) => {
        const value = formatNumber(replaceObj[cur]);

        return acc.replace(
          new RegExp(`{\s*${cur}\s*}`, "g"),
          value
        );
      },
      translation,
    );
}

function formatNumber(numObj) {
  if (Object.hasOwn(numObj, 'str')) return numObj['str'];
  if (numObj['style'] == 'decimal') return formatAsIntl(numObj);
  if (numObj['style'] == 'pct') return formatAsPercent(numObj['num']);
  return numObj;
}

function translateBokehWidgets() {
  const bk_wdg = ['heatmap_type', 'map_select'];

  bk_wdg.forEach((wdg_name) => {
    const wdg = window.Bokeh.documents[0].get_model_by_name(wdg_name);
    translateBokehWidgetItems(wdg);
    });
}

function translateBokehWidgetItems(wdg) {
  const items = [];
  const tags = wdg.tags;
  let wdg_items_type = '';
  let idx = 0;

  if (wdg.options != undefined) {
    wdg_items_type = 'options';
    idx = wdg[wdg_items_type].indexOf(wdg.value);
  }
  if (wdg.labels != undefined) wdg_items_type = 'labels';

  for (let i = 0; i < tags.length; i++) {
    const key = tags[i]['i18n-key'];
    const valueObj = tags[i]['i18n-val'] || {};

    items.push(replaceTemplate(key, valueObj));
  }
  
  if (tags.length > 0) wdg[wdg_items_type] = items;
  
  if (wdg_items_type == 'options') {
    if (idx != -1) wdg.value = items[idx];
  }
}

function translateBokehPlots() {
  const xaxis = window.Bokeh.documents[0].get_model_by_name('hist_voters_density_xaxis');
  const yaxis = window.Bokeh.documents[0].get_model_by_name('hist_voters_density_yaxis');
  xaxis.axis_label = replaceTemplate('axis-label-voters-density-grid');
  yaxis.axis_label = replaceTemplate('probability');
}