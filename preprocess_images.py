import gdal, ogr, osr
import shapefile
import sys
import utm
import numpy as np
import pdb
from matplotlib import pyplot as pyp2
import random
import os
from utils import visualizers as vs
import png

# Global variables
raster_data_path = "/Users/valentina/Documents/project/14SEP10130721-S2AS_R1C1-054168728010_01_P001.TIF"
shp_data_path = '/Users/valentina/Documents/project/parkopedia-villa-maria-sao-paolo/parkopedia-villa-maria-sao-paolo.shp'
cookie_size = 256
cookie_overlap = cookie_size / 4 ## number of overlapping pixels for segmentations 
output_folder = 'cookies'
random_seed = 12347 ## To aid reproducibility

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

def getCookie(image_array_RGB, line_start, pixel_start):
  """
  Segment the image: given the coord line-pixel, it 
  extracts the corresponding cookie with (cookie_size x cookie_size)
  
  Arguments 
    ---------

    image_array_RGB : numpy array
        RGB image extracted from the geotiff

    line_start : int
        row index of the image corresponding to the cookie first row  

    pixel_start : int
        column index of the image corresponding to the cookie first column

  """
  return image_array_RGB[line_start:(line_start + cookie_size), pixel_start:(pixel_start+cookie_size)].copy() # Defensive copy

def assignLabelToCookie(poly_bounds, line_start, pixel_start):
  """
  Check if the coords (pixel_start, line_start) are inside the polygon that 
  indicate the parking lot
  Arguments 
    ---------

    poly_bounds : list
        It contains the boundaries of all the polygons

    line_start : int
        row index of the image corresponding to the cookie first row  

    pixel_start : int
        column index of the image corresponding to the cookie first column

  """

  for poly_no in range(0, len(poly_bounds)):

    #check if cookie is fully inside the polygon
    offset_array = [0, 100]

    for offset in offset_array:

      is_line_start_in_poly = (line_start>poly_bounds[poly_no][0]+offset) and (line_start<poly_bounds[poly_no][1]-offset)
      is_line_end_in_poly = (line_start+cookie_size>poly_bounds[poly_no][0]+offset) and (line_start+cookie_size<poly_bounds[poly_no][1]-offset)

      if ((offset==0 and (is_line_start_in_poly and is_line_end_in_poly)) or \
        (offset==100 and (is_line_start_in_poly or is_line_end_in_poly))):

        is_pixel_start_in_poly = (pixel_start>poly_bounds[poly_no][2]+offset) and (pixel_start<poly_bounds[poly_no][3]-offset)
        is_pixel_end_in_poly = (pixel_start+cookie_size>poly_bounds[poly_no][2]+offset) and (pixel_start+cookie_size<poly_bounds[poly_no][3]-offset)
        
        if ((offset==0 and (is_pixel_start_in_poly and is_pixel_end_in_poly)) or \
          (offset==100 and (is_pixel_start_in_poly or is_pixel_end_in_poly))):
          return 1

  return 0

def saveCookieAsPNG(cookie_name, cookie_npy):
  """
  Save cookie_npy as a color PNG.
  Arguments 
    ---------

    cookie_name : string
        Name of the .png file containing the cookie

    cookie_npy : numpy array
        Numpy array of the RGB cookie  

  """

  cookie_npy *= (255.0/cookie_npy.max())

  with open(cookie_name, 'wb') as f:

      writer = png.Writer(width=cookie_npy.shape[1], height=cookie_npy.shape[0])

      # Convert cookie_npy to a list of lists expected by the png writer.
      cookie_list = cookie_npy.reshape(-1, cookie_npy.shape[1]*cookie_npy.shape[2]).tolist()
      writer.write(f, cookie_list)
  
def getPolygonBounds(sf, geo_transform):
  """
  Save cookie_npy as a color PNG.
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

    for long_point, lat_point in polygon.shape.points:

      # convert lat-long to UTM in accordance to the geotiff coord system
      utm_coords = utm.from_latlon(lat_point, long_point)

      # convert utm to pixel line coords
      xPixel, xLine = world2Pixel(geo_transform, utm_coords[0], utm_coords[1])
      
      pixel_coords.append(xPixel)
      line_coords.append(xLine)

    poly_bounds.append([min(line_coords), max(line_coords), min(pixel_coords), max(pixel_coords)])

  return poly_bounds

def extractCookies(image_array_RGB, poly_bounds):
  """
  It extract all the cookies from the geotiff and put it into a list
  Arguments 
    ---------

    image_array_RGB : numpy array
        RGB image extracted from the geotiff

    poly_bounds : list
        It contains the boundaries of all the polygons

  """
  #offset to remove the first and last 200 rows and lines of the image that are black
  offset_image = 200

  idx_to_img = []
  idx_to_label = []
  idx_to_name = []

  for line_start_coord in range(offset_image, image_array_RGB.shape[0] - offset_image, cookie_overlap):

    cookie = []
    cookie_label = []

    for pixel_start_coord in range(offset_image, image_array_RGB.shape[1] - offset_image, cookie_overlap):

      idx_to_img.append(getCookie(image_array_RGB, line_start_coord, pixel_start_coord))
      cookie_label = assignLabelToCookie(poly_bounds, line_start_coord, pixel_start_coord)
      idx_to_label.append(cookie_label)
      idx_to_name.append('_'.join(['label', str(cookie_label), 'cookie', str(line_start_coord), str(pixel_start_coord), '.png']))

  return idx_to_img, idx_to_label, idx_to_name

def saveImages(negative_cookies, positive_cookies, idx_to_name, idx_to_label, idx_to_img):
  """
  It extract all the cookies from the geotiff and put it into a list
  Arguments 
    ---------

    negative_cookies : 

    positive_cookies : 

    idx_to_name : 

    idx_to_label : 

    idx_to_img :

  """
  output_path = '/' + output_folder + '_' + str(cookie_size)
  current_path = os.getcwd()

  if not(os.path.exists('.' + output_path)):

    os.mkdir(output_path)

  training_labels = []

  folder_dir = current_path + output_path + '/' 
  for idx in range(0, len(positive_cookies)):

    training_labels.append(folder_dir + idx_to_name[negative_cookies[idx]] + ' ' + str(idx_to_label[negative_cookies[idx]]) + '\n')
    training_labels.append(folder_dir + idx_to_name[positive_cookies[idx]] + ' ' + str(idx_to_label[positive_cookies[idx]]) + '\n')

    saveCookieAsPNG(folder_dir + idx_to_name[negative_cookies[idx]], idx_to_img[negative_cookies[idx]])
    saveCookieAsPNG(folder_dir + idx_to_name[positive_cookies[idx]], idx_to_img[positive_cookies[idx]])

  with open('.' + output_path  + '/training_labels.csv','w') as fileCSV:

    fileCSV.writelines(training_labels)

def main():

  ## Set the random seed to aid reproducibility
  np.random.seed(random_seed)

  ## read geotiff satellite image
  [image_array_RGB, geo_transform] = loadGeotiff()

  ## read the shapefile with polygons
  sf = shapefile.Reader(shp_data_path)

  ## get coords for multiple polygons
  poly_bounds = getPolygonBounds(sf, geo_transform)

  ## segment image to extract train and test cookies
  [idx_to_img, idx_to_label, idx_to_name] = extractCookies(image_array_RGB, poly_bounds)

  ## get list of cookies in parking lots
  positive_cookies = [i for i, j in enumerate(idx_to_label) if j == 1]
  negative_cookies = [i for i, j in enumerate(idx_to_label) if j == 0]
 
  ## shuffle the negative cookies to randomize the subset used for training
  random.shuffle(negative_cookies)

  ## save cookies: save positive and negative cookies
  saveImages(negative_cookies, positive_cookies, idx_to_name, idx_to_label, idx_to_img)

if __name__=="__main__":
  main()
# def __init__ == "__main__":
#   main() 

