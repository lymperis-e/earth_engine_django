#1: Split the requests to Earth Engine to avoid Error 429: Too many requests
#2: Implement caching: redirect all EE traffic through an nginx reverse proxy and cache everything with memcache