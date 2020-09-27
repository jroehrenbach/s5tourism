"""
Description
-----------
GDAL wrapper module for reading and writing raster-files
"""

import gdal
import numpy as np

from ctrans import transformation_from_dataset


def create_raster_file(path, arrays, geotransform=None, projection=None,
	dtype=None, driver='GTiff'):
	"""
	Create raster-file and save arrays and geospatial information

	Parameters
	----------
	path : str
		Path to new raster-file
	arrays : list
		List of arrays to save to raster-file
	geotransform : tuple, optional
	projection : str, optional
	dtype : int, optional
		GDAL data type (gdal.GDT*)
	driver : str, optional
		Name of raster-driver
	"""
	h, w = arrays[0].shape
	count = len(arrays)
	driver = gdal.GetDriverByName(driver)
	if dtype == None:
		dtype = 1
	dataset = driver.Create(path, w, h, count, dtype)
	if projection != None:
		dataset.SetProjection(projection)
	if geotransform != None:
		dataset.SetGeoTransform(geotransform)
	for i, array in enumerate(arrays):
		band = dataset.GetRasterBand(i+1)
		band.WriteArray(array)
	dataset = None


class Raster(object):
	"""
	Wrapper object for raster data of GDAL Band
	"""

	def __init__(self, dataset, band_index=1, qv=None, ct=None):
		"""
		Parameters
		----------
		dataset : gdal.Dataset
		band_index : int
			Index of raster band in GDAL-Dataset
		qv : int, optional
			Quantification value
		"""
		self.shape = dataset.RasterYSize, dataset.RasterXSize
		self.band = dataset.GetRasterBand(band_index)
		self.qv = qv
		if ct == None:
			self.ct = transformation_from_dataset(dataset)
		else:
			self.ct = ct

	def get_data(self, x=0, y=0, w=None, h=None, buf_obj=None, resample_alg=0,
		scaled=False):
		"""
		Extract raster data from GDAL-Band

		Parameters
		----------
		x : int, optional
		y : int, optional
		w : None or int, optional
			If None, w will be maximum width
		h : None or int, optional
			If None, h will be maximum height
		buf_obj : None or np.ndarray, optional
			Buffer array which has shape and data type of target array
		resample_alg : int, optional
			Resample algorithm
			{
				0: GRA_NearestNeighbour,
				1: GRA_Bilinear,
				2: GRA_Cubic,
				3: GRA_CubicSpline,
				4: GRA_Lanczos,
				5: GRA_Average,
				6: GRA_Mode,
				8: GRA_Max,
				9: GRA_Min,
				10: GRA_Med,
				11: GRA_Q1,
				12: GRA_Q3
			}
		scaled : bool, optional
			If true, extracted data will be devided by quantification value (qv)

		Returns
		-------
		np.ndarray
		"""
		if not (0 <= y < self.shape[0] and 0 <= x < self.shape[1]):
			# offset out of bounds
			return
		x, y = int(x), int(y)
		w = int(w) if w != None else w
		h = int(h) if h != None else h
		# read raster data from GDAL-Band
		data = self.band.ReadAsArray(x, y, w, h, buf_obj=buf_obj,
			resample_alg=resample_alg)
		if scaled and self.qv != None and data != None:
			# apply quantification value (qv)
			data = data / self.qv
		return data

	def get_matchup(self, lat, lon, scaled=True):
		"""
		Read single point from raster by passing coordinates

		Parameters
		----------
		lat, lon : float
			Latitude and Longitude coordinates in decimal degree
		scaled : bool, optional
			If true, extracted data will be devided by quantification value (qv)
		"""
		y, x = self.ct.degree_to_pixel(lat, lon)
		data = self.get_data(x, y, 1, 1, scaled=scaled)
		return data[0,0] if data != None else None

	def get_matchups(self, lats, lons, scaled=True):
		"""
		"""
		# get pixel coordinates
		y, x = self.ct.degree_to_pixel(lats, lons)

		# check which coordinates are within boundaries
		sel = (y>=0) & (y<self.shape[0]) & (x>=0) & (x<self.shape[1])

		# get pixel coordinate boundaries
		y0, y1, x0, x1 = y[sel].min(), y[sel].max(), x[sel].min(), x[sel].max()

		# read subset-array within boundaries from raster
		data = self.get_data(x0, y0, x1-x0+1, y1-y0+1, scaled=scaled)
		
		# extract points which are within boundaries
		return np.where(sel, data[y-y0, x-x0], np.nan)


if __name__ == '__main__':
	path = '../cashew/S2B_MSIL2A_20200711T071619_N0214_R006_T37LFJ_20200711T113821_TILE.tif'
	ds = gdal.Open(path)
	raster = Raster(ds)
	y, x = np.array([[-1, 2, 3, 0], [2, -1, 2, 1]])
	lats, lons = raster.ct.pixel_to_degree(y, x)
	matchups = raster.get_matchups(lats, lons)