import cv2
import numpy as np
import glob
import os

def make_vid():
    img_array = []
    path = os.path.join('C:\\', 'video_data', '2022-09-04_10-57-42')
    print(path + '\\*.jpeg')
    print(os.path.isdir(path))
    for filename in glob.glob(path + '\\*.jpeg'):
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)

    out = cv2.VideoWriter('project.avi', cv2.VideoWriter_fourcc(*'DIVX'), 15, size)

    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()

if __name__ == '__main__':
    make_vid()
