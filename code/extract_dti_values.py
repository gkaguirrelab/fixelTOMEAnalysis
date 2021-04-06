import os, subprocess

def extract_dti_values(metric_image, workdir, output_folder_path, left_track, right_track, tckmap_template, mrtrix_path='', freesurfer_path='', ants_path='', fslpath='', track_density_thresh='1', binary_threshold='1'):

    '''
    metric_image: input FA image from FSL DTIfit. FA image is used for registration since it has the best contrast among other
    DTI measures. Pass other metric images to other_metrics flag as a python list to move the tracks to 
    them.
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
    ### Process tractography ####

    # Get subject name and metric name
    subject_id = os.path.split(metric_image)[1][:-10]
    metric_name = os.path.split(metric_image)[1][-9:-7]
    
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
    track_density_map = os.path.join(tractography_folder, 'track_density_map.nii.gz')
    os.system('%s %s %s -template %s' % (os.path.join(mrtrix_path, 'tckmap'), left_and_right_tck, 
                                          track_density_map, tckmap_template))
    
    # Threshold the track density map
    thresholded_track = os.path.join(tractography_folder, 'thresholded.nii.gz')
    os.system('%s %s -abs %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_map, 
                                    track_density_thresh, thresholded_track))
    
    # Warp the image which the track was based on and warp it to the target    
    warp_workdir = os.path.join(workdir, 'warp_workdir')
    os.system('mkdir %s' % warp_workdir)
    extracted_template = os.path.join(warp_workdir, 'extracted_template.nii.gz')
    os.system('%s %s %s 0 1' % (os.path.join(fslpath,'fslroi'), tckmap_template, extracted_template))
    output_name = os.path.join(warp_workdir, 'tckmap2fod')
    output_warped = os.path.join(warp_workdir, '%s_tckmap2fodWarped.nii.gz' % subject_id)
    output_inverse_warped = os.path.join(warp_workdir, '%s_tckmap2fodInverseWarped.nii.gz' % subject_id)    
    output_warp = os.path.join(warp_workdir, '%s_tckmap2fod1Warp.nii.gz' % subject_id)
    output_affine = os.path.join(warp_workdir, '%s_tckmap2fod0GenericAffine.mat' % subject_id)
    
    command = 'ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=7; %s --verbose 1 --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 \
--winsorize-image-intensities [ 0.005,0.995 ] --initial-moving-transform [ %s,%s,1 ] \
--transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 \
--smoothing-sigmas 3x2x1x0vox --transform Affine[ 0.1 ] \
--metric MI[ %s,%s,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox --transform SyN[ 0.1,3,0 ] \
--metric CC[ %s,%s,1,4 ] --convergence [ 100x70x50x20,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox' % (os.path.join(ants_path, 'antsRegistration'),
                                                            output_name, output_warped, 
                                                            output_inverse_warped, metric_image, 
                                                            extracted_template, metric_image, 
                                                            extracted_template, metric_image, 
                                                            extracted_template, metric_image,
                                                            extracted_template)
    
    
    os.system(command)
    
    # Move the track to the target dti space
    binary_track_mask_warped = os.path.join(workdir, 'binary_mask_warped.nii.gz')
    os.system('%s -d 3 -i %s -r %s -o %s -n NearestNeighbor -t [ %s, 1 ] -t %s' % (os.path.join(ants_path, 'antsApplyTransforms'),
                                                                                   thresholded_track, metric_image, binary_track_mask_warped,
                                                                                   output_affine, output_inverse_warped))
    
    # Extract the tracks from the metric
    extracted_metric_image = os.path.join(workdir, '%s_%s_extracted.nii.gz' % (subject_id, metric_name))
    os.system('%s %s %s %s' % (os.path.join(freesurfer_path, 'mri_mask'),
                                metric_image, binary_track_mask_warped, extracted_metric_image))
    
    # Get the mean metric value
    metric_value_raw = subprocess.check_output(['%s' % os.path.join(fslpath, 'fslstats'), '%s' % extracted_metric_image, '-M'])
    metric_value = float(metric_value_raw.decode('utf-8'))
    
    return metric_value