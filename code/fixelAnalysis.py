import os

def fixelAnalysis(mrtrix_path, workdir, output_folder, subject_fod_list, subject_mask_list, wm_fod_template, left_track, right_track, fmls_peak_value='0.06', track_density_thresh='1'):
    
    # Get the length of the subject_fod_list and check if you have masks for each of them
    length_fod = len(subject_fod_list)
    length_mask = len(subject_mask_list)
    if length_fod != length_mask:
        raise RuntimeError('The number of input fod images is not equal to number of masks')
    
    # Create a subjects folder in workdir
    main_subject_folder = os.path.join(workdir, 'subjects')
    os.system('mkdir %s' % main_subject_folder)
    
    # Create the template folder
    template_folder = os.path.join(workdir, 'template')
    os.system('mkdir %s' % template_folder)
    
    # Copy the wm template in the template folder
    os.system('cp %s %s/' % (wm_fod_template, template_folder))
    
    # Create an empty list for registered masks which will be populated later 
    all_masks_in_template = []
    
    # Loop through subject paths
    for num_subject in range(length_fod):
        # Get individual subject fod and mask path
        fod_path = subject_fod_list[num_subject]
        mask_path = subject_mask_list[num_subject]
        
        # Get the subject name
        fod_name = os.path.split(fod_path)[1][:8]
        
        # Make subject folders for each subject 
        subject_folder = os.path.join(main_subject_folder, fod_name)        
        if not os.path.exists(subject_folder):
            os.system('mkdir %s' % subject_folder)
        else:
            raise RuntimeError('You have two images with the same name. Make sure you are not using the same subject multiple times')
        
        # Move the fod and mask images in their subject folders after converting to mif
        new_fod_path_and_name = os.path.join(subject_folder, 'wm_fod.mif')
        new_mask_path_and_name = os.path.join(subject_folder, 'mask.mif')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'mrconvert'), fod_path, new_fod_path_and_name))
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'mrconvert'), mask_path, new_mask_path_and_name))
        
        # Create the warp calculation workdir for each subject
        warp_calculations = os.path.join(subject_folder, 'warp_calculations')
        if not os.path.exists(warp_calculations):
            os.system('mkdir %s' % warp_calculations)
    
        # Calculate warps between each subjects and the template
        subject_to_template = os.path.join(warp_calculations, 'subject2template_warp.mif')
        template_to_subject = os.path.join(warp_calculations, 'template2subject_warp.mif')
        os.system('%s %s -mask1 %s %s -nl_warp %s %s' % (os.path.join(mrtrix_path, 'mrregister'),
                                                          fod_path, mask_path,
                                                          wm_fod_template, subject_to_template,
                                                          template_to_subject))
        
        # Transform masks to the template space
        mask_in_template = os.path.join(subject_folder, 'dwi_mask_in_template_space.mif')  
        os.system('%s %s -warp %s -interp nearest -datatype bit %s' % (os.path.join(mrtrix_path, 'mrtransform'),
                                                                        mask_path, subject_to_template,
                                                                        mask_in_template))
         
        # Populate the all_masks_template with the paths to the mask_in_template
        all_masks_in_template.append(mask_in_template)
        
    # Here we calculate an intersection of all masks outside the loop
    # to make a template mask
    template_mask = os.path.join(template_folder, 'template_mask.mif')
    initial_mask_command = '%s ' % os.path.join(mrtrix_path, 'mrmath')
    for m in all_masks_in_template: # Get paths and append to the command 
        initial_mask_command = initial_mask_command + m + ' '
    final_mask_command = initial_mask_command + 'min %s -datatype bit' % template_mask
    os.system(final_mask_command)
    
    # Calculate fixel mask from the template mask and FOD template
    fixel_mask = os.path.join(template_folder, 'fixel_mask')
    os.system('%s -mask %s -fmls_peak_value %s %s %s' % (os.path.join(mrtrix_path, 'fod2fixel'), template_mask,
                                                          fmls_peak_value, wm_fod_template, fixel_mask))
        
    # Loop through each subject and register them to the template using the warps
    # we calculated in the previous loop
    for sf in os.listdir(main_subject_folder):
        subject_path_in_folder = os.path.join(main_subject_folder, sf)
        os.system('%s %s -warp %s -reorient_fod no %s' % (os.path.join(mrtrix_path, 'mrtransform'),
                                                          os.path.join(subject_path_in_folder, 'wm_fod.mif'), 
                                                          os.path.join(subject_path_in_folder, 'warp_calculations', 'subject2template_warp.mif'),
                                                          os.path.join(subject_path_in_folder, 'fod_in_template_space_NOT_REORIENTED.mif')))
        
        # Calculate FD values for each subject         
        os.system('%s -mask %s %s %s -afd fd.mif' % (os.path.join(mrtrix_path, 'fod2fixel'),
                                                      template_mask, 
                                                      os.path.join(subject_path_in_folder, 'fod_in_template_space_NOT_REORIENTED.mif'),
                                                      os.path.join(subject_path_in_folder, 'fixel_in_template_space_NOT_REORIENTED')))
        
        # Reorienting fixels 
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelreorient'),
                                    os.path.join(subject_path_in_folder, 'fixel_in_template_space_NOT_REORIENTED'),
                                    os.path.join(subject_path_in_folder, 'warp_calculations', 'subject2template_warp.mif'),
                                    os.path.join(subject_path_in_folder, 'fixel_in_template_space')))
    
        # Assign subject fixels to the template image
        os.system('%s %s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcorrespondence'),
                                      os.path.join(subject_path_in_folder, 'fixel_in_template_space', 'fd.mif'),
                                      fixel_mask, os.path.join(template_folder, 'fd'), '%s.mif' % sf))
        
        # Compute FC metric 
        os.system('%s %s -fc %s %s %s' % (os.path.join(mrtrix_path, 'warp2metric'),
                                          os.path.join(subject_path_in_folder, 'warp_calculations', 'subject2template_warp.mif'),
                                          fixel_mask, os.path.join(template_folder, 'fc'), '%s.mif' % sf))
        
        # Compute logFC from FC values 
        if not os.path.exists(os.path.join(template_folder, 'log_fc')):
            os.system('mkdir %s' % os.path.join(template_folder, 'log_fc'))
            os.system('cp %s %s' % (os.path.join(template_folder, 'fc', 'index.mif'), os.path.join(template_folder, 'log_fc')))
            os.system('cp %s %s' % (os.path.join(template_folder, 'fc', 'directions.mif'), os.path.join(template_folder, 'log_fc')))
        os.system('%s %s -log %s' % (os.path.join(mrtrix_path, 'mrcalc'),
                                      os.path.join(template_folder, 'fc', '%s.mif' % sf),
                                      os.path.join(template_folder, 'log_fc', '%s.mif' % sf)))
        
        # Compute FDC 
        if not os.path.exists(os.path.join(template_folder, 'fdc')):
            os.system('mkdir %s' % os.path.join(template_folder, 'fdc'))
            os.system('cp %s %s' % (os.path.join(template_folder, 'fc', 'index.mif'), os.path.join(template_folder, 'fdc')))
            os.system('cp %s %s' % (os.path.join(template_folder, 'fc', 'directions.mif'), os.path.join(template_folder, 'fdc')))
        os.system('%s %s %s -mult %s' % (os.path.join(mrtrix_path, 'mrcalc'),
                                          os.path.join(template_folder, 'fd', '%s.mif' % sf),
                                          os.path.join(template_folder, 'fc', '%s.mif' % sf),
                                          os.path.join(template_folder, 'fdc', '%s.mif' % sf)))

    #### Process tractography ####
    # Convert vtk to tck
    tractography_folder = os.path.join(workdir, 'tractography')
    os.system('mkdir %s' % tractography_folder)
    left_track_tck = os.path.join(tractography_folder, 'left_tract.tck')
    right_track_tck = os.path.join(tractography_folder, 'right_tract.tck')
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, left_track_tck))
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, right_track_tck))
            
    # Combine the tracks
    left_and_right_tck = os.path.join(tractography_folder, 'left_and_right_tracks.tck')
    os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'tckedit'), left_track_tck, right_track_tck, left_and_right_tck))
    
    # Map tracks to the fixel template 
    fixel_folder_tracked = os.path.join(tractography_folder, 'fixel_folder_tracked')
    os.system('%s %s %s %s track_density' % (os.path.join(mrtrix_path, 'tck2fixel'), left_and_right_tck,
                                              fixel_mask, fixel_folder_tracked))
    track_density_file = os.path.join(fixel_folder_tracked, 'track_density.mif')
    
    # Threshold track density
    track_density_thresholded = os.path.join(fixel_folder_tracked, 'thresh_track_density.mif')
    os.system('mrthreshold -abs %s %s %s' % (track_density_thresh, track_density_file, track_density_thresholded))

    # Crop the fixels from subject FD, FC, and FDC
    if not os.path.exists(output_folder):
        os.system('mkdir %s' % output_folder)
    os.system('fixelcrop %s %s %s' % (os.path.join(template_folder, 'fd'), track_density_thresholded, 
                                      os.path.join(output_folder, 'cropped_fd')))
    os.system('fixelcrop %s %s %s' % (os.path.join(template_folder, 'fc'), track_density_thresholded, 
                                      os.path.join(output_folder, 'cropped_fc')))
    os.system('fixelcrop %s %s %s' % (os.path.join(template_folder, 'fdc'), track_density_thresholded, 
                                      os.path.join(output_folder, 'cropped_fdc')))