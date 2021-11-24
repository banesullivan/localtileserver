// Initialize the map
let map = geo.map({
    node: '#map',
    clampBoundsX: true
})

/////////////////////////////
// Map Layers - order matters

// Basemap
var basemapLayer = map.createLayer('osm', {
    source: getCookie('basemapChoice', 'osm'),
    gcs: 'EPSG:3857' // web mercator
});

// Tile layer for showing rasters/images with large_image
var tileLayer = map.createLayer('osm', {
    keepLower: false,
    attribution: '',
    autoshareRenderer: false,
});
tileLayer.visible(false)

// Feature/data layer
let layer = map.createLayer('feature', {
    features: ['polygon', 'marker']
});
let reader = geo.createFileReader('geojsonReader', {
    'layer': layer
});

// User Interface layer
var ui = map.createLayer('ui');

// Annotation layer
var annotationLayer = map.createLayer('annotation', {
    clickToEdit: true,
    showLabels: false
});

/////////////////////////////

// Increase zoom range from default of 16
map.zoomRange({
    min: 0,
    max: 20,
})

// Position the map to show data extents. If none present, the position
//   should have been set by the search parameters
function setBounds(extent, setMax = false) {
    if (extent != undefined && extent.xmin != undefined) {
        let xc = (extent.xmax - extent.xmin) * 0.2
        let yc = (extent.ymax - extent.ymin) * 0.2
        if (xc === 0) {
            xc = 0.01
        }
        if (yc === 0) {
            yc = 0.01
        }
        var bounds = {
            left: Math.max(extent.xmin - xc, -180.0),
            right: Math.min(extent.xmax + xc, 180.0),
            top: Math.min(extent.ymax + yc, 89.9999),
            bottom: Math.max(extent.ymin - yc, -89.9999)
        }
        map.bounds(bounds);
        if (setMax) {
            map.maxBounds(bounds)
        } else {
            map.zoom(map.zoom() - 0.25);
        }
    }
}
