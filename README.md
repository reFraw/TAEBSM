# TAEBSM - Tool for Automated Extraction of Brain Slices from MRI scans

The TAEBSM tool allows the extraction of a triplet slice from an MRI in NIFTI format.  
The extracted slices, one per anatomical plane, are centred in the central point of the brain mass.

## 1. Description
The script operates using the BET (Brain Extraction Tool) and FLIRT (FMRIB's Linear Image Registration Tool) modules offered by the FSL tool. In detail, the workflow followed by the script consists of the following operations:

1) Isotropic resampling of the NIFTI images.
2) Extraction of the brain mass via BET.
3) Linear registration of the images via FLIRT.
4) Extraction of the anatomical views and reduction of the background portion.

Registration is carried out on the standard MNI152 space.  

## 2. Dependencies
FSL installation is required to use the tool. To use the tool on Windows operating systems, use WSL (Windows Subsystem for Linux).  
Additional dependencies required for operation are contained in the 'requirements.txt' file.

## 3. Usage
The first execution of the programme, which can be called up via the help, allows the creation of the input directory, into which the NIFTI images to be processed are to be inserted.  
Once the files to be processed have been inserted, the script can be called again by specifying the following parameters:

1) Voxel size (-v) | Voxel size for image resampling. The default value is 2 mm.
2) Fractional intensity treshold (-f) | Threshold for brain mass extraction, must be between 0 and 1. Higher values may lead to loss of brain mass during extraction. The default value is 0.5.
3) BET mode (-m) | Mode of brain mass extraction by FSL. There are two options, B (Reduce Bias and Neck) and R (Robust Brain Centre Extimation). The default value is R.
4) Degree of freedom (-d) | Degrees of freedom for linear recording via FLIRT. You can choose between 6 (rigid body), 9 (standard) and 12 (affine).
5) Atlas (-a) | Reference atlas for linear registration via FLIRT. You can choose between MNI152 with 1 mm isotropic resolution or 2 mm isotropic resolution.
6) Image size (-i) |Size of images extracted from the MRI in SIZExSIZE format. The default value is 224 px.
