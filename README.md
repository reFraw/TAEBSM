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

1) Voxel size (-v) |
2) Fractional intensity treshold (-f) |
3) BET mode (-m) |
4) Degree of freedom (-d) |
5) Atlas (-a) |
6) Image size (-i) |
