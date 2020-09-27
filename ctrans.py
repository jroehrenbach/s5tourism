"""
Description
-----------
GDAL wrapper-module for coordinate transformation of geo-rasters
"""

import osr
import gdal
import numpy as np

is_iterable = lambda obj: hasattr(obj, '__getitem__')

def transformation_from_dataset(dataset):
	"""
	Create Transformation from GDAL-Dataset
	"""
	projection = dataset.GetProjection()
	geotransform = dataset.GetGeoTransform()
	return Transformation(projection, geotransform)


class Transformation(object):
	"""
	Wrapper-object for translating geo-raster coordinates
	"""

	def __init__(self, projection, geotransform):
		"""
		Parameters
		----------
		projection : str
			Projection-Wkt; can be returned by calling
			gdal.Dataset.GetProjection()
		geotransform : tuple
			Geo-Transform; can be returned by calling
			gdal.Dataset.GetGeoTransform()
			order: xoff, xdx, xdy, yoff, ydx, ydy (in meters)
		"""
		# set source spatial reference
		ssr = osr.SpatialReference()
		if int(gdal.VersionInfo()[0]) >= 3:
			# for GDAL-Version >= 3 use traditional GIS order
			#TODO use new GIS order as standard
			ssr.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
		ssr.ImportFromWkt(projection)

		# get target spatial reference
		tsr = ssr.CloneGeogCS()

		self.ct = osr.CoordinateTransformation(ssr, tsr)
		self.ct_rev = osr.CoordinateTransformation(tsr, ssr)
		self.gt = geotransform
		self.prj = projection

	def pixel_to_meter(self, py, px):
		"""
		Translate pixel coordinates to meter coordinates
		"""
		x = self.gt[0] + (px * self.gt[1]) + (py * self.gt[2])
		y = self.gt[3] + (px * self.gt[4]) + (py * self.gt[5])
		return y, x

	def meter_to_degree(self, y, x):
		"""
		Translate meter coordinates to degree coordinates
		"""
		if is_iterable(y):
			points = np.array([x, y]).T
			lon, lat, _ = np.array(self.ct.TransformPoints(points)).T
		else:
			lon, lat, _ = self.ct.TransformPoint(x, y)
		return lat, lon

	def pixel_to_degree(self, py, px):
		"""
		Translate pixel coordinates to degree coordinates
		"""
		y, x = self.pixel_to_meter(py, px)
		return self.meter_to_degree(y, x)

	def degree_to_meter(self, lat, lon):
		"""
		Translate degree coordinates to meter coordinates
		"""
		if is_iterable(lat):
			points = np.array([lon, lat]).T
			x, y, _ = np.array(self.ct_rev.TransformPoints(points)).T
		else:
			x, y, _ = self.ct_rev.TransformPoint(lon, lat)
		return y, x

	def meter_to_pixel(self, y, x):
		"""
		Translate meter coordinates to pixel coordinates
		"""
		px = np.round((x - self.gt[0]) / self.gt[1]).astype(int)
		py = np.round((y - self.gt[3]) / self.gt[5]).astype(int)
		return py, px

	def degree_to_pixel(self, lat, lon):
		"""
		Translate degree coordinates to pixel coordinates
		"""
		y, x = self.degree_to_meter(lat, lon)
		return self.meter_to_pixel(y, x)


if __name__ == '__main__':
	ds = gdal.Open('../cashew/S2B_MSIL2A_20200711T071619_N0214_R006_T37LFJ_20200711T113821_TILE.tif')
	ct = transformation_from_dataset(ds)
	lats = np.array([-10.31075  , -10.3115556, -10.3112222, -10.3120833])
	lons = np.array([40.1345556, 40.1336111, 40.1355556, 40.1345   ])
	y,x = ct.degree_to_pixel(lats, lons)
	print(ct.pixel_to_degree(y,x))