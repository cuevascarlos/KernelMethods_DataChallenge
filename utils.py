import random
import numpy as np
import pandas as pd
from scipy.ndimage import rotate
from skimage.feature import hog, daisy
from sklearn.cluster import MiniBatchKMeans
from skimage.feature import SIFT
from tqdm import tqdm


def read_data(data_path):
    #Read training data
    Xtr = np.array(pd.read_csv(data_path+'Xtr.csv',header=None,sep=',',usecols=range(3072))) #Drop the last column of Xtr because it is generated by the format of the data but it is unnecessary.
    Ytr = np.array(pd.read_csv(data_path+'Ytr.csv',sep=',',usecols=[1])).squeeze() 

    #Read test data
    Xte = np.array(pd.read_csv(data_path+'/Xte.csv',header=None,sep=',',usecols=range(3072))) ##Drop the last column of Xte because it is generated by the format of the data but it is unnecessary.
    return Xtr,Ytr,Xte

def gray_scale(X):
    #Scale images to gray
    X = (X - X.min())/(X.max() - X.min())
    X = np.reshape(X, (X.shape[0], 3, 32, 32))
    X_gray = np.mean(X, axis=1)
    return X_gray

def flip_augmentation(images, labels, aug_ratio = 0.2):
    """
    Method to augment the dataset size by flipping some images (randomly chosen) 
    in the dataset. We take a aug_ratio*100 percent of images for each label and 
    flip them.
    inputs:
        images: images in the dataset
        labels: labels of the images
        aug_ratio: ratio of images to flip
    output:
        augmented_images: images after augmentation
        augmented_labels: labels after augmentation
    """

    augmented_images = []
    augmented_labels = []

    for label in set(labels):
        idx_label = np.where(labels == label)[0]
        idx_to_augment = random.sample(list(idx_label), int(len(idx_label)*aug_ratio))

        for idx in idx_to_augment:
            image = images[idx]

            image = np.reshape(image, (3, 32,32))
            new_image = np.dstack((image[0], image[1], image[2]))

            new_image = np.fliplr(new_image)

            new_image = np.array([new_image[:,:,0], new_image[:,:,1], new_image[:,:,2]])
            new_image = new_image.flatten()
            augmented_images.append(new_image)
            augmented_labels.append(label)
    
    #To not append in the same order
    ids = np.random.permutation(len(augmented_labels))
    augmented_images = np.array(augmented_images)[ids]
    augmented_labels = np.array(augmented_labels)[ids]

    #To not have images and its augmented versions concatenate
    final_images = np.concatenate((images, augmented_images), axis = 0)
    final_labels = np.concatenate((labels, augmented_labels), axis=0)
    ids = np.random.permutation(len(final_labels))
    final_images = final_images[ids]
    final_labels = final_labels[ids]
    
    return final_images, final_labels


def rotate_dataset(images, labels, n_rotations = 1, ratio=0.2, rotate_angle=1):
    '''
    Method to augment the dataset size by rotating some images (randomly chosen)
    in the dataset. We take a ratio*100 percent of images for each label and
    rotate them.

    inputs:
        images: images in the dataset
        labels: labels of the images
        n_rotations: number of rotations per image randomly chosen
        ratio: ratio of images to rotate per label
        rotate_angle: angle to rotate

    output:
        final_images: images after augmentation
        final_labels: labels after augmentation
    '''

    augmented_images = []
    augmented_labels = []
    for i in range(n_rotations):
        for label in set(labels):
            #Get the index where label is
            idx_label = np.where(labels == label)[0]
            #Choose randomly 20% of the data with y=label 
            idx_to_augment = random.sample(list(idx_label), int(len(idx_label)*ratio))
            
            for id in idx_to_augment:
                image = images[id]
                image = np.reshape(image, (3, 32,32))
                x_aux = np.dstack((image[0], image[1], image[2]))

                angle = np.random.randint(-rotate_angle, rotate_angle)
                new_image = rotate(x_aux, angle, reshape=False, mode = 'nearest')

                new_image = np.array([new_image[:,:,0], new_image[:,:,1], new_image[:,:,2]])
                new_image = new_image.flatten()
                augmented_images.append(new_image)
                augmented_labels.append(label)

    #To not append in the same order
    ids = np.random.permutation(len(augmented_labels))
    augmented_images = np.array(augmented_images)[ids]
    augmented_labels = np.array(augmented_labels)[ids]

    #To not have images and its augmented versions concatenate
    final_images = np.concatenate((images, augmented_images), axis = 0)
    final_labels = np.concatenate((labels, augmented_labels), axis=0)
    ids = np.random.permutation(len(final_labels))
    final_images = final_images[ids]
    final_labels = final_labels[ids]


    return final_images, final_labels


class hog_feature_extractor:
    def __init__(self, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(3, 3)):
        self.orientations = orientations
        self.pixels_per_cell = pixels_per_cell
        self.cells_per_block = cells_per_block
    
    def extract_features(self, images, ravel=True):
        """
        Method to extract the hog features from the images
        inputs:
            images: images to extract the features
        output:
            features: hog features
        """
        features = []
        for image in tqdm(images):
            image = np.reshape(image, (3, 32, 32))
            hog_features = []
            for channel in range(3):
                hog_features.append(hog(image[channel], orientations=self.orientations, pixels_per_cell=self.pixels_per_cell, cells_per_block=self.cells_per_block))
            if ravel:
                hog_features = np.ravel(hog_features)
            else :
                hog_features = np.array(hog_features)
            features.append(hog_features)
        return np.array(features)

class sift_extractor():
    def __init__(self,n_clusters):
        self.n_clusters=n_clusters
        self.km=MiniBatchKMeans(n_clusters=self.n_clusters,batch_size=10, verbose=1)

    def extract_features(self,X):
        # sift = SIFT(upsampling=2, n_octaves=8, n_scales=3, sigma_min=1.2, sigma_in=0.5, c_dog=0.00013333333333333334, c_edge=10, n_bins=36, lambda_ori=1.5, c_max=0.8, lambda_descr=6, n_hist=4, n_ori=8)
        sift = SIFT(upsampling=2, n_octaves=8, n_scales=3, sigma_min=1.0, sigma_in=0.2, c_dog=0.00000000013333333333333334, c_edge=10, n_bins=36, lambda_ori=1.5, c_max=0.8, lambda_descr=6, n_hist=4, n_ori=8)

        sift_features=[]
        for img in tqdm(X):
            sift.detect_and_extract(img)
            des=sift.descriptors
            if des is not None:
                sift_features.append(des)

        return sift_features
    
    def fit(self,X):
        sift_features=self.extract_features(X)
        sift_features=np.vstack(sift_features)
        self.km.fit(sift_features)
    
    def predict(self,X):
        sift_features=self.extract_features(X)
        X_features = []

        for img in tqdm(sift_features):
            if len(img)==0:
                hist = np.zeros(self.n_clusters)
            else:
                img_clusters=self.km.predict(img)
                hist = np.bincount(img_clusters, minlength=self.n_clusters)
                hist = hist/np.linalg.norm(hist)
            
            X_features.append(hist)
        return np.array(X_features)


class daisy_feature_extractor:
    def __init__(self, step = 11, radius = 4, rings=2, histograms=6,orientations=8):
        self.step = step
        self.radius = radius
        self.rings = rings
        self.histograms = histograms
        self.orientations = orientations

    def fit(self, images, labels):
        pass
    
    def extract_features(self, images):
        """
        Method to extract the daisy features from the images
        inputs:
            images: images to extract the features
        output:
            features: hog features
        """
        features = []
        for image in tqdm(images):
            image = np.reshape(image, (3, 32, 32))
            daisy_features = []
            for channel in range(3):
                descs = daisy(image[channel], step=self.step, radius=self.radius, rings=self.rings, histograms=self.histograms,orientations=self.orientations)
                descs_num = descs.shape[0] * descs.shape[1]
                daisy_features.append(descs.reshape(descs_num,descs.shape[2]))
            daisy_features = np.ravel(daisy_features)
            features.append(daisy_features)
        return np.array(features)
    
    def fit_extract(self, images, labels):
        """
        Method to fit the hog extractor and extract the features
        inputs:
            images: images to extract the features
            labels: labels of the images
        output:
            features: hog features
        """
        self.fit(images, labels)
        return self.extract_features(images)