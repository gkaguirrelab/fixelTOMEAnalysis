import os 

def create_fod_population_template(qsirecon_list, path_to_mrtrix_bin, workdir, output_template_file):
    
    '''
    This is a wrapper around MRtrix "population_template" function. The 
    original function requires two folders, one containing the FOD maps and the 
    other containing the subject specific masks. This function accepts a python
    list of qsirecon output archives and extracts and properly moves the maps 
    and the masks to get them ready for the template function. 
    
    Requirements:
        In order for this function to work properly, you should be able to call
        "unzip" from your terminal
    
    Inputs:
        - qsirecon_list = A python list containing paths to the qsirecon 
        archives (e.g. ["/myfiles/qsirecon1.zip, /myfiles/qsirecon2.zip"] )
        - path_to_mrtrix_bin = Path to the bin file inside the MRtrix 
        installation folder. If MRtrix is already in your path (You can call
        MRtrix functions from a terminal without specifying the direct path),
        you can leave this flag empty (path_to_mrtrix_bin = '')
        - workdir = This is the path where the input folders will be organized.
        - output_template_file = This is the final template file. Should have 
        the .mif extension         
        
    Outputs:
        - FOD maps are placed in <workdir>/input_fods
        - Masks are placed in <workdir>/input_masks
        - The final template
    '''
    
    # Create the input and mask folders in the workdirectory
    input_fods = os.path.join(workdir, 'input_fods')
    input_masks = os.path.join(workdir, 'input_masks')
    
    if os.path.exists(input_fods):
        os.system('mkdir %s' % input_fods)
    if os.path.exists(input_masks):
        os.system('mkdir %s' % input_masks)
        
    # Loop through the zip archives, unzip them and organize the FOD and masks
    temporary_unzip_folder = os.path.join(workdir, 'temporary_zips')
    if os.path.exists(temporary_unzip_folder):
        os.system('mkdir %s' % temporary_unzip_folder)
    for i in qsirecon_list:
        subject_name = os.path.basename(i)[:-4].split('_')[1]
        folder_name = os.path.basename(i)[:-4].split('_')[2]
        os.system('unzip -q %s -d %s' % (i, temporary_unzip_folder))
        subject_folder = os.path.join(temporary_unzip_folder, folder_name,
                                      'qsirecon', subject_name)
        for session in os.listdir(subject_folder):
            if 'ses' in session:
                # Construct the image and mask names 
                fod_name = subject_name+'_'+session+'_'+'space-T1w_desc-preproc_space-T1w_desc-wmFODmtnormed_msmtcsd.mif'
                mask_name = subject_name+'_'+session+'_'+'space-T1w_desc-preproc_space-T1w_desc-mtinliermask_msmtcsd.nii'
                # Get the full paths to the image and the mask
                image = os.path.join(subject_folder, session, 'dwi', fod_name)
                mask = os.path.join(subject_folder, session, 'dwi', mask_name)  
                # Create the new fod and mask names
                new_fod_name = subject_name+'_'+session+'.mif'
                new_mask_name = subject_name+'_'+session+'.nii'
                # Copy the images and masks into the workdir
                os.system('cp %s %s' % (image, os.path.join(input_fods, new_fod_name)))
                os.system('cp %s %s' % (mask, os.path.join(input_masks, new_mask_name)))
    
    os.system('%s %s -mask_dir %s %s' % (os.path.join(path_to_mrtrix_bin, 'population_template'),
                                         input_fods, input_masks, output_template_file))
        
    return (workdir, output_template_file)
        
    