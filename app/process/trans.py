import math

from pyproj import Transformer

_TRANSFORMER = Transformer.from_crs("epsg:4326", "epsg:3857")


def epsg4326_to_3857(lng, lat):
    x, y = _TRANSFORMER.transform(lat, lng)
    return x, y


def float_format(x):
    return float(format(x, '.4f'))


def ff(x):
    return float(format(x, '.2f'))


def l2_distance(o1, o2):
    dist = 0
    for i in range(len(o1)):
        dist += (o1[i] - o2[i]) ** 2
    return math.sqrt(dist)
