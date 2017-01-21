# parkopedia project
Repository storing the python files for a project on recognizing parking lots from satellite images

# Requirements
- Chainer: Deep learning framework
- GDAL: Library for raster and vector geospatial data
- pyshp: Library to read and write support for the Esri Shapefile format
- Numpy: Math library

# Documentation 
See [doc/report.docx](https://github.com/valebb/parkopedia/blob/master/doc/report.docx)

# How to run it
- Step 1: Run preprocess_images.py to create a binary matrix specifying if each pixel of the image is in a polygon (label=1) or not
- Step 2: Run segment_images.py to extract the cookies for the training and validation set
- Step 3: Run compute_mean.py to compute the mean of the images of the training set
- Step 4: Run train_imagenet.py to train the neural network on the training and validation set
