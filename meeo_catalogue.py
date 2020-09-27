
import requests
import json
from datetime import datetime, timedelta
import ogr

OFFL_CATALOGUE_URL = "https://meeo-s5p.s3.amazonaws.com/COGT/OFFL/catalog.json"

get_catalogue = lambda url: json.loads(requests.get(url).text)


class Catalogue:

	def __init__(self, json_url):
		self._dict = get_catalogue(json_url)
		self.children = self.get_links("child")
		self.items = self.get_links("item")

	def get_links(self, rel):
		return {
			element["title"]: element["href"]
			for element in self._dict["links"]
			if element["rel"] == rel
		}

	def get_child_catalogue(self, title):
		if not title in self.children:
			return None
		url = self.children[title]
		return Catalogue(url)


class OFFL(Catalogue):
	def __init__(self):
		Catalogue.__init__(self, OFFL_CATALOGUE_URL)


class Item:

	def __init__(self, json_url):
		self._dict = get_catalogue(json_url)
		self.assets = {
			k: v["href"] for k, v in self._dict
		}

	def covers_region(self, region_wkt):
		points = self._dict['geometry']['coordinates'][0][0]
		wkt = "POLYGON ((%s))"%(",".join(["%f %f"%tuple(p)
			for p in points]))
		poly = ogr.CreateGeometryFromWkt(wkt)
		return ogr.CreateGeometryFromWkt(region_wkt).Within(poly)


def get_products(dt0, dt1, product_type, region_wkt):
	cat = OFFL().get_child_catalogue(product_type)
	items = {}
	for dt in [dt0 + timedelta(d) for d in range((dt1 - dt0).days)]:
		ycat = cat.get_child_catalogue("%d"%dt.year)
		if ycat == None:
			continue
		mcat = ycat.get_child_catalogue("%02d"%dt.month)
		if mcat == None:
			continue
		dcat = mcat.get_child_catalogue("%02d"%dt.day)
		if dcat == None:
			continue
		for key, url in dcat.items.items():
			item = Item(url)
			if not item.covers_region(region_wkt):
				continue
			items[key] = item.assets
	return items

vienna_wkt = "POLYGON ((16.193377 48.228980, 16.424090 48.317641, 16.593004 48.223948, 16.424776 48.122750, 16.23209 48.123209, 16.193377 48.228980))"


if __name__ == "__main__":
	dt0 = datetime(2020, 1, 1)
	dt1 = datetime(2020, 2, 1)
	product_type = "Sulphur Dioxide (SO2) total column"
	items = get_item_catalogues(dt0, dt1, product_type, vienna_wkt)
