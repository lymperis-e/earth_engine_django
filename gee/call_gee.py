import json
import ee
from .app_secrets import *

email       =   email
key_file    =   key_file
credentials =   credentials    

ee.Initialize(credentials)


#def pixelValue(image, band,  x, y):
#    geom = ee.Geometry.Point(x, y)


def mean_stddev(image, band):
    '''
    Calculate the mean & standard dev for an
    ee.Image and return it, for display and 
    visual parameter setting
    '''
    stdDev = image.select(band).reduceRegion(ee.Reducer.stdDev()).getInfo()[band]
    mean = image.select(band).reduceRegion(ee.Reducer.mean()).getInfo()[band]
    print("Std Dev {} : ".format(band), stdDev)
    print("Mean {} : ".format(band), mean)
    return {'mean': mean, 'stddev': stdDev}

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



def color_composites(aoi, year) -> dict:
    '''
    Compute True & False color composites for the
    day with the minimum cloud coverage of the year
    '''
    L8  = start_gee_service(aoi, year)['L8']
    roi = start_gee_service(aoi, year)['roi']

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

    return {
        'min_cloud_tc': {
            'label': 'True Color Composite',
            'url': minCloud_TC_tiles['mapid']
        },
        'min_cloud_fc': {
            'label': 'False Color Composite',
            'url': minCloud_FC_tiles['mapid']
        }
    }

def min_cloud_ndvi (aoi, year):
    '''
    Compute the NDVI for the day with the minimum
    cloud coverage of the year
    '''
    L8  = start_gee_service(aoi, year)['L8']
    roi = start_gee_service(aoi, year)['roi']

    # Sort by Cloud Coverage
    sortedByCloud = ee.ImageCollection(L8.sort('CLOUD_COVER'))

    # Select the image with the minimum cloud coverage
    minCloud = (sortedByCloud.first().clip(roi))

    # Compute NDVI for the day with the minimum cloud cover
    minCloud_NDVI = computeNDVI(minCloud)

    # Calculate mean & stddev, to set the visualisation parameters 
    mean = mean_stddev(minCloud_NDVI, 'ndvi')['mean']
    stdDev = mean_stddev(minCloud_NDVI, 'ndvi')['stddev']

    minCloud_NDVI_tiles = ee.Image(minCloud_NDVI).getMapId({'bands':['ndvi'], 'max': (mean+2*stdDev), 'min':  (mean-2*stdDev), 'palette': ['red','green']})

    return {
        'min_cloud_ndvi': {
            'label': 'Landsat 8, Minimum Cloud Coverage: NDVI',
            'url': minCloud_NDVI_tiles['mapid']
        }
    }


def max_ndvi(aoi, year):
    '''
    Compute the maximum values of 3 common indices:
    NDVI, EVI, NDWI
    '''
    L8  = start_gee_service(aoi, year)['L8']
    roi = start_gee_service(aoi, year)['roi']

    # Map NDVI, NDWI & EVI computation functions over the whole time series
    NDVI = L8.map(computeNDVI)

    
    #Calculate max NDVI/EVI/NDWI per pixel in the time series, via temporal reduction
    maxNDVI = NDVI.reduce(ee.Reducer.max())


    maxNDVI_tiles = ee.Image(maxNDVI).getMapId({'bands':['ndvi_max'], 'max': -0.5, 'min': 1, 'palette': ['red','green']})    


    return {
        'max_ndvi': {
            'label': 'Max NDVI/pixel ',
            'url': maxNDVI_tiles['mapid']
        },
    }

def max_evi(aoi, year):
    '''
    Compute the maximum values of 3 common indices:
    NDVI, EVI, NDWI
    '''
    L8  = start_gee_service(aoi, year)['L8']
    roi = start_gee_service(aoi, year)['roi']

    # Map EVI computation functions over the whole time series
    EVI  = L8.map(computeEVI)
    
    #Calculate max EVI per pixel in the time series, via temporal reduction
    maxEVI  = EVI.reduce(ee.Reducer.max())
    maxEVI_tiles  = ee.Image(maxEVI).getMapId({'bands':['evi_max'],   'max': -0.5, 'min': 1, 'palette': ['red','green']})

    return {
        'max_evi': {
            'label': 'Max EVI/pixel ',
            'url': maxEVI_tiles['mapid']
        },
    }

def max_ndwi(aoi, year):
    '''
    Compute the maximum values of 3 common indices:
    NDVI, EVI, NDWI
    '''
    L8  = start_gee_service(aoi, year)['L8']
    roi = start_gee_service(aoi, year)['roi']

    # Map  NDWI  computation functions over the whole time series
    NDWI = L8.map(computeNDWI)
    
    #Calculate max NDWI per pixel in the time series, via temporal reduction
    maxNDWI = NDWI.reduce(ee.Reducer.max())
    maxNDWI_tiles = ee.Image(maxNDWI).getMapId({'bands':['ndwi_max'], 'max': -0.5, 'min': 1, 'palette': ['red','green']})

    return {
        'max_ndwi': {
            'label': 'Max NDWI/pixel ',
            'url': maxNDWI_tiles['mapid']
        },
    }





def doy_max_ndvi(aoi, year):
    '''
    Compute the Day Of the Year (DOY) on which the
    maximum values of NDVI, EVI & NDWI occured
    '''
    L8  = start_gee_service(aoi, year)['L8']

    # Map NDVI, NDWI & EVI computation functions over the whole time series
    NDVI = L8.map(computeNDVI)
 
    # Map the NDVI ImageCollection to addDate, then temporally reduce it.
    DoyMaxNdvi = NDVI.map(addDate).qualityMosaic('ndvi').select('DOY')
    DoyMaxNdvi_tiles = ee.Image(DoyMaxNdvi).getMapId({'bands':['DOY'],  'max': 365, 'min': 1, 'palette': ['white', 'blue','green','yellow','red']})           
            

    return {
        'doy_max_ndvi' :{
            'label':'Max NDVI: Day-of-Year',
            'url'  : DoyMaxNdvi_tiles['mapid']
        }
    }

def doy_max_evi(aoi, year):
    '''
    Compute the Day Of the Year (DOY) on which the
    maximum values of NDVI, EVI & NDWI occured
    '''
    L8  = start_gee_service(aoi, year)['L8']

    # Map EVI computation functions over the whole time series
    EVI  = L8.map(computeEVI)
    
    # Map the date from the image metadata to each pixel and
    # calculate max EVI per pixel in the time series, via temporal reduction
    DoyMaxEvi = EVI.map(addDate).qualityMosaic('evi').select('DOY')
    DoyMaxEvi_tiles  = ee.Image(DoyMaxEvi).getMapId({'bands':['DOY'],   'max': 365, 'min': 1, 'palette': ['white', 'blue','green','yellow','red']})           
       
    return {
        'doy_max_evi' :{
            'label':'Max EVI: Day-of-Year',
            'url'  : DoyMaxEvi_tiles['mapid']
        }
    }


def doy_max_ndwi(aoi, year):
    '''
    Compute the Day Of the Year (DOY) on which the
    maximum values of NDWI occured
    '''
    L8  = start_gee_service(aoi, year)['L8']

    # Map EVI computation functions over the whole time series
    NDWI  = L8.map(computeEVI)
    
    # Map the date from the image metadata to each pixel and
    # calculate max EVI per pixel in the time series, via temporal reduction
    DoyMaxNdvi = NDWI.map(addDate).qualityMosaic('evi').select('DOY')
    DoyMaxNdwi_tiles  = ee.Image(DoyMaxNdvi).getMapId({'bands':['DOY'],   'max': 365, 'min': 1, 'palette': ['white', 'blue','green','yellow','red']})           

    return {
        'doy_max_evi' :{
            'label':'Max EVI: Day-of-Year',
            'url'  : DoyMaxNdwi_tiles['mapid']
        }
    }






def start_gee_service(aoi, year):
    ''' 
    Authenticate against EE with a Service Account,
    Initialize an EE server-side script and return the 
    client-side objects for different evaluation methods
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

    return {
            'L8': L8,
            'roi': roi
            } 



