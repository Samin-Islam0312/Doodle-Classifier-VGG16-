# -*- coding: utf-8 -*-
"""Final Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oc0cdaSrqqj7TFgohSTdMBNsgqgcOGMT
"""

from google.colab import drive
drive.mount('/content/drive/')

# Commented out IPython magic to ensure Python compatibility.
import keras
from keras.applications.vgg16 import VGG16
from keras.models import Model
from keras.layers import *
from keras.layers.pooling import GlobalAveragePooling2D
from keras.layers.recurrent import LSTM
from keras.layers.wrappers import TimeDistributed
from tensorflow.keras.optimizers import Adam
import os
import re
from glob import glob
from tqdm import tqdm
import numpy as np
import pandas as pd
import ast
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
# %matplotlib inline

num_classes=15
fileNumber=150
channels=3
width=224
height=224
vgg16_base = VGG16(input_shape=(width,height,channels),weights="imagenet",include_top=False)
vgg16_base.trainable = False

"""Converting the stroke positions to numpy arrays of pixels, 
arrays are also normalized. 
Resized the 2D strokes arrays into 3D array similar to RGB for feed into VGG16. """

def draw_it(strokes):
    image = Image.new("P", (256,256), color=255)
    image_draw = ImageDraw.Draw(image)
    for stroke in ast.literal_eval(strokes):
        for i in range(len(stroke[0])-1):
            image_draw.line([stroke[0][i], 
                             stroke[1][i],
                             stroke[0][i+1], 
                             stroke[1][i+1]],
                            fill=0, width=5)
    image = image.resize((height, width))
    image = np.array(image)/255.0
    image = np.stack((image,)*3, axis=-1)
    return image

"""Input"""

fileLink='/content/drive/MyDrive/quickdraw_data/'
fileList = os.listdir(fileLink)
X=[] #INPUT
Y=[] #prediction

"""Extracting the labels from the csv files."""

count=0
for i in fileList:
    count+=1
    if count%10==0:
        print(count)
    tempDF = pd.read_csv(fileLink+i)
    for x in range(fileNumber):
        if tempDF['recognized'][x]: 
            X.append(draw_it(tempDF['drawing'][x]))
            Y.append(i.split('.')[0])
        x-=1
    if count == num_classes:
        break

#show the dataset
tempDF.head(5)

import random
Z = list(zip(X, Y))

random.shuffle(Z)

X, Y = zip(*Z)
del Z

from sklearn.preprocessing import OneHotEncoder, LabelEncoder
le = LabelEncoder()
le.fit(np.unique(Y))
encoded_labels=le.transform(Y)
encoded_labels = np.reshape(encoded_labels,(-1,1))

encoder = OneHotEncoder()
encoder.fit(encoded_labels)
encoded_labels=encoder.transform(encoded_labels)
encoded_labels=encoded_labels.toarray()
Y=np.array(encoded_labels)
X=np.array(X)

#size of each X
X[2].shape

#show a doodle
plt.imshow(X[8])

#see the label of the doodle previously shown
le.inverse_transform([np.argmax(Y[8])])

from sklearn.model_selection import train_test_split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y,shuffle=True, random_state=32, test_size=0.15)
del X
del Y

flatten_layer = Flatten()
dense_layer_1 = Dense(1024, activation='relu')
dropout_layer1 = Dropout(0.2)
dense_layer_2 = Dense(512, activation='relu')
dropout_layer2 = Dropout(0.2)
dense_layer_3 = Dense(256, activation='relu')
dropout_layer3 = Dropout(0.2)
prediction_layer = Dense(num_classes, activation='softmax')
model = keras.models.Sequential([
    vgg16_base,
    flatten_layer,
    dense_layer_1,
    dropout_layer1,
    dense_layer_2,
    dropout_layer2,
    dense_layer_3,
    dropout_layer3,
    prediction_layer
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['categorical_accuracy'],
)

model.summary()

batchsize=10
history = model.fit(X_train, Y_train, epochs=15, validation_data=(X_test, Y_test),batch_size=batchsize,
                   callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10), #stop training if accuracy doesn't improve in next 10 epoch
        tf.keras.callbacks.ModelCheckpoint('model_best.hdf5', monitor='val_loss', verbose=1, save_best_only=True, save_weights_only=False, mode='auto', save_frequency=1)
    ])

def plot_graphs(history, string):
  plt.plot(history.history[string])
  plt.plot(history.history['val_'+string])
  plt.xlabel("Epochs")
  plt.ylabel(string)
  plt.legend([string, 'val_'+string])
  plt.show()
  
plot_graphs(history, "categorical_accuracy")
plot_graphs(history, "loss")