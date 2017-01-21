import gdal, ogr, osr
import shapefile
import sys
import utm
import numpy as np
import os
import png
from utils import visualizers as vs
from utils import ray_algorithm as ray

# Global variables
raster_data_path = "/Users/valentina/Documents/project/14SEP10130721-S2AS_R1C1-054168728010_01_P001.TIF"
shp_data_path = '/Users/valentina/Documents/project/parkopedia-villa-maria-sao-paolo/parkopedia-villa-maria-sao-paolo.shp'
cookie_size = 256

def loadGeotiff():
  """
  It loads the geotiff image and converts it to a numpy RGB array. It also extracts the 
  geo-transformation to convert lat-lon to pixel coordinates 
  """
  ## Open and read geotiff
  raster_geotiff = gdal.Open(raster_data_path, gdal.GA_ReadOnly)
  geo_transform = raster_geotiff.GetGeoTransform()

  r = []
  b = []
  g = []
  band_r = raster_geotiff.GetRasterBand(3)
  r.append(band_r.ReadAsArray())
  band_g = raster_geotiff.GetRasterBand(2)
  g.append(band_g.ReadAsArray())
  band_b = raster_geotiff.GetRasterBand(1)
  b.append(band_b.ReadAsArray())

  image_array_RGB = np.dstack([r[:][0],g[:][0],b[:][0]])

  return image_array_RGB, geo_transform

def world2Pixel(geo_transform, x, y):
  """
  Uses a gdal geo_transform (gdal.GetGeoTransform()) to calculate
  the pixel location of a geospatial coordinate 

  The line is a negative index: upper left is at line=0, lowest line is at -16383

  Arguments 
    ---------

    geo_transform : bool
        output of gdal GetGeoTransform() function

    x : int
        latitude in utm 

    y : int
        longitude in utm

  """

  ulX = geo_transform[0]        #/* top left x */
  ulY = geo_transform[3]        #/* top left y */
  xDist = geo_transform[1]        #/* w-e pixel resolution */
  yDist = geo_transform[5]        #/* n-s pixel resolution */ 
  rtnX = geo_transform[2]       #/* rotation, 0 if image is "north up" */
  rtnY = geo_transform[4]       #/* rotation, 0 if image is "north up" */
  pixel = int((x - ulX) / xDist)
  line = abs(int((ulY - y) / yDist))

  return (pixel, line) 

def getPolygons(sf, geo_transform):
  """
  Returns the list of polygons contained in sf.
  Arguments 
    ---------

    sf : shapefile object
      It contains the polygons from the shapefile


    geo_transform : bool
        output of gdal GetGeoTransform() function

  """

  poly_bounds = []

  for polygon in sf.shapeRecords():

    pixel_coords = []
    line_coords = []

    edge_list = []

    for long_point, lat_point in polygon.shape.points:

      # convert lat-long to UTM in accordance to the geotiff coord system
      utm_coords = utm.from_latlon(lat_point, long_point)

      # convert utm to pixel line coords
      xPixel, xLine = world2Pixel(geo_transform, utm_coords[0], utm_coords[1])

      edge_list.append(ray.Point(xLine, xPixel))

    poly_bounds.append(ray.Polygon(edge_list))

  return poly_bounds

def labelParkingPixels(image_size, polygons):
  """
  Returns a binary matrix with 1 if the pixel is contained in any polygon.
  Arguments 
    ---------

    image_size : 1x2 npy array
    	the size of the image


    polygons : list
       	the list of polygons' edges

  """

  parking_binary = np.zeros((image_size[0], image_size[1]), dtype=np.int)

  for poly in polygons:

    [max_x, max_y, min_x, min_y] = poly.getBoundaries()
    num_pixels = 0
    for x in range(min_x, max_x):
      for y in range(min_y, max_y):
        if poly.contains(ray.Point(x, y)):
          num_pixels += 1
          parking_binary[x,y] = 1

  return parking_binary

def main():

  ## read geotiff satellite image
  [image_array_RGB, geo_transform] = loadGeotiff()

  ## read the shapefile with polygons
  sf = shapefile.Reader(shp_data_path)

  ## get the polygons polygons
  polygons = getPolygons(sf, geo_transform)

  ## get matrix of pixel labels (1 = is inside a parking polygon, 0 = otherwise)
  parking_matrix = labelParkingPixels(image_array_RGB.shape, polygons)

  ## save parking_matrix as np array
  np.save('parking_matrix.npy', parking_matrix)


if __name__=="__main__":
  main()

