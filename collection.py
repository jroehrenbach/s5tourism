"""
Description
-----------
GDAL wrapper module for reading raster-files with multiple rasters or
collections of raster-files
"""

import gdal

from raster import Raster
from ctrans import transformation_from_dataset


class Collection(object):
	"""
	Object that can hold multiple rasters
	"""

	def __init__(self, filedict=None, quantification_values=None):
		"""
		Parameters
		----------
		filedict : dict, optional
			Contains filenames and names for raster-indices (indexdict).
			Example:
			filedict = {
				'example.tif': {
					1: 'red-band',
					2: 'green-band',
					3: 'blue-band'
				}
			}
		"""
		self._datasets = [] # list of GDAL-Datasets
		self.rasters = {} # dict with Rasters
		if filedict != None:
			for path, indexdict in filedict.items():
				if quantification_values == None:
					qv = None
				else:
					qv = quantification_values[path]
				self.add_rasters(path, indexdict, qv)

	def add_rasters(self, path, indexdict=None, qv=None):
		"""
		Add any raster bands from raster-file as Raster

		Parameters
		----------
		path : str
			Path to raster-file
		indexdict : dict, optional
			Contains names for raster-indices, where key is GDAL-Band index
			and value is the key for the Raster in Collection.rasters
		qv : int, optional
			Quantification value
		"""
		# open GDAL-Dataset
		dataset = gdal.Open(path)
		ct = transformation_from_dataset(dataset)

		if indexdict == None:
			# add all rasters to indexdict
			keys = range(1, dataset.RasterCount + 1)
			rc = len(self.rasters)
			names = range(len(self.rasters), len(self.rasters) +
				dataset.RasterCount)
			indexdict = dict(zip(keys, names))

		for index, name in indexdict.items():
			# add raster-band as Raster to Collection.rasters
			self.rasters[name] = Raster(dataset, index, qv, ct)

		self._datasets.append(dataset)

	def get_matchup(self, lat, lon, scaled=True, raster_keys=None):
		"""
		Extract location match-up

		Parameters
		----------
		lat, lon : float
			Latitude and longitude coordinate of point (decimal degrees)
		scaled : bool, optional
			If true, data values will be devided by raster quantification value
			(Raster.qv)
		raster_keys : list or None, optional
			list of raster keys to be extracted. If None, all rasters will be
			extracted

		Return
		------
		matchup as dict
		"""
		if raster_keys == None:
			raster_keys = self.rasters.keys()
		return {
			key: self.rasters[key].get_matchup(lat, lon, scaled)
			for key in raster_keys
		}