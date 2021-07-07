import os

def construct_optic_radiations(hcp_struct_archive, freesurfer_archive, bayesprf_inferred_volume_archive, segment_thalamic_segmentations_archive, 
                               subjectFOD, FODtemplate, calculateFixelsIntermediate, workdir, outputdir, minFODamp='0.2', track_density_thresh='1', freesurfer_path='', 
                               ants_path='', fsl_path='', mrtrix_path='', trekker_path=''):
    
    # Create workdir and outputdir if it doesn't exist 
    if not os.path.exists(workdir):
        os.system('mkdir %s' % workdir)
    if not os.path.exists(outputdir):
        os.system('mkdir %s' % outputdir)
        
    # Get the subject id from hcp-struct zip archive
    subject_id = os.path.split(hcp_struct_archive)[1][:-14]
    
    # Create a nested workdir with the subject id 
    subject_workdir = os.path.join(workdir, subject_id)
    os.system('mkdir %s' % subject_workdir)
    
    # Extract the higres skull stripped T1 from the struct archive and convert it to nifti
    higres_mgz_extracted = os.path.join(subject_workdir, 'brain.hires.mgz')
    higres_nifti = os.path.join(subject_workdir, 'brain.hires.nii.gz')
    os.system('unzip -q -j %s %s/T1w/%s/mri/brain.hires.mgz -d %s' % (hcp_struct_archive, subject_id, subject_id, subject_workdir))
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'), higres_mgz_extracted, higres_nifti))
    
    # Extract the bayesprf varea and convert to nifti
    os.system('unzip -q %s -d %s' % (bayesprf_inferred_volume_archive, subject_workdir))
    varea_mgz = os.path.join(subject_workdir, 'inferred_varea.mgz')
    V1 = os.path.join(subject_workdir, 'V1.nii.gz')
    os.system('%s %s 1 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), varea_mgz, V1))
    
    # Extract LGN from thalamic nuclei and convert to nifti
    os.system('unzip -q %s -d %s' % (segment_thalamic_segmentations_archive, subject_workdir))
    thalamic_segmentations = os.path.join(subject_workdir, 'ThalamicNuclei.v12.T1.FSvoxelSpace.mgz')
    left_lgn = os.path.join(subject_workdir, 'left_lgn.nii.gz')
    right_lgn = os.path.join(subject_workdir, 'right_lgn.nii.gz')
    os.system('%s %s 8109 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), thalamic_segmentations, left_lgn))
    os.system('%s %s 8209 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), thalamic_segmentations, right_lgn))
    
    # Get the first volume of FOD image for registration
    single_frame_FOD = os.path.join(subject_workdir, 'single_frame_FOD.nii.gz')   
    single_frame_FOD_template = os.path.join(subject_workdir, 'single_frame_FOD_template.nii.gz')   
    os.system('%s %s %s 0 1' % (os.path.join(fsl_path, 'fslroi'), subjectFOD, single_frame_FOD))
    os.system('%s %s %s 0 1' % (os.path.join(fsl_path, 'fslroi'), FODtemplate, single_frame_FOD_template))
    
    # Do an affine registration between highres image and FOD template 
    output_name = os.path.join(subject_workdir, 'highres2fod')
    output_warped = os.path.join(subject_workdir, 'outputWarped.nii.gz')
    generic_affine = os.path.join(subject_workdir, 'highres2fod0GenericAffine.mat')
    output_inverse_warped = os.path.join(subject_workdir, 'outputInverseWarped.nii.gz')
    ants_run = '%s --verbose 1 --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 --winsorize-image-intensities [ 0.005,0.995 ] \
--initial-moving-transform [ %s,%s,1 ] --transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox \
--transform Affine[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox' % (os.path.join(ants_path, 'antsRegistration'), 
                                                           output_name,output_warped, output_inverse_warped,
                                                           single_frame_FOD, higres_nifti, single_frame_FOD, higres_nifti,
                                                           single_frame_FOD, higres_nifti)
    os.system(ants_run)
    
    # Move V1 to subject FOD space
    warped_v1 = os.path.join(subject_workdir, 'warped_V1.nii.gz')
    os.system('%s -d 3 -i %s -r %s -n NearestNeighbor -t %s -o %s' % (os.path.join(ants_path, 'antsApplyTransforms'), V1, single_frame_FOD, generic_affine, warped_v1))
    
    # LGN was constructed with a different version of recon-all. So we do a rigid registration between the standalone freesurfer 
    # brain.mgz file and HCP-struct freesurfer higres run and then apply the warp we calculated above to move the segmentations to 
    # the FOD coordinate space.
    freesurfer_orig_mgz_extracted = os.path.join(subject_workdir, 'brain.mgz')
    freesurfer_orig_nifti = os.path.join(subject_workdir, 'brain.nii.gz')
    os.system('unzip -q -j %s %s/mri/brain.mgz -d %s' % (freesurfer_archive, subject_id, subject_workdir))
   
    
    freesurfer_output_name = os.path.join(subject_workdir, 'brain2hires')
    freesurfer_output_warped = os.path.join(subject_workdir, 'brain2hiresOutputWarped.nii.gz')
    freesurfer_generic_affine = os.path.join(subject_workdir, 'brain2hires0GenericAffine.mat')
    freesurfer_output_inverse_warped = os.path.join(subject_workdir, 'brain2hiresoutputInverseWarped.nii.gz')   
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'), freesurfer_orig_mgz_extracted, freesurfer_orig_nifti))
    ants_run = '%s --verbose 1 --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 --winsorize-image-intensities [ 0.005,0.995 ] \
--initial-moving-transform [ %s,%s,1 ] --transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox ' % (os.path.join(ants_path, 'antsRegistration'), 
                                                                                                       freesurfer_output_name, freesurfer_output_warped, 
                                                                                                       freesurfer_output_inverse_warped,
                                                                                                       higres_nifti, freesurfer_orig_nifti, 
                                                                                                       higres_nifti, freesurfer_orig_nifti)
    os.system(ants_run)
    
    # Apply warps
    warped_lgn_left = os.path.join(subject_workdir, 'warped_left_lgn.nii.gz')
    warped_lgn_right = os.path.join(subject_workdir, 'warped_right_lgn.nii.gz') 
    os.system('%s -d 3 -i %s -r %s -n NearestNeighbor -t %s -t %s -o %s' % (os.path.join(ants_path, 'antsApplyTransforms'), left_lgn, single_frame_FOD, generic_affine, freesurfer_generic_affine, warped_lgn_left))
    os.system('%s -d 3 -i %s -r %s -n NearestNeighbor -t %s -t %s -o %s' % (os.path.join(ants_path, 'antsApplyTransforms'), right_lgn, single_frame_FOD, generic_affine, freesurfer_generic_affine, warped_lgn_right))
    
    # Do tractography
    left_track = os.path.join(subject_workdir, 'left_optic_radiation.vtk')
    right_track = os.path.join(subject_workdir, 'right_optic_radiation.vtk')
    os.system('%s -fod %s -seed_image %s -seed_count 12000 -pathway=require_entry %s -pathway=stop_at_exit %s -minFODamp %s -output %s -maxLength 100 -atMaxLength discard -directionality one_sided > %s/trekker_left.log' % (os.path.join(trekker_path, 'trekker'),
                                                                                                                                                                                                                               subjectFOD, warped_lgn_left,
                                                                                                                                                                                                                               warped_v1, warped_v1, minFODamp, 
                                                                                                                                                                                                                               left_track, outputdir))
    os.system('%s -fod %s -seed_image %s -seed_count 12000 -pathway=require_entry %s -pathway=stop_at_exit %s -minFODamp %s -output %s -maxLength 100 -atMaxLength discard -directionality one_sided > %s/trekker_right.log' % (os.path.join(trekker_path, 'trekker'),
                                                                                                                                                                                                                                subjectFOD, warped_lgn_right,
                                                                                                                                                                                                                                warped_v1, warped_v1, minFODamp, 
                                                                                                                                                                                                                                right_track, outputdir))
    # Convert tracks to tck 
    tck_left = os.path.join(outputdir, 'native_left_optic_radiation.tck')
    tck_right = os.path.join(outputdir, 'native_right_optic_radiation.tck')
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, tck_left))
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, tck_right))    
    
    # Make volumetric density masks
    tck_left_density = os.path.join(outputdir, 'native_left_optic_radiation_density.nii.gz')
    tck_right_density = os.path.join(outputdir, 'native_right_optic_radiation_density.nii.gz')
    os.system('%s %s -template %s %s' % (os.path.join(mrtrix_path, 'tckmap'), tck_left, single_frame_FOD, tck_left_density))
    os.system('%s %s -template %s %s' % (os.path.join(mrtrix_path, 'tckmap'), tck_right, single_frame_FOD, tck_right_density))
    
    # Threshold density maps 
    thresholded_density_left = os.path.join(outputdir, 'native_left_optic_radiation_density_thresholded.nii.gz')
    thresholded_density_right = os.path.join(outputdir, 'native_right_optic_radiation_density_thresholded.nii.gz')    
    os.system('%s -abs %s %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_thresh, tck_left_density, thresholded_density_left))
    os.system('%s -abs %s %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_thresh, tck_right_density, thresholded_density_right))

    # Extract the warp file from the intermediate fixel archive
    os.system('unzip -q -j %s subjects/preproc_wm_fod_%s/warp_calculations/subject2template_warp.mif -d %s' % (calculateFixelsIntermediate, subject_id, subject_workdir))
    fod_warp = os.path.join(subject_workdir, 'subject2template_warp.mif')
    
    # Warp the tracks to FOD template space 
    track_mask_in_template_left = os.path.join(outputdir, 'mask_in_FOD_template_left.nii.gz')
    track_mask_in_template_right = os.path.join(outputdir, 'mask_in_FOD_template_right.nii.gz')
    os.system('%s -warp %s -interp nearest -datatype bit -template %s %s %s' % (os.path.join(mrtrix_path, 'mrtransform'),
                                                                                fod_warp, single_frame_FOD_template,
                                                                                thresholded_density_left, track_mask_in_template_left))    
    os.system('%s -warp %s -interp nearest -datatype bit -template %s %s %s' % (os.path.join(mrtrix_path, 'mrtransform'),
                                                                                fod_warp, single_frame_FOD_template,
                                                                                thresholded_density_right, track_mask_in_template_right))