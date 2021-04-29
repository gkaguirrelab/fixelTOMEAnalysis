# fixelTOMEAnalysis
Analysis code and Flywheel gear files for TOME fixel-based diffusion analysis 

# Software Requirements for the wrapper code
- Python3 (Python2 should also work but not tested)
- ANTs 
- AFNI (If the adaptive convex method will be used)
- Mrtrix
- trekker https://dmritrekker.github.io/manual/trekker.html
- FSL

# Fixel Analysis Steps
All analysis functions are wrappers around one or multiple software mentioned
above. All of the steps mentioned next were run with Flywheel gears. The scripts
to submit these gears for all subjects can be found in submitGears folder of 
this repo.

1- Creating a FOD image from HCP-diff results.  
- For adaptiveConvexOptimization Tran&Shi(2015), fodMakerWrapper.m could be run 
    directly with the DTI images and bval/bvec files.
- For the mrtrix method, first run calculateAverageResponseFunction.py to
    calculate 3-tissue average response functions and then run create_fod_image.py to
    make FOD images. This method was used for the TOME data. We used multi-shell
    option since our data had multiple b-values with 8 lmax.
    
2- We run create_fod_population_template.py to calculate an unbiased FOD 
template image.

3- An anatomical template was created with ANTs from all subject MPRAGE images 
with the following call
    "antsMultivariateTemplateConstruction2.sh -d 3 -c 2 -A 1 -a 1 -b 0 -e 1 -g 0.2 -i 4 -j 6 -k 1 -w 1 -q 500x500x100x50 -f 6x4x2x1 -s 3x2x1x0 -n 1 -o /flywheel/v0/output/TOME -r 1 -l 1 -m CC -t SyN -y 1"
    
4- recon-all was run on the template.

5- The thalamic regions of the template was segmented following the Freesurfer
instructions: https://freesurfer.net/fswiki/ThalamicNuclei

6- LGNs were extracted from the ThalamicSegmentation results with the Freesurfer 
mri_extract_label function using the segmentations codes 8109 and 8209 
(left and right LGN respectively). The optic chiasm was extracted with the code
85

7- Extracted segmentations were linearly (12DOF) registered to the FOD template. 

8- A wrapper around trekker (roi_tractography.py) was used to calculate the 
optic tract using the LGN and optic chiasm segmentations from the previous step.

9- fixelAnalysis.py was used to calculate whole brain fixel metrics.

10- With the extract_fixel_values.py function the whole brain fixel maps were 
cropped using the tracts from step 8. The function also produces optic tract 
fixel stats.

# DTI Analysis Steps

1- FSL's dtifit was used to fit tensors to the preprocessed DTI images.

2- extract_dti_values.py was used to construct whole brain DTI metric values 
as well as the ones cropped with the tracks calculated at the fixel analysis 
step 8.
 