import cv2
import numpy
import typing
import Entomoscope.globals as globals
import os
import PIL.Image

import gc


class Stacking:
    """
    Focus stacking of multiple images with any number of frames. 
    Each image is composed of a sharp and an out-of-focus part.
    """
    __KERNEL_SIZE = globals.KERNEL_SIZE
    __BLUR_SIZE = globals.BLUR_SIZE
    __SIGMAX = globals.SIGMA_X
    __RANSAC_REPROJ_THRESHOLD_VALUE = globals.RANSAC_REPROJ_THRESHOLD_VALUE
    __HIGHEST_PIXEL_VALUE = globals.HIGHEST_PIXEL_VALUE
    __NUMBER_MATCHES = globals.NUMBER_MATCHES
    __OFFSET = globals.OFFSET
    
    def __init__(self) -> None:
        image_width = globals.IMAGE_WIDTH
        image_height = globals.IMAGE_HEIGHT
        self.__image_width = image_width
        self.__image_height = image_height

    
    def findHomography(self, 
                        image_1_kp: typing.List[numpy.ndarray], 
                        image_2_kp: typing.List[numpy.ndarray], 
                        matches: typing.List
        ) -> typing.List[numpy.ndarray]:
        """
        Find matches between different captures by identifying key features.

        :param image_1_kp:
            first image to find homography for
        :param image_2_kp:
            second image to find homography for
        :param matches:
            ...
        :return: list of numpy arrays
        """ 
        image_1_points = numpy.zeros((len(matches), 1, 2), dtype=numpy.float32)
        image_2_points = numpy.zeros((len(matches), 1, 2), dtype=numpy.float32)

        for i in range(len(matches)):
            image_1_points[i] = image_1_kp[matches[i].queryIdx].pt
            image_2_points[i] = image_2_kp[matches[i].trainIdx].pt

        homography, _ = cv2.findHomography(image_1_points, 
                                        image_2_points, 
                                        cv2.RANSAC, 
                                        ransacReprojThreshold=Stacking.__RANSAC_REPROJ_THRESHOLD_VALUE)
        return homography
    

    def align_images(self, 
                    image1, 
                    image2
        ):
        im1 = image1
        im2 = image2

        im1_gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        im2_gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

        sz = im1.shape
        warp_mode = cv2.MOTION_TRANSLATION
        warp_matrix = numpy.eye(2, 3, dtype=numpy.float32)

        number_of_iterations = 5000
        termination_eps = 1e-10
        criteria = (cv2.TERM_CRITERIA_EPS / cv2.TERM_CRITERIA_COUNT, number_of_iterations, termination_eps)
        criteria = list(criteria)
        criteria[0] = int(criteria[0])
        criteria = tuple(criteria)
        
        _, warp_matrix = cv2.findTransformECC(im1_gray, im2_gray, warp_matrix, warp_mode, criteria)
        im2_aligned = cv2.warpAffine(im2, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)

        return im2_aligned
    

    def focus_stack(self,
                    unimages: typing.List[numpy.ndarray]
        ) -> numpy.ndarray:
        """
        Find the sharpest area of each of the superimposed images 
        and generates an image from the different sharp areas.

        :param unimages: 
            list of images for the focus stacking
        :return: list of images
        """
        #self.__images = self.align_images(unimages, distance)

        laplacians_img = []
        for i in range(len(unimages)):
            image = cv2.cvtColor(unimages[i], cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(image, (Stacking.__BLUR_SIZE, Stacking.__BLUR_SIZE), Stacking.__SIGMAX)
            laplacian = cv2.Laplacian(blurred, cv2.CV_64F, ksize=Stacking.__KERNEL_SIZE)
            laplacians_img.append(laplacian)
        laplacians_img = numpy.asarray(laplacians_img)
        output = numpy.zeros(shape=unimages[0].shape, dtype=unimages[0].dtype)

        abs_laplacians_img = numpy.absolute(laplacians_img)
        maxima = abs_laplacians_img.max(axis=0)
        bool_mask = abs_laplacians_img == maxima
        mask = bool_mask.astype(numpy.uint8)

        for i in range(len(unimages)):
            output = cv2.bitwise_not(unimages[i], output, mask=mask[i])
        
        del laplacians_img
        del abs_laplacians_img
        del bool_mask
        del mask
        gc.collect()
        
        return Stacking.__HIGHEST_PIXEL_VALUE - output
  
    
    def del_edges(self, 
                image: numpy.ndarray, 
                orig_image: numpy.ndarray,
        ) -> numpy.ndarray:
        """
        Delete edges of the aligned image.

        :param images:
            final stacked image
        :return:
            image with deleted edges
        """
        image_width = self.__image_width
        image_height = self.__image_height
        offset = Stacking.__OFFSET
        image_threshold_width_left = image_width - offset
        image_threshold_heigth_left = image_height - offset

        image[:offset, :] = orig_image[:offset, :]
        image[image_threshold_heigth_left:, :] = orig_image[image_threshold_heigth_left:, :]
        image[:, :offset] = orig_image[:, :offset]
        image[:, image_threshold_width_left:] = orig_image[:, image_threshold_width_left:]

        return image

    
    def find_sharpness(self, 
                    image_list: typing.List[numpy.ndarray]
        ) -> numpy.ndarray:
        """
        Find the sharpest image of all stacked imaged.

        :param image_list:
            image_list as numpy arrays
        :return:
            stacked image as a numpy array
        """
        sharpness_list = []
        for image in image_list:
            image = PIL.Image.fromarray(image).convert('L')
            image = numpy.asarray(image, dtype=numpy.int32)
            gx, gy = numpy.gradient(image)
            gnorm = numpy.sqrt(gx**2 + gy**2)
            sharpness = numpy.average(gnorm)
            sharpness_list.append(sharpness)
        most_sharp = max(sharpness_list)
        index_most_sharp = sharpness_list.index(most_sharp)

        return image_list[index_most_sharp] 
    

    def do_stacking(self, 
                    image_list: numpy.ndarray, 
        ) -> numpy.ndarray:
        """
        Runs the stacking process for the image list.

        :param image_list:
            image list as numpy arrays
        :return:
            stacked image as a numpy array
        """
        '''
        image_list_sharpness = []        
        i = 1
        for distance in configuration.DISTANCE_VALUES:
            z_stacking_image = self.focus_stack(distance, image_list)
            stacked_image = self.del_edges(z_stacking_image)
            image_list_sharpness.append(stacked_image)
            stacked_image = PIL.Image.fromarray(stacked_image)
            stacked_image.save(f'/home/pi/Desktop/{i}.png')
            i += 1
        stacked_image = self.find_sharpness(image_list_sharpness)
        image = PIL.Image.fromarray(stacked_image)
        
        return image
        '''
        aligned_image_list = []
        image1 = image_list[0]
        image2 = image_list[1]

        aligned_image = self.align_images(image1, image2)
        aligned_image_list.append(aligned_image)

        for image in image_list[2:]:
            aligned_image = self.align_images(aligned_image_list[-1], image)
            aligned_image_list.append(aligned_image)

        stacked_image = self.focus_stack(aligned_image_list)
        del aligned_image_list
        gc.collect()

        #stacked_image = self.del_edges(z_stacked_image)
        #stacked_image.save('/home/pi/Desktop/image_test.png')
        #image_orig = numpy.array(image_list[0])
        #stacked_image = self.del_edges(stacked_image, image_orig)
        #stacked_image = PIL.Image.fromarray(stacked_image)

        return stacked_image
        
