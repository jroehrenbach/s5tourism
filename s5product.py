
import gdal, ogr

FOOTPRINT_KEY = '/METADATA/EOP_METADATA/om:featureOfInterest/eop:multiExtentOf/gml:surfaceMembers/gml:exterior/NC_GLOBAL#gml:posList'

S5_STANDARD_BANDS = ["qa_value"]
S5_CUSTOM_BANDS = {
   'L2__CLOUD_',
   'L2__AER_AI',
   'L2__AER_LH',
   'L2__SO2___',
   'L2__NP_BD6',
   'L2__CO____',
   'L2__NP_BD7',
   'L2__NO2___',
   'L2__O3____',
   'L2__CH4___',
   'L2__O3_TCL',
   'L2__NP_BD3',
   'L2__HCHO__'
}


def get_polygon(ds):
    # lon lat - order
    values = [float(c) for c in ds.GetMetadataItem[FOOTPRINT_KEY].split()]
    points = ["%f %f"%(lon, lat) for lat, lon in zip(values[1::2], values[::2])]
    return ogr.CreateGeometryFromWkt("POLYGON ((%s))"%(",".join(points)))

def product_covers_region(path, wkt):
    product_polygon = get_polygon(gdal.Open(path))
    region_polygon = ogr.CreateGeometryFromWkt(wkt)
    return region_polygon.Within(product_polygon)

def product_complete(path):
    try:
        os.listdir(path)
        return True
    except:
        return False


class S5Product:
    
    def __init__(self, path, keys):
        path = path + "/" + os.listdir(path)[0]
        self.datasets = {}
        for path, _ in gdal.Open(path).GetSubDatasets():
            for key in keys:
                if key in path:
                    self.datasets[key] = gdal.Open(path)