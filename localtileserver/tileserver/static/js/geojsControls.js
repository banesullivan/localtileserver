// Fill select drop down
var options = geo.osmLayer.tileSources;
for (const option in options) {
    var newOption = document.createElement('option');
    newOption.value = option;
    newOption.text = options[option].name ? options[option].name : option;
    document.getElementById('basemapDropdown').appendChild(newOption)
}

var basemapDropdown = document.getElementById("basemapDropdown")
basemapDropdown.value = basemapLayer.source()

function changeBasemap() {
    if (basemapDropdown.value == '-- none --') {
        basemapLayer.visible(false)
    } else {
        basemapLayer.visible(true)
        setCookie('basemapChoice', basemapDropdown.value)
        basemapLayer.source(basemapDropdown.value)
    }
}


var b1 = document.getElementById("drawROIButton")
var b2 = document.getElementById("extractROIButton")
var b3 = document.getElementById("clearROIButton")
var roi;

// Add callback to annotation layer
annotationLayer.geoOn(geo.event.annotation.state, (e) => {
    if (e.annotation.state() === "edit") {
        // Prevent downloading while editing as last complete state is used and
        //   could yield seemingly wrong results
        b2.disabled = true
    } else if (e.annotation.state() === "done") {
        var coords = e.annotation.coordinates();
        // Re-enable button
        b1.disabled = false
        b2.disabled = false
        // Get the bounding box
        roi = {
            left: coords[0].x,
            right: coords[1].x,
            bottom: coords[1].y,
            top: coords[2].y
        };
        var xx = coords.forEach((p) => {
            if (p.x < roi.left) {
                roi.left = p.x
            }
            if (p.x > roi.right) {
                roi.right = p.x
            }
            if (p.y < roi.bottom) {
                roi.bottom = p.y
            }
            if (p.y > roi.top) {
                roi.top = p.y
            }
        });
    }
});

function enableDrawROI() {
    // Disable button until completed
    b1.disabled = true
    b2.disabled = true
    // Make sure clear button is enabled
    b3.disabled = false
    // Clear any previous annotations
    annotationLayer.removeAllAnnotations()
    // Start new annotation
    annotationLayer.mode('rectangle');
}

function downloadROI() {
    // Check if ROI is outside of the bounds of raster as this will
    //   yield invalid results
    if (roi.left < extents.xmin |
        roi.right > extents.xmax |
        roi.top > extents.ymax |
        roi.bottom < extents.ymin) {
        console.log('ROI exceeds the boundary of the source raster.')
        // TODO: show toast with error message
        return
    }
    // Build a URL for extracting that ROI
    var url = `${host}/world/region.tif?units=EPSG:4326&left=${roi.left}&right=${roi.right}&bottom=${roi.bottom}&top=${roi.top}&filename=${filename}`;
    download(url, 'region.tif')
}

function clearROI() {
    annotationLayer.removeAllAnnotations()
    b1.disabled = false
    b2.disabled = true
    b3.disabled = true
}
