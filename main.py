import os
import argparse
import datetime
import SimpleITK as sitk
import cv2
import matplotlib.pyplot as plt

from utils.utils import fslBET
from utils.utils import fslFLIRT
from utils.utils import resample_image
from utils.utils import anatomical_views_extraction
from utils.utils import reduce_background

from tqdm.contrib import tzip
from tqdm import tqdm

def parse_args():

	parser = argparse.ArgumentParser(prog='TAEBSM', description='Tool for Automated Extraction of Brain Slices from MRI scans')

	group = parser.add_argument_group('Arguments')

	group.add_argument('--voxel_size', '-v', required=False, type=float, default=2.0,
							help='Isotropic voxels size for image resampling')

	group.add_argument('--frac', '-f', required=False, type=float, default=0.5,
							help='Fractional intensity treshold, must be a number between 0 and 1. Smaller value allow the preservation of more brain mass')

	group.add_argument('--BET_mode', '-m', required=False, type=str, choices=['B', 'R'], default='R',
							help='BET Extraction mode. | B (Reduce Bias and Neck) | R (Robust Brain Center Estimation)')

	group.add_argument('--dof', '-d', required=False, type=int, choices=[ 6, 9, 12], default=12,
							help='Degree of Freedom for linear registration. | 6 (Rigid Body) | 9 (Traditional) | 12 (Affine)')

	group.add_argument('--atlas', '-a', required=False, type=str, choices=['MNI152_1mm', 'MNI152_2mm'], default='MNI152_2mm',
							help='Atlas for linear registration via FLIRT')

	group.add_argument('--image_size', '-i', required=False, type=int, default=224,
							help='Image size in format SIZExSIZE for anatomical views extraction.')

	arguments = parser.parse_args()

	return arguments

def get_input_file(path='input_files/'):

	inp_files = [os.path.join(path, file) for file in os.listdir(path)]

	return inp_files


def get_output_file(input_files):

	filename = [file.split('/')[-1] for file in input_files]
	filename = [file.split('.')[0] + '_final.nii.gz' for file in filename]
	out_file = [os.path.join('output_files', file) for file in filename]

	return out_file


def get_mat_file(input_files):

	filename = [file.split('/')[-1] for file in input_files]
	filename = [file.split('.')[0] for file in filename]
	filename = [file + '_final.mat' for file in filename]
	mat_file = [os.path.join('mat_files', file) for file in filename]

	return mat_file


def get_resampled_file(input_files):

	filename = [file.split('/')[-1] for file in input_files]
	filename = [file.split('.')[0] + '_resampled.nii.gz' for file in filename]
	resampled_file = [os.path.join('resampled_files', file) for file in filename]

	return resampled_file

def make_input_folder():

	ROOT = os.path.abspath(__file__)
	FILENAME = os.path.basename(__file__)
	ROOT = ROOT.replace(FILENAME, '')

	input_path = os.path.join(ROOT, 'input_files')

	if not os.path.exists(input_path):
		os.makedirs(input_path)

def make_dirs():

	ROOT = os.path.abspath(__file__)
	FILENAME = os.path.basename(__file__)
	ROOT = ROOT.replace(FILENAME, '')

	output_path = os.path.join(ROOT, 'output_files')
	mat_path = os.path.join(ROOT, 'mat_files')
	resampled_path = os.path.join(ROOT, 'resampled_files')
	antomical_views_path = os.path.join(ROOT, 'anatomical_views')
	
	if not os.path.exists(mat_path):
		os.makedirs(mat_path)

	if not os.path.exists(resampled_path):
		os.makedirs(resampled_path)

	if not os.path.exists(output_path):
		os.makedirs(output_path)

	if not os.path.exists(antomical_views_path):
		os.makedirs(antomical_views_path)

if __name__ == '__main__':

	# ========== Make dirs at first execution ========== 
	make_input_folder()
	arguments = parse_args()


	# ========== Start ========== #
	make_dirs()
	start_time = datetime.datetime.now()
	print('\n\n[*] Starting process at {}'.format(start_time))

	
	# ========== Get input and output file names ========== 
	input_files = get_input_file()
	output_files = get_output_file(input_files)
	mat_files = get_mat_file(input_files)
	resampled_files = get_resampled_file(input_files)


	# ========== Resampling Images ========== 
	print('\n[*] Starting Resampling Images...\n')
	for inp, res in tzip(input_files, resampled_files):
		inp_image = sitk.ReadImage(inp)

		res_image = resample_image(inp_image, out_spacing=[arguments.voxel_size,
															arguments.voxel_size,
															arguments.voxel_size])

		sitk.WriteImage(res_image, res)
	print('\n[#] Resampled finished.')


	# ========== BET Brain Extraction ========== 
	print('\n[*] Starting BET Extraction...\n')
	for inp, out in tzip(resampled_files, output_files):
		fslBET(inp, out, arguments.frac, arguments.BET_mode)
		os.remove(inp)
	os.rmdir('resampled_files/')
	mask_file = [file for file in os.listdir('output_files/') if '_mask' in file]
	mask_file = [os.path.join('output_files/', file) for file in mask_file]
	for file in mask_file:
		os.remove(file)
	print('\n[#] BET Extraction finished.')


	# ========== FLIRT Linear Registration ========== 
	print('\n[*] Starting FLIRT Registration...\n')
	for inp, mat in tzip(output_files, mat_files):
		fslFLIRT(inp, inp, arguments.dof, mat,arguments.atlas)
	print('\n[#] FLIRT Registration finished.')


	# ========== Extraction of Anatomical Views ==========
	print('\n[*] Starting Extraction of Anatomical Views...\n')

	for file in tqdm(output_files):
		anatomical_views_extraction(file)

	dirs_ID = [dirs for dirs in os.listdir('anatomical_views/')]
	for directory in dirs_ID:
		base_path = os.path.join('anatomical_views/', directory)
		for image in os.listdir(base_path):
			image_path = os.path.join(base_path, image)
			reduced_img = reduce_background(image_path)
			reduced_img = cv2.resize(reduced_img,
										dsize=(arguments.image_size, arguments.image_size),
										interpolation=cv2.INTER_CUBIC)
			plt.imsave(image_path, reduced_img)

	print('\n[#] Extraction of Anatomical Views finished.\n')

	exec_time = datetime.datetime.now() - start_time
	print('[#] Total Exec Time {}\n\n'.format(exec_time))
	
