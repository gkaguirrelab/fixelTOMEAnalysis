import os 

def create_fod_population_template(fod_list, mask_list, path_to_mrtrix_bin, workdir, voxel_size, output_template_file):
    
    '''
    This is a wrapper around MRtrix "population_template" function for a 
    Flywheel gear.
    
    Inputs:
        - fod_list = A python list containing paths to the FOD images
        - mask_list = A python list containing paths to the masks. Make sure 
        that the order of the masks matches the order of the images (eg. first
        mask on the mask_list belongs to the first fod image on the fod_list) 
        - path_to_mrtrix_bin = Path to the bin file inside the MRtrix 
        installation folder. If MRtrix is already in your path (You can call
        MRtrix functions from a terminal without specifying the direct path),
        you can leave this flag empty (path_to_mrtrix_bin = '')
        - workdir = This is the path where the folders will be organized.
        - voxel_size = enter one number if isotropic. Otherwise, comma seperated
        - output_template_file = This is the final template file. Should have 
        the .mif extension         
    '''
    
    # Create the input and mask folders in the workdirectory
    input_fods = os.path.join(workdir, 'input_fods')
    input_masks = os.path.join(workdir, 'input_masks')
    
    if not os.path.exists(input_fods):
        os.system('mkdir %s' % input_fods)
    if not os.path.exists(input_masks):
        os.system('mkdir %s' % input_masks)
        
    # Get the length of the list
    num_images = len(fod_list)    
    for i in range(num_images):
        new_file_name = str(i + 1) + '.mif'
        print('renaming %s to %s' % (os.path.split(fod_list[i])[1], new_file_name))
        print('renaming %s to %s' % (os.path.split(mask_list[i])[1], new_file_name))
        os.system('cp %s %s' % (fod_list[i], os.path.join(input_fods, new_file_name)))
        os.system('cp %s %s' % (mask_list[i], os.path.join(input_masks, new_file_name)))
    
    os.system('%s %s -mask_dir %s %s -voxel_size %s -scratch %s' % (os.path.join(path_to_mrtrix_bin, 'population_template'),
                                                                    input_fods, input_masks, output_template_file,
                                                                    voxel_size, workdir))
    
    return (workdir, output_template_file)
        
    
