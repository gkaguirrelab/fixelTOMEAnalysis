import os 

def calculateAverageResponseFunction(mrtrix_path, subject_mask_list, workdir, output_folder_path, shell='multi'):
    
    # Create folders in workdir for 3 responses
    if shell == 'single':    
        wm = os.path.join(workdir, 'wm')
        os.system('mkdir %s' % wm)   
    elif shell == 'multi':
        gm = os.path.join(workdir, 'gm')
        os.system('mkdir %s' % gm)        
        csf = os.path.join(workdir, 'csf')
        os.system('mkdir %s' % csf)
    else:
        raise RuntimeError('shell type unrecognized use single or multi')
   
    # Calculate response functions for each image
    subject_name_initiate = '0'
    for subject in subject_mask_list:
        if shell == 'single':
            os.system('%s tournier %s %s' % (os.path.join(mrtrix_path, 'dwi2response'), subject,
                                             os.path.join(wm, subject_name_initiate + '.txt')))
        elif shell == 'multi':                   
            os.system('%s dhollander %s %s %s %s ' % (os.path.join(mrtrix_path, 'dwi2response'), subject,
                                                      os.path.join(wm, subject_name_initiate + '.txt'),
                                                      os.path.join(gm, subject_name_initiate + '.txt'),
                                                      os.path.join(csf, subject_name_initiate + '.txt')))

    # Average responses
    if shell == 'single':  
        group_average_wm = os.path.join(output_folder_path, 'group_average_wm.txt')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'reponsemean'),
                                os.path.join(wm, '*'), group_average_wm))    
    if shell == 'multi':         
        group_average_gm = os.path.join(output_folder_path, 'group_average_gm.txt')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'reponsemean'),
                                os.path.join(gm, '*'), group_average_gm))
        
        group_average_csf = os.path.join(output_folder_path, 'group_average_csf.txt')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'reponsemean'),
                                os.path.join(csf, '*'), group_average_csf))
    
