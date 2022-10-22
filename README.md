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

## 3. Usage
