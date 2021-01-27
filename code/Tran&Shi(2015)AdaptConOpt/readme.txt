FOD image calculation

If you use these script, please cite the paper:
Tran, G., & Shi, Y. (2015). Fiber orientation and compartment parameter estimation from multi-shell diffusion imaging. IEEE Transactions on Medical Imaging, 34(11), 2320–2332.

step 1.
convert the dMRI data to RAS space
FlipNII2RAS input_dti  output_dti  input_bvec output_gradientTable

step 2.
split dMRI data to speedup the calculation
SplitDTIData input_dti input_gradientTable input_mask input_mask input_NumSplit Output_Dir input_Subj_name

step 3.
calculate FOD
FOD_AdaptiveConvexOpt_WholeVolume_KernelOptimization input_gradientTable 500 3500 input_dti 0 input_mask 12 120 30 0.12 0.06 3 4 1 0 output_FOD output_tissuemap


fslmerge -z output_FOD FOD_*.nii"

step 4.
tract to mask
TrackVis2MRTrixTracks input_fod reference_img output_tck
mrtrix/tracks2prob tck_in reference_img nifti_out
