import os
import argparse
import datetime
import SimpleITK as sitk
import cv2
import matplotlib.pyplot as plt
import shutil

from utils.utils import fslBET
from utils.utils import fslFLIRT
from utils.utils import resample_image
from utils.utils import anatomical_views_extraction
from utils.utils import reduce_background
from utils.utils import Bcolors

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
	exceptions_path = os.path.join(ROOT, 'exceptions/')

	
	if not os.path.exists(mat_path):
		os.makedirs(mat_path)

	if not os.path.exists(output_path):
		os.makedirs(output_path)

	if not os.path.exists(antomical_views_path):
		os.makedirs(antomical_views_path)

	if not os.path.exists(exceptions_path):
		os.makedirs(exceptions_path)



if __name__ == '__main__':

	ROOT = os.path.abspath(__file__)
	FILENAME = os.path.basename(__file__)
	ROOT = ROOT.replace(FILENAME, '')

	output_path = os.path.join(ROOT, 'output_files')
	mat_path = os.path.join(ROOT, 'mat_files')
	antomical_views_path = os.path.join(ROOT, 'anatomical_views')
	input_path = os.path.join(ROOT, 'input_files')
	exceptions_path = os.path.join(ROOT, 'exceptions/')

	# ========== Make dirs at first execution ========== 
	make_input_folder()
	arguments = parse_args()


	# ========== Start ========== #
	make_dirs()
	start_time = datetime.datetime.now()
	num_nifti = len(os.listdir(input_path))
	print(Bcolors.OKCYAN + '\n\n[*] Starting process at {}'.format(start_time) + Bcolors.ENDC)

	for idx, file in enumerate(os.listdir(input_path)):

		# Get MRI ID
		filename = file.split('.')[0]
		image_input_path = os.path.join(input_path, file)

		try:
			print('\n[*] Processing file {} ({} of {})'.format(file, idx + 1, num_nifti))

			# Define output image and mat file path

			image_output_path = filename + '_final.nii.gz'
			image_output_path = os.path.join(output_path, image_output_path)

			mat_output_path = os.path.join(mat_path, filename + '_final.mat')

			# Resampling to isotropic voxel size
			sitk_image = sitk.ReadImage(image_input_path)
			resampled_image = resample_image(sitk_image, out_spacing=[arguments.voxel_size, 
																		arguments.voxel_size,
																		arguments.voxel_size])

			sitk.WriteImage(resampled_image, image_output_path)
			print(Bcolors.OKGREEN + '	[*] Resampling finished' + Bcolors.ENDC)

			# Starting brain volume extraction through BET Tool and Nipype interfaces
			fslBET(image_output_path, image_output_path, arguments.frac, arguments.BET_mode)

			# Check if the BET extraction was successful
			checkfiles = [file for file in os.listdir(output_path) if filename in file]

			if len(checkfiles) > 2:
				checkfiles = [os.path.join(output_path, file) for file in checkfiles]
				print(Bcolors.FAIL + '	[*] BET extraction failed' + Bcolors.ENDC)

				for file in checkfiles:
					os.remove(file)

				except_path = os.path.join(exceptions_path, filename + '.nii')
				shutil.move(image_input_path, except_path)

				continue

			print(Bcolors.OKGREEN + '	[*] BET extraction finished' + Bcolors.ENDC)

			# Starting linear registration through FLIRT Tool and Nipype interfaces
			fslFLIRT(image_output_path, image_output_path, arguments.dof, mat_output_path, arguments.atlas)
			print(Bcolors.OKGREEN + '	[*] FLIRT registration finished' + Bcolors.ENDC)

			# Extraction of anatomical views
			anatomical_views_extraction(image_output_path, arguments.image_size)
			print(Bcolors.OKGREEN + '	[*] Views extracion finished' + Bcolors.ENDC)

			# Remove mask file
			maskfiles = [os.path.join(output_path, file) for file in os.listdir(output_path) if '_mask' in file]
			for maskfile in maskfiles:
				os.remove(maskfile)

		except Exception as err:

			except_path = os.path.join(exceptions_path, filename + '.nii')
			shutil.move(image_input_path, except_path)

			print(Bcolors.FAIL + '[#] ERROR AT FILE {} ||| error : {}'.format(filename, err) + Bcolors.ENDC)

			trashfiles = [file for file in os.listdir(output_path) if file.startswith(filename)]
			trashfiles = [os.path.join(output_path, file) for file in trashfiles]

			for trashfile in trashfiles:
				os.remove(trashfile)

			pass

	exec_time = datetime.datetime.now() - start_time
	print(Bcolors.OKCYAN + '\n[#] Total Exec Time {}\n'.format(exec_time) + Bcolors.ENDC)
	print(Bcolors.OKCYAN + 'No of exceptions : {}\n\n'.format(len(os.listdir(exceptions_path))) + Bcolors.ENDC)






