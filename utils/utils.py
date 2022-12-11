import os
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'

import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np
import cv2
import imutils

from nipype.interfaces import fsl

class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def resample_image(itk_image, out_spacing=[2.0, 2.0, 2.0]):

	# Resample images to 2mm Isotropic Voxels
    original_spacing = itk_image.GetSpacing()
    original_size = itk_image.GetSize()

    out_size = [
        int(np.round(original_size[0] * (original_spacing[0] / out_spacing[0]))),
        int(np.round(original_size[1] * (original_spacing[1] / out_spacing[1]))),
        int(np.round(original_size[2] * (original_spacing[2] / out_spacing[2])))]

    resample = sitk.ResampleImageFilter()
    resample.SetOutputSpacing(out_spacing)
    resample.SetSize(out_size)
    resample.SetOutputDirection(itk_image.GetDirection())
    resample.SetOutputOrigin(itk_image.GetOrigin())
    resample.SetTransform(sitk.Transform())
    resample.SetDefaultPixelValue(itk_image.GetPixelIDValue())

    resample.SetInterpolator(sitk.sitkBSpline)

    return resample.Execute(itk_image)


def fslBET(inp_file, out_file, frac, mode):

	# Define BET Pipeline
	bet = fsl.BET()

	bet.inputs.in_file = inp_file
	bet.inputs.out_file = out_file
	bet.inputs.frac = frac

	if mode == 'B':
		bet.inputs.reduce_bias = True
	elif mode == 'R':
		bet.inputs.robust = True

	result = bet.run()

	return result


def fslFLIRT(inp_file, out_file, dof, mat_file, atlas):

	# Define FLIRT Pipeline
	flirt = fsl.FLIRT()

	flirt.inputs.in_file = inp_file
	flirt.inputs.out_file = out_file
	if atlas == 'MNI152_2mm':
		flirt.inputs.reference = 'utils/atlas/MNI152_2mm_brain.nii.gz'
	elif atlas == 'MNI152_1mm':
		flirt.inputs.reference = 'utils/atlas/MNI152_1mm_brain.nii.gz'
	flirt.inputs.dof = dof
	flirt.inputs.out_matrix_file = mat_file

	result = flirt.run()

	return result


def anatomical_views_extraction(file_path, image_size):

	fileID = file_path.split('/')[-1]
	fileID = fileID.split('.')[0]
	fileID = fileID.replace('_final', '')

	sitkImage = sitk.ReadImage(file_path)
	Image = sitk.GetArrayFromImage(sitkImage)

	index = np.asarray(Image.shape) // 2

	axial_view = Image[index[0], :, :]
	axial_view = cv2.resize(axial_view, (image_size, image_size))

	coronal_view = Image[:, index[1], :]
	coronal_view = cv2.flip(coronal_view, 0)
	coronal_view = cv2.resize(coronal_view, (image_size, image_size))

	sagittal_view = Image[:, :, index[2]]
	sagittal_view = cv2.flip(sagittal_view, 0)
	sagittal_view = cv2.resize(sagittal_view, (image_size, image_size))

	save_path = os.path.join('anatomical_views', fileID)

	if not os.path.exists(save_path):
		os.makedirs(save_path)

	axial_save_path = os.path.join(save_path, fileID + '_axial.png')
	coronal_save_path = os.path.join(save_path, fileID + '_coronal.png')
	sagittal_save_path = os.path.join(save_path, fileID + '_sagittal.png')

	plt.imsave(axial_save_path, axial_view, cmap='gray')
	plt.imsave(coronal_save_path, coronal_view, cmap='gray')
	plt.imsave(sagittal_save_path, sagittal_view, cmap='gray')


def reduce_background(image_path):
    
    img = cv2.imread(image_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    
    thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.erode(thresh, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=2)
    
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv2.contourArea)
    
    extLeft = tuple(c[c[:, :, 0].argmin()][0])
    extRight = tuple(c[c[:, :, 0].argmax()][0])
    extTop = tuple(c[c[:, :, 1].argmin()][0])
    extBot = tuple(c[c[:, :, 1].argmax()][0])
    
    img_cnt = cv2.drawContours(img.copy(), [c], -1, (0, 255, 255), 4)
    
    img_pnt = cv2.circle(img_cnt.copy(), extLeft, 8, (0, 0, 255), -1)
    img_pnt = cv2.circle(img_pnt, extRight, 8, (0, 255, 0), -1)
    img_pnt = cv2.circle(img_pnt, extTop, 8, (255, 0, 0), -1)
    img_pnt = cv2.circle(img_pnt, extBot, 8, (255, 255, 0), -1)
    
    ADD_PIXELS = 3
    new_img = img[extTop[1]-ADD_PIXELS:extBot[1]+ADD_PIXELS, extLeft[0]-ADD_PIXELS:extRight[0]+ADD_PIXELS].copy()
    
    return new_img