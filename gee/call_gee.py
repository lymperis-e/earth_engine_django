import json
import ee
from .app_secrets import *

email       =   email
key_file    =   key_file
credentials =   credentials    

ee.Initialize(credentials)





def computeNDVI(image) :
    '''
    Apply the NDVI computation on a Landsat-8 image
    and return the image with a new 'ndvi' band
    '''
    ndvi = (image.select('B5').subtract(image.select('B4')).divide(image.select('B5').add(image.select('B4')))
                .rename('ndvi'))
    return image.addBands(ndvi).select('ndvi')
    
def computeEVI(image):
    '''
    Apply the NDVI computation on a Landsat-8 image
    and return the image with a new 'evi' band
    '''
    evi = image.expression(
    '2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))', 
    {
      'nir': image.select('B5'),
      'red': image.select('B4'),
      'blue': image.select('B2')
    }
    ).float().rename('evi')
    return image.addBands(evi).select('evi')

def computeNDWI(image):
    '''
    Apply the NDVI computation on a Landsat-8 image
    and return the image with a new 'evi' band
    '''
    ndwi = image.normalizedDifference(['B3', 'B5']).rename('ndwi')
    return image.addBands(ndwi).select('ndwi')


def start_gee_service(geojson):
    ''' Returns a dict with different layers produced by Earth Engine.
    Each layer carries two attributes: label & url
    '''


    aoi = geojson['aoi']
    title = aoi['properties']['NAME']
    polygon = aoi['geometry']['coordinates']
  
    
    #roi = ee.Geometry.Point(22.754573960700434, 37.63424498161601).buffer(7500)
    roi = ee.Geometry.MultiPolygon(polygon)


    L8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1")

          .filter(ee.Filter.date('2021-01-01', '2021-12-31'))
            .filter(ee.Filter.lt('CLOUD_COVER', 20))
          .filterBounds(roi)

          # Crop to AOI
          .map(lambda x: x.clip(roi))
          )

    # Calibration: DNs->Radiance->At-Sensor Reflectance
    # This step is needed for comparative analysis of time series
    L8.map(ee.Algorithms.Landsat.calibratedRadiance)
    L8.map(ee.Algorithms.Landsat.TOA)

    # Sort by Cloud Coverage
    sortedByCloud = ee.ImageCollection(L8.sort('CLOUD_COVER'))

    # Select the image with the maximum cloud coverage
    max_cloud = L8.aggregate_max('CLOUD_COVER')
    print('Max Cloud ::', max_cloud.getInfo())
   
    # Select the image with the minimum cloud coverage
    minCloud = (sortedByCloud.first().clip(roi))

    
    minCloud_TC_tiles = ee.Image(minCloud).getMapId({ 'bands': ['B4', 'B3', 'B2'], 'max':  25000, 'gamma': [0.95, 1.1, 1] } )   #ee.Image({sorter}).getMapId({visParams})
    minCloud_FC_tiles = ee.Image(minCloud).getMapId({ 'bands': ['B5', 'B4', 'B3'], 'max':  22000, 'gamma': [0.95, 1.1, 1] } )

    # Compute NDVI for the day with the minimum cloud cover
    minCloud_NDVI = computeNDVI(minCloud)

    minCloud_NDVI_tiles = ee.Image(minCloud_NDVI).getMapId({'bands':['ndvi'], 'max': 0.54, 'min': -0.1, 'palette': ['red','green']})
    


    return {
        'min_cloud_tc': {
            'label': 'Landsat 8, Minimum Cloud Coverage: True Color Composite',
            'url': minCloud_TC_tiles['mapid']
        },
        'min_cloud_fc': {
            'label': 'Landsat 8, Minimum Cloud Coverage: False Color Composite',
            'url': minCloud_FC_tiles['mapid']
        },
        'min_cloud_ndvi': {
            'label': 'Landsat 8, Minimum Cloud Coverage: NDVI',
            'url': minCloud_NDVI_tiles['mapid']
        }
        
    }
