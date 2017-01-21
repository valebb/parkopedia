import gdal, ogr, osr
import sys
import numpy as np
from matplotlib import pyplot as pyp2
import random
import os
from utils import visualizers as vs
import png
import shutil

# Global variables
raster_data_path = "/Users/valentina/Documents/project/14SEP10130721-S2AS_R1C1-054168728010_01_P001.TIF"
parking_data_path = '/Users/valentina/Documents/project/parkopedia-git/parking_matrix.npy'
cookie_size = 256
cookie_overlap = cookie_size / 4 ## number of overlapping pixels for segmentations 
threshold_pixels = 100 ## minimum percentage of pixels required to be labeled as parking
output_folder = 'cookies'
random_seed = 12347 ## To aid reproducibility

def loadGeotiff():
  """
  It loads the geotiff image and converts it to a numpy RGB array. It also extracts the 
  geo-transformation to convert lat-lon to pixel coordinates 
  """
  ## Open and read geotiff
  raster_geotiff = gdal.Open(raster_data_path, gdal.GA_ReadOnly)

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

  return image_array_RGB

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

def assignLabelToCookie(parking_matrix, line_start, pixel_start):
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
  count_pixels = 0
  
  for line in range(line_start, line_start+cookie_size-1):
    for pixel in range(pixel_start, pixel_start+cookie_size-1):
        if not parking_matrix[line, pixel] == 0:
        
          count_pixels += 1
          
          if count_pixels == threshold_pixels:
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

def extractCookies(image_array_RGB, parking_matrix):
  """
  It extract all the cookies from the geotiff and put it into a list
  Arguments 
    ---------

    image_array_RGB : numpy array
        RGB image extracted from the geotiff

    poly_bounds : list
        It contains the boundaries of all the polygons

  """

  print "Extracting cookies"

  #offset to remove the first and last 200 rows and lines of the image that are black
  offset_image = 200

  idx_to_img = []
  idx_to_label = []
  idx_to_name = []

  for line_start_coord in range(offset_image, image_array_RGB.shape[0] - cookie_size, cookie_overlap):

    cookie = []
    cookie_label = []

    for pixel_start_coord in range(offset_image, image_array_RGB.shape[1] - cookie_size, cookie_overlap):

      idx_to_img.append(getCookie(image_array_RGB, line_start_coord, pixel_start_coord))
      cookie_label = assignLabelToCookie(parking_matrix, line_start_coord, pixel_start_coord)
      idx_to_label.append(cookie_label)
      idx_to_name.append('_'.join(['label', str(cookie_label), 'cookie', str(line_start_coord), str(pixel_start_coord), '.png']))

      if len(idx_to_name) % 1000 ==0:
        print len(idx_to_name)

  print "...done"

  return idx_to_img, idx_to_label, idx_to_name

def saveImages(negative_cookies, positive_cookies, idx_to_name, idx_to_label, idx_to_img):
  """
  Saves each cookie as an RGB image and a csv file with the list of image urls and labels
  Arguments 
    ---------

    negative_cookies : list of negative cookies

    positive_cookies : list of positive cookies

    idx_to_name : list indexed by cookie index and the value is the cookie name

    idx_to_label : list indexed by cookie index and the value is the cookie label

    idx_to_img : list indexed by cookie index and the value is the cookie image

  """
  output_path = output_folder + '_' + str(cookie_size)
  current_path = os.getcwd()

  if os.path.exists(output_path):
    shutil.rmtree(output_path, ignore_errors=True)

  os.mkdir(output_path)
  training_labels = []
  folder_dir = current_path + '/' + output_path + '/' 
  
  for idx in range(0, len(positive_cookies)):

    training_labels.append(folder_dir + idx_to_name[negative_cookies[idx]] + ' ' + str(idx_to_label[negative_cookies[idx]]) + '\n')
    training_labels.append(folder_dir + idx_to_name[positive_cookies[idx]] + ' ' + str(idx_to_label[positive_cookies[idx]]) + '\n')

    saveCookieAsPNG(folder_dir + idx_to_name[negative_cookies[idx]], idx_to_img[negative_cookies[idx]])
    saveCookieAsPNG(folder_dir + idx_to_name[positive_cookies[idx]], idx_to_img[positive_cookies[idx]])

  with open('./' + output_path  + '/training_labels.csv','w') as fileCSV:

    fileCSV.writelines(training_labels)

def main():

  ## Set the random seed to aid reproducibility
  np.random.seed(random_seed)

  ## read geotiff satellite image
  image_array_RGB = loadGeotiff()

  ## read the numpy array with polygons
  parking_matrix = np.load(parking_data_path)

  ## segment image to extract train and test cookies
  [idx_to_img, idx_to_label, idx_to_name] = extractCookies(image_array_RGB, parking_matrix)

  ## get list of cookies in parking lots
  positive_cookies = [i for i, j in enumerate(idx_to_label) if j == 1]
  negative_cookies = [i for i, j in enumerate(idx_to_label) if j == 0]
 
  ## shuffle the negative cookies to randomize the subset used for training
  random.shuffle(negative_cookies)

  ## save cookies: save positive and negative cookies
  saveImages(negative_cookies, positive_cookies, idx_to_name, idx_to_label, idx_to_img)

if __name__=="__main__":
  main()

