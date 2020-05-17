var icon_green = new OpenLayers.Icon(
  fmStaticPath + '/mm_20_green.png',
  new OpenLayers.Size(12,20),
  new OpenLayers.Pixel(-(12/2), -20)
);

var icon_red = new OpenLayers.Icon(
  fmStaticPath + '/mm_20_red.png',
  new OpenLayers.Size(12,20),
  new OpenLayers.Pixel(-(12/2), -20)
);

var icon_gray = new OpenLayers.Icon(
  fmStaticPath + '/mm_20_gray.png',
  new OpenLayers.Size(12,20),
  new OpenLayers.Pixel(-(12/2), -20)
);

var icon_blue = new OpenLayers.Icon(
  fmStaticPath + '/mm_20_blue.png',
  new OpenLayers.Size(12,20),
  new OpenLayers.Pixel(-(12/2), -20)
);

var icon_orange = new OpenLayers.Icon(
  fmStaticPath + '/mm_20_orange.png',
  new OpenLayers.Size(12,20),
  new OpenLayers.Pixel(-(12/2), -20)
);

function makemap(div, centerlon, centerlat, zoom) {
  var arrayOSM = [
    "//a.tile.openstreetmap.org/${z}/${x}/${y}.png",
    "//b.tile.openstreetmap.org/${z}/${x}/${y}.png",
    "//c.tile.openstreetmap.org/${z}/${x}/${y}.png",
  ];
  var arrayCARTOLight = [
    "//cartodb-basemaps-a.global.ssl.fastly.net/light_all/${z}/${x}/${y}.png",
    "//cartodb-basemaps-b.global.ssl.fastly.net/light_all/${z}/${x}/${y}.png",
    "//cartodb-basemaps-c.global.ssl.fastly.net/light_all/${z}/${x}/${y}.png",
  ];
  var arrayCARTODark = [
    "//cartodb-basemaps-a.global.ssl.fastly.net/dark_all/${z}/${x}/${y}.png",
    "//cartodb-basemaps-b.global.ssl.fastly.net/dark_all/${z}/${x}/${y}.png",
    "//cartodb-basemaps-c.global.ssl.fastly.net/dark_all/${z}/${x}/${y}.png",
  ];
  var arrayStamenTerrain = [
    "//stamen-tiles-a.a.ssl.fastly.net/terrain/${z}/${x}/${y}.png",
    "//stamen-tiles-b.a.ssl.fastly.net/terrain/${z}/${x}/${y}.png",
    "//stamen-tiles-c.a.ssl.fastly.net/terrain/${z}/${x}/${y}.png",
  ];
  var arrayStamenToner = [
    "//stamen-tiles-a.a.ssl.fastly.net/toner/${z}/${x}/${y}.png",
    "//stamen-tiles-b.a.ssl.fastly.net/toner/${z}/${x}/${y}.png",
    "//stamen-tiles-c.a.ssl.fastly.net/toner/${z}/${x}/${y}.png",
  ];

  var map = new OpenLayers.Map({
    div: div,
    theme: null,
    controls: [
      new OpenLayers.Control.Attribution(),
      new OpenLayers.Control.TouchNavigation({
        dragPanOptions: {
          enableKinetic: true
        }
      }),
      new OpenLayers.Control.ZoomPanel(),
      new OpenLayers.Control.LayerSwitcher({'ascending':false}),
    ],
    layers: [
      new OpenLayers.Layer.OSM("CARTO Dark", arrayCARTODark, {
        transitionEffect: "resize",
        maxZoom: 18,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, &copy; <a href="https://carto.com/attribution" target="_blank">CARTO</a>',
      }),
      new OpenLayers.Layer.OSM("CARTO Light", arrayCARTOLight, {
        transitionEffect: "resize",
        maxZoom: 18,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, &copy; <a href="https://carto.com/attribution" target="_blank">CARTO</a>',
      }),
      new OpenLayers.Layer.OSM("OpenStreetMap", arrayOSM, {
        transitionEffect: "resize",
        attribution: 'Courtesy: <a href="http://openstreetmap.org/" target="_blank">OpenStreetMap</a>',
      }),
      new OpenLayers.Layer.OSM("Stamen Toner", arrayStamenToner, {
        transitionEffect: "resize",
        attribution: 'Map tiles by <a href="http://stamen.com" target="_blank">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0" target="_blank">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org" target="_blank">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright" target="_blank">ODbL</a>.',
      }),
      new OpenLayers.Layer.OSM("Stamen Terrain", arrayStamenTerrain, {
        transitionEffect: "resize",
        attribution: 'Map tiles by <a href="http://stamen.com" target="_blank">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0" target="_blank">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org" target="_blank">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright" target="_blank">ODbL</a>.',
      }),
    ],
    center: new OpenLayers.LonLat(centerlon, centerlat)
        .transform(
          new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
          new OpenLayers.Projection("EPSG:900913") // to Spherical Mercator Projection
        ),
    zoom: zoom
  });

  return(map);
}

function setMarker(map, lon, lat, icon_base, layer, content_html, hover){
  var lonLatMarker = new OpenLayers.LonLat(lon, lat).transform(new OpenLayers.Projection("EPSG:4326"),  map.getProjectionObject());
  var icon = icon_base.clone();
  var marker = new OpenLayers.Marker(lonLatMarker, icon);

  if(content_html) {
    var feature = new OpenLayers.Feature(layer, lonLatMarker);
    feature.closeBox = false;
    feature.opacity = 0.9;
    feature.popupClass = OpenLayers.Class(OpenLayers.Popup.AnchoredBubble, {});
    feature.data.popupContentHTML = content_html;
    feature.data.overflow = "auto";
    feature.data.popupSize = new OpenLayers.Size(200, 100);

    marker.feature = feature;

    var markerClick = function(evt) {
      if (this.popup == null) {
        this.popup = this.createPopup(this.closeBox);
        this.popup.opacity = this.opacity;
        map.addPopup(this.popup);
        this.popup.show();
      } else {
        this.popup.toggle();
      }
      OpenLayers.Event.stop(evt);
    };
    var markerPointerOver = function(evt) {
      map.div.style.cursor = "pointer";
      OpenLayers.Event.stop(evt);
    };
    var markerPointerOut = function(evt) {
      map.div.style.cursor = "default";
      OpenLayers.Event.stop(evt);
    };
    if(hover) {
      marker.events.register("mouseover", feature, markerClick);
      marker.events.register("mouseout", feature, markerClick);
    } else {
      marker.events.register("mouseover", feature, markerPointerOver);
      marker.events.register("mouseout", feature, markerPointerOut);
      marker.events.register("mousedown", feature, markerClick);
    }

  }

  layer.addMarker(marker);
}
