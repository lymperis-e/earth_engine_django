from django.shortcuts import render 
import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from .call_gee import *

def index(request):
    return render(request, "index.html")


@csrf_exempt
def map(request):

    if request.method == 'GET':     #Default first time loading of the page
        f = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'default_geojson.json'), encoding="utf-8")
        data = json.load(f)
        f.close()
        return render(request, "map.html", {'feature': json.dumps(data)})

    elif request.method == 'POST':      # Async data loading with custom params
        import urllib.parse
        data = json.loads( urllib.parse.unquote(request.body.decode('utf-8'))[5:])
        #data = json.loads(request.body.decode('utf-8'))
        
        return render(request, "map.html", {'feature': json.dumps(data['aoi']), 'year': json.dumps(data['year']) })


    

@csrf_exempt
def asyncEE(request):
    '''Request and return data asynchronously,
    so as to allow new request to the GEE API 
    without reloading the web page'''
    if request.method == 'POST':      # Async data loading with custom params
        data =  json.loads(request.body.decode("utf-8"))
        aoi = data['aoi']
        year = data['year']
        layers = data['layers']

        # Check what layers were requested
        if layers == 'composites':
            gee_data = color_composites(aoi, year)
        elif layers == 'min_cloud_ndvi':
            gee_data = min_cloud_ndvi(aoi, year)
        elif layers == 'max_ndvi':
            gee_data = max_ndvi(aoi, year)
        elif layers == 'max_evi':
            gee_data = max_evi(aoi, year)
        elif layers == 'max_ndwi':
            gee_data = max_ndwi(aoi, year)
        elif layers == 'doy_max_evi':
            gee_data = doy_max_evi(aoi, year)
        elif layers == 'doy_max_ndvi':
            gee_data = doy_max_ndvi(aoi, year)
        elif layers == 'doy_max_ndwi':
            gee_data = doy_max_ndwi(aoi, year)
        
        return JsonResponse(gee_data)






















