import os

def extract_dti_values(fa_image, other_metrics, workdir, output_folder_path, left_track, right_track, tckmap_template, mrtrix_path='', freesurfer_path='', ants_path='', track_density_thresh='1', binary_threshold='1'):

    '''
    fa_image: input FA image from FSL DTIfit. FA image is used for registration since it has the best contrast among other
    DTI measures. Pass other metric images to other_metrics flag as a python list to move the tracks to 
    them.
    other_metrics: other metrics to process
    workdir: Wordir folder where intermediate files will be saved
    output_folder_path: The output folder where the fixel files will be saved
    left_track: Left hemisphere track
    right_track: Right hemisphere track
    tckmap_template = Template in which the tracts were calculated
    mrtrix_warp = warp tracks to another coordinates using a mrtrix warp file
    mrtrix_path: Path to mrtrix bin. If you can call mrtrix functions from the terminal, you can leave this empty ''
    freesurfer_path: path to freesurfer bin 
    track_density_thresh: Select only those voxels that have the specified amount of fibres running through it
    binary_threshold: Threshold to binarize the track density images. 1 default is pretty liberal
    '''
    #### Process tractography ####
    
    # Convert vtk to tck
    tractography_folder = os.path.join(workdir, 'tractography')
    os.system('mkdir %s' % tractography_folder)
    if not left_track == 'NA': 
        left_track_tck = os.path.join(tractography_folder, 'left_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, left_track_tck))
    if not right_track == 'NA':
        right_track_tck = os.path.join(tractography_folder, 'right_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, right_track_tck))
            
    # Combine the tracks if more than one exist 
    if not left_track == 'NA' and not right_track == 'NA':
        left_and_right_tck = os.path.join(tractography_folder, 'left_and_right_tracks.tck')
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'tckedit'), left_track_tck, right_track_tck, left_and_right_tck))
    elif not left_track == 'NA':
        left_and_right_tck = left_track_tck
    elif not right_track == 'NA':
        left_and_right_tck = right_track_tck
    else:
        raise RuntimeError('You need to specify at least one track to extract values from')
    
    # Calculate track density map    
    track_density_map = os.path.join(workdir, 'track_density_map.nii.gz')
    os.system('%s %s %s -template %s' % (os.path.join(mrtrix_path, 'tckmap'), left_and_right_tck, 
                                         track_density_map, tckmap_template))
    
    # Threshold the track density map
    thresholded_track = os.path.join(workdir, 'thresholded.nii.gz')
    os.system('%s %s -abs %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_map, 
                                    track_density_thresh, thresholded_track))
    
    # Binarize the thresholded track density map
    binary_track_mask = os.path.join(workdir, 'binary_mask.nii.gz')
    os.system('%s --i %s --min %s --o %s' % (os.path.join(freesurfer_path, 'mri_binarize'), thresholded_track,
                                             binary_threshold, binary_track_mask))
    
    # Warp the image which the track was based on and warp it to the target    
    warp_workdir = os.path.join(workdir, 'warp_workdir')
    os.system('mkdir %s' % warp_workdir)
    output_name = os.path.join(warp_workdir, 'tckmap2fod')
    output_warped = os.path.join(warp_workdir, 'tckmap2fodWarped.nii.gz')
    output_inverse_warped = os.path.join(warp_workdir, 'tckmap2fodInverseWarped.nii.gz')    
    output_warp = os.path.join(warp_workdir, 'tckmap2fod1Warp.nii.gz')
    output_affine = os.path.join(warp_workdir, 'tckmap2fod0GenericAffine.mat')
    
    command = '%s --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 \
--winsorize-image-intensities [ 0.005,0.995 ] --initial-moving-transform [ %s,%s,1 ] \
--transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 \
--smoothing-sigmas 3x2x1x0vox --transform Affine[ 0.1 ] \
--metric MI[ %s,%s,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox' % (os.path.join(ants_path, 'antsRegistration'),
                                                           output_name, output_warped, 
                                                           output_inverse_warped, fa_image, 
                                                           tckmap_template, fa_image, 
                                                           tckmap_template, fa_image, 
                                                           tckmap_template)
    
    os.system(command)
    
    # Move the track to the target dti space
    binary_track_mask_warped = os.path.join(workdir, 'binary_mask_warped.nii.gz')
    os.system('%s -d 3 -i %s -r %s -o %s -t %s -t %s' % (os.path.join(ants_path, 'applyApplyTransforms'),
                                                         binary_track_mask, fa_image, binary_track_mask_warped,
                                                         output_warp, output_affine))
    
    # Extract the tracks from all metrics 
    subject_id = os.path.split(fa_image)[1][:-10]
    subject_folder = os.path.join(output_folder_path, subject_id)
    FA_folder = os.path.join(subject_folder, 'FA')
    os.system('mkdir %s' % FA_folder)
    extracted_fa_track = os.path.join(FA_folder, 'FA.nii.gz')
    os.system('%s %s %s %s' % (os.path.join(freesurfer_path, 'mri_mask'),
                               fa_image, binary_track_mask_warped, extracted_fa_track))    
    for i in other_metrics:
        metric_name = os.path.split(i)[1][-9:-7]
        metric_folder = os.path.join(subject_folder, metric_name)
        metric_file = os.path.join(metric_folder, metric_name + '.nii.gz')
        os.system('%s %s %s %s' % (os.path.join(freesurfer_path, 'mri_mask'),
                                   i, binary_track_mask_warped, metric_file))        
    
    
    