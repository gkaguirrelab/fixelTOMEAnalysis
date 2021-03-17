import os
import subprocess
import pandas as pd

def fixelAnalysis(mrtrix_path, output_folder_path, subject_fod_list, subject_mask_list, wm_fod_template, fmls_peak_value='0.06'):
    
    '''
    mrtrix_path: Path to mrtrix bin. If you can call mrtrix functions from the terminal, you can leave this empty ''
    output_path: The output folder where the fixel files will be saved
    subject_fod_list: A python list that contains FOD images
    subject_mask_list: A python list that contains MRI mask. Order should match the FOD list
    wm_fod_template: White matter template FOD 
    fmls_peak_values: FOD peak values
    '''
    # Create an output folder if it doesn't exist 
    if not os.path.exists(output_folder_path):
        os.system('mkdir %s' % output_folder_path)
    
    # Get the length of the subject_fod_list and check if you have masks for each of them
    length_fod = len(subject_fod_list)
    length_mask = len(subject_mask_list)
    if length_fod != length_mask:
        raise RuntimeError('The number of input fod images is not equal to number of masks')
    
    # Create a subjects folder in workdir
    main_subject_folder = os.path.join(output_folder_path, 'subjects')
    os.system('mkdir %s' % main_subject_folder)
    
    # Create the template folder
    template_folder = os.path.join(output_folder_path, 'template')
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
        
    # Make full brain stat values
    types = ['fd', 'fc', 'fdc', 'log_fc']
    for ty in types:
        pandasSubject = []
        pandasMean = []
        pandasMedian = []
        pandasStd = []
        pandasMax = []
        pandasMin = []
        fullPandasDict = {}    
        for i in os.listdir(os.path.join(template_folder, '%s' % ty)):   
            if not i == 'index.mif' and not i =='directions.mif':
                imname = i[:-4]
                pandasSubject.append(imname)
                impath = os.path.join(template_folder, '%s' % ty, imname + '.mif')
                
                # Calculate mean
                mean_byte = subprocess.check_output("%s -output mean %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                mean_str = mean_byte.decode('utf-8')
                pandasMean.append(float(mean_str))
                # Add median
                median_byte = subprocess.check_output("%s -output median %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                median_str = median_byte.decode('utf-8')
                pandasMedian.append(float(median_str))         
                # Add std
                std_byte = subprocess.check_output("%s -output std %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                std_str = std_byte.decode('utf-8')
                pandasStd.append(float(std_str))                                           
                # Add min
                min_byte = subprocess.check_output("%s -output min %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                min_str = min_byte.decode('utf-8')
                pandasMin.append(float(min_str))                 
                # Add max
                max_byte = subprocess.check_output("%s -output max %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                max_str = max_byte.decode('utf-8')
                pandasMax.append(float(max_str))   
        fullPandasDict['subject'] = pandasSubject
        fullPandasDict['mean'] = pandasMean
        fullPandasDict['median'] = pandasMedian
        fullPandasDict['std'] = pandasStd
        fullPandasDict['max'] = pandasMax
        fullPandasDict['min'] = pandasMin  
        dataFrame = pd.DataFrame(fullPandasDict)
        dataFrame.set_index('subject', inplace=True)
        dataFrame.to_csv(os.path.join(output_folder_path, '%s_stats.csv' % ty))