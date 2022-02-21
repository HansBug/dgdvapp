from pyproj import Transformer

_TRANSFORMER = Transformer.from_crs("epsg:4326", "epsg:3857")


def epsg4326_to_3857(lng, lat):
    x, y = _TRANSFORMER.transform(lat, lng)
    return x, y
