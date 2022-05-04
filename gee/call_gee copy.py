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

def addDate(image):
    '''
    Parse the metadata of an ee.Image and add it as 
    the Day Of The Year to a new band (DOY)
    '''
    image = ee.Image(image)
    return image.addBands(ee.Image.constant(ee.Number.parse(image.date().format("D"))).rename('DOY').float())




def start_gee_service(aoi, year):
    ''' 
    Returns a dict with different layers produced by Earth Engine.
    Each layer carries two attributes: label & url
    '''

    title = aoi['properties']['NAME']
    polygon = aoi['geometry']['coordinates']
  
    
    #roi = ee.Geometry.Point(22.754573960700434, 37.63424498161601).buffer(7500)
    roi = ee.Geometry.MultiPolygon(polygon)
    

    L8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1")
            .filter(ee.Filter.date('{}-01-01'.format(year), '{}-12-31'.format(year)))
            .filter(ee.Filter.lt('CLOUD_COVER', 20))
            .filterBounds(roi)      
            .map(lambda x: x.clip(roi))  # Crop to AOI
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

    # Create True & False color composites
    minCloud_TC_tiles = ee.Image(minCloud).getMapId({ 'bands': ['B4', 'B3', 'B2'], 'max':  25000, 'gamma': [0.95, 1.1, 1] } )   #ee.Image({sorter}).getMapId({visParams})
    minCloud_FC_tiles = ee.Image(minCloud).getMapId({ 'bands': ['B5', 'B4', 'B3'], 'max':  22000, 'gamma': [0.95, 1.1, 1] } )

    # Compute NDVI for the day with the minimum cloud cover
    minCloud_NDVI = computeNDVI(minCloud)
    minCloud_NDVI_tiles = ee.Image(minCloud_NDVI).getMapId({'bands':['ndvi'], 'max': 0.54, 'min': -0.1, 'palette': ['red','green']})

    # Map NDVI, NDWI & EVI computation functions over the whole time series
    NDVI = L8.map(computeNDVI)
    EVI  = L8.map(computeEVI)
    NDWI = L8.map(computeNDWI)
    
    #Calculate max NDVI/EVI/NDWI per pixel in the time series, via temporal reduction
    maxNDVI = NDVI.reduce(ee.Reducer.max())
    maxEVI  = EVI.reduce(ee.Reducer.max())
    maxNDWI = NDWI.reduce(ee.Reducer.max())

    maxNDVI_tiles = ee.Image(maxNDVI).getMapId({'bands':['ndvi_max'], 'max': -0.5, 'min': 1, 'palette': ['red','green']})    
    maxEVI_tiles  = ee.Image(maxEVI).getMapId({'bands':['evi_max'],   'max': -0.5, 'min': 1, 'palette': ['red','green']})
    maxNDWI_tiles = ee.Image(maxNDWI).getMapId({'bands':['ndwi_max'], 'max': -0.5, 'min': 1, 'palette': ['red','green']})


    # Map the NDVI ImageCollection to addDate, then temporally reduce it.
    # As the images in the collection only have one band, we can use
    # 'qualityMosaic' equivalently to 'Reducer.max'. We opt for it for
    # demonstrative purposes. Do the same with EVI, NDWI
    DoyMaxNdvi = NDVI.map(addDate).qualityMosaic('ndvi').select('DOY')
    DoyMaxEvi = EVI.map(addDate).qualityMosaic('evi').select('DOY')
    DoyMaxNdwi = NDWI.map(addDate).qualityMosaic('ndwi').select('DOY')

  
    DoyMaxNdvi = ee.Image(DoyMaxNdvi).getMapId({'bands':['DOY'],  'max': 365, 'min': 1, 'palette': ['white', 'blue','green','yellow','red']})           
    DoyMaxEvi  = ee.Image(DoyMaxEvi).getMapId({'bands':['DOY'],   'max': 365, 'min': 1, 'palette': ['white', 'blue','green','yellow','red']})           
    DoyMaxNdwi = ee.Image(DoyMaxNdwi).getMapId({'bands':['DOY'],  'max': 365, 'min': 1, 'palette': ['white', 'blue','green','yellow','red']})           



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
        },
        'max_ndvi': {
            'label': 'Max NDVI/pixel ',
            'url': maxNDVI_tiles['mapid']
        },
        'max_evi': {
            'label': 'Max EVI/pixel ',
            'url': maxEVI_tiles['mapid']
        },
        'max_ndwi': {
            'label': 'Max NDWI/pixel ',
            'url': maxNDWI_tiles['mapid']
        },
        'doy_max_ndvi' :{
            'label':'Max NDVI: Day-of-Year',
            'url'  : DoyMaxNdvi['mapid']
        },
        'doy_max_evi' :{
            'label':'Max EVI: Day-of-Year',
            'url'  : DoyMaxEvi['mapid']
        },
        'doy_max_ndwi' :{
            'label':'Max NDWI: Day-of-Year',
            'url'  : DoyMaxNdwi['mapid']
        }
        
    }
