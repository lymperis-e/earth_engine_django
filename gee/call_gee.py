import json
import ee
from .app_secrets import *

email       =   email
key_file    =   key_file
credentials =   credentials    

ee.Initialize(credentials)







def start_gee_service(geojson):
    ''' Returns a dict with different layers produced by Earth Engine
    Each layer has two attributes: label & url'''


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

    # Cloud Coverage
    sortedByCloud = ee.ImageCollection(L8.sort('CLOUD_COVER'))


    max_cloud = L8.aggregate_max('CLOUD_COVER')
    #print('Max Cloud ::', max_cloud)
   
  

    minCloud = (sortedByCloud.first().clip(roi))

    minCloud_TrueColor = {
        'bands': ['B4', 'B3', 'B2'],
        'max':  25000,
        'gamma': [0.95, 1.1, 1]
    }
    minCloud_FalseColor = {
        'bands': ['B5', 'B4', 'B3'],
        'max':  22000,
        'gamma': [0.95, 1.1, 1]
    }


    minCloud_TC = ee.Image(minCloud).getMapId(minCloud_TrueColor)
    minCloud_FC = ee.Image(minCloud).getMapId(minCloud_FalseColor)




    return {
        'min_cloud_tc': {
            'label': 'Landsat 8, Minimum Cloud Coverage: True Color Composite',
            'url': minCloud_TC['mapid']
        },
        'min_cloud_fc': {
            'label': 'Landsat 8, Minimum Cloud Coverage: False Color Composite',
            'url': minCloud_FC['mapid']
        }
        
    }
