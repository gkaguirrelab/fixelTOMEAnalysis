# fixelTOMEAnalysis
Analysis code and Flywheel gear files for TOME fixel-based diffusion analysis 

# Software Requirements
- Python3 (Python2 should also work but not tested)
- ANTs 
- AFNI (If the adaptive convex method will be used)
- Mrtrix
- trekker https://dmritrekker.github.io/manual/trekker.html

# Analysis Steps
1- Creating a FOD image from HCP-diff results.  
    - For adaptiveConvexOptimization Tran&Shi(2015), fodMakerWrapper.m could be 
    run directly with the DTI images and bval/bvec files
    - For the mrtrix method, first run calculateAverageResponseFunction.py to
    calculate 3-tissue average response functions and then run create_fod_image.py to
    make FOD images. This method was used for the TOME data.
    
2-  