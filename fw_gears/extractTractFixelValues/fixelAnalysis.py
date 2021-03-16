import os
import subprocess
import pandas as pd

def fixelAnalysis(mrtrix_path, workdir, output_folder, subject_fod_list, subject_mask_list, wm_fod_template, left_track, right_track, fmls_peak_value='0.06', track_density_thresh='1', smooth_fixels=False):
    
    '''
    mrtrix_path: Path to mrtrix bin. If you can call mrtrix functions from the terminal, you can leave this empty ''
    workdir: Workdir where the intermediate files will be saved.
    output_path: The output folder where the cropped fixel files will be saved
    subject_fod_list: A python list that contains FOD images
    subject_mask_list: A python list that contains MRI mask. Order should match the FOD list
    wm_fod_template: White matter template FOD 
    left_tract: Left hemisphere tractography streamlines
    right_tract: RIght hemisphere tractography streamlines
    fmls_peak_values: FOD peak values
    tract_density: Threshold to decide how many steams should pass through a voxel for that voxel to be selected
    smooth_fixels: Smooth fixels by fixel-fixel connectivity calculatedwith the streamlines  
    '''
    
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
        if 'nii.gz' in os.path.split(fod_path)[1]:
            fod_name = os.path.split(fod_path)[1].replace('.nii.gz', '')
        elif '.mif' in os.path.split(fod_path)[1]:
            fod_name = os.path.split(fod_path)[1].replace('.mif', '')
        else:
            raise RuntimeError('Input image type is not recognzied. Use mif or nifti files')
        
        # Make subject folders for each subject 
        subject_folder = os.path.join(main_subject_folder, fod_name)        
        if not os.path.exists(subject_folder):
            os.system('mkdir %s' % subject_folder)
        else:
            raise RuntimeError('You have two images with the same name. Make sure you are not using the same subject multiple times')
        
        # Move the fod and mask images in their subject folders after converting to mif if input is nifti
        new_fod_path_and_name = os.path.join(subject_folder, 'wm_fod.mif')
        new_mask_path_and_name = os.path.join(subject_folder, 'mask.mif')
        if 'nii.gz' in os.path.split(fod_path)[1]:
            os.system('%s %s %s' % (os.path.join(mrtrix_path, 'mrconvert'), fod_path, new_fod_path_and_name))
            os.system('%s %s %s' % (os.path.join(mrtrix_path, 'mrconvert'), mask_path, new_mask_path_and_name))
        else:
            os.system('cp %s %s' % (fod_path, new_fod_path_and_name))
            os.system('cp %s %s' % (mask_path, new_mask_path_and_name))
            
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
    if not left_track == 'NA': 
        left_track_tck = os.path.join(tractography_folder, 'left_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, left_track_tck))
    if not left_track == 'NA':
        right_track_tck = os.path.join(tractography_folder, 'right_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, right_track_tck))
            
    # Combine the tracks if more than one exist 
    if not left_track == 'NA' and not right_track == 'NA':
        left_and_right_tck = os.path.join(tractography_folder, 'left_and_right_tracks.tck')
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'tckedit'), left_track_tck, right_track_tck, left_and_right_tck))
    elif not left_track == 'NA':
        left_and_right_tck = left_track
    elif not right_track == 'NA':
        left_and_right_tck = right_track
    else:
        raise RuntimeError('You need to specify at least one track to extract values from')
    
    # Calculate fixel2fixel measurements and smooth fixel data if requested
    if smooth_fixels == True:
        smoothed_fd_dir = os.path.join(template_folder, 'smooth_fd')
        smoothed_fc_dir = os.path.join(template_folder, 'smooth_fc')
        smoothed_log_fc_dir = os.path.join(template_folder, 'smooth_log_fc')
        smoothed_fdc_dir = os.path.join(template_folder, 'smooth_fdc')
        
        fixel_fixel_connectivity_dir = os.path.join(workdir, 'fixel2fixelConn')
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelconnectivity'),
                                    fixel_mask, left_and_right_tck, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(template_folder, 'fd'),
                                                  smoothed_fd_dir, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(template_folder, 'fc'),
                                                  smoothed_fc_dir, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(template_folder, 'log_fc'),
                                                  smoothed_log_fc_dir, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(template_folder, 'fdc'),
                                                  smoothed_fdc_dir, fixel_fixel_connectivity_dir))        
        
    # Map tracks to the fixel template 
    fixel_folder_tracked = os.path.join(tractography_folder, 'fixel_folder_tracked')
    os.system('%s %s %s %s track_density.mif' % (os.path.join(mrtrix_path, 'tck2fixel'), left_and_right_tck,
                                              fixel_mask, fixel_folder_tracked))
    track_density_file = os.path.join(fixel_folder_tracked, 'track_density.mif')
    
    # Threshold track density
    track_density_thresholded = os.path.join(fixel_folder_tracked, 'thresh_track_density.mif')
    os.system('%s -abs %s %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_thresh, track_density_file, track_density_thresholded))

    # Create the output folder if it doesn't exist 
    if not os.path.exists(output_folder):
        os.system('mkdir %s' % output_folder)
    
    # Crop the fixels from subject FD, FC, and FDC 
    if smooth_fixels == False:     
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(template_folder, 'fd'), track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_fd')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(template_folder, 'fc'), track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_fc')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(template_folder, 'log_fc'), track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_log_fc')))    
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(template_folder, 'fdc'), track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_fdc')))
    elif smooth_fixels == True:
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_fd_dir, track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_fd')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_fc_dir, track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_fc')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_log_fc_dir, track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_log_fc')))    
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_fdc_dir, track_density_thresholded, 
                                    os.path.join(output_folder, 'cropped_fdc')))
    else:
        raise RuntimeError('smooth_fixels option was set to something other than False or True')
         
    # Extract FD, FC, log_FC and FDC stats from images and write them to a text file and create a pandas object for cvs save
    types = ['fd', 'fc', 'fdc', 'log_fc']
    for ty in types:
        text_file = open('%s' % os.path.join(output_folder, '%s_stats.txt' % ty), 'w')
        initial_txt = ''
        pandasSubject = []
        pandasMean = []
        pandasMedian = []
        pandasStd = []
        pandasMax = []
        pandasMin = []
        fullPandasDict = {}
        for i in os.listdir(os.path.join(output_folder, 'cropped_%s' % ty)):
            if not i == 'index.mif' and not i =='directions.mif':
                # Get image name and path
                imname = i[:-4]
                pandasSubject.append(imname)
                impath = os.path.join(output_folder, 'cropped_%s' % ty, imname + '.mif')
                # Add image name to the path
                initial_txt = initial_txt + imname + ' \n\n'
                # Add mean
                mean_byte = subprocess.check_output("%s -output mean %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                mean_str = mean_byte.decode('utf-8')
                pandasMean.append(float(mean_str))
                initial_txt = initial_txt + 'mean ' + mean_str
                # Add median
                median_byte = subprocess.check_output("%s -output median %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                median_str = median_byte.decode('utf-8')
                pandasMedian.append(float(median_str))
                initial_txt = initial_txt + 'median ' + median_str            
                # Add std
                std_byte = subprocess.check_output("%s -output std %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                std_str = std_byte.decode('utf-8')
                pandasStd.append(float(std_str))                
                initial_txt = initial_txt + 'std ' + std_str                            
                # Add min
                min_byte = subprocess.check_output("%s -output min %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                min_str = min_byte.decode('utf-8')
                pandasMin.append(float(min_str))   
                initial_txt = initial_txt + 'min ' + min_str               
                # Add max
                max_byte = subprocess.check_output("%s -output max %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                max_str = max_byte.decode('utf-8')
                pandasMax.append(float(max_str)) 
                initial_txt = initial_txt + 'max ' + max_str + '\n\n'   
        fullPandasDict['subject'] = pandasSubject
        fullPandasDict['mean'] = pandasMean
        fullPandasDict['median'] = pandasMedian
        fullPandasDict['std'] = pandasStd
        fullPandasDict['max'] = pandasMax
        fullPandasDict['min'] = pandasMin  
        dataFrame = pd.DataFrame(fullPandasDict)
        dataFrame.set_index('subject', inplace=True)
        dataFrame.to_csv(os.path.join(output_folder, '%s_stats.csv' % ty))
        text_file.write(initial_txt)
        text_file.close()
