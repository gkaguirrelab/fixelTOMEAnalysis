import os 

def calculateAverageResponseFunction(mrtrix_path, subject_dwi_list, bval_list, bvec_list, workdir, output_folder_path, tissue='multi'):
    
    # Create folders in workdir for 3 responses
    wm = os.path.join(workdir, 'wm')
    if not os.path.exists(wm):
        os.system('mkdir %s' % wm)   
    if tissue == 'multi':
        gm = os.path.join(workdir, 'gm')
        if not os.path.exists(gm):
            os.system('mkdir %s' % gm)        
        csf = os.path.join(workdir, 'csf')
        if not os.path.exists(csf):
            os.system('mkdir %s' % csf)
   
    # Calculate response functions for each image
    subject_name_initiate = 0
    for subject in subject_dwi_list:
        bval = bval_list[subject_name_initiate]
        bvec = bvec_list[subject_name_initiate]
        if tissue == 'single':
            os.system('%s tournier %s -fslgrad %s %s %s' % (os.path.join(mrtrix_path, 'dwi2response'), subject,
                                                            bvec, bval, os.path.join(wm, subject_name_initiate + '.txt')))
        elif tissue == 'multi':                   
            os.system('%s dhollander %s -fslgrad %s %s %s %s %s ' % (os.path.join(mrtrix_path, 'dwi2response'), subject, bvec, bval,
                                                                     os.path.join(wm, str(subject_name_initiate) + '.txt'),
                                                                     os.path.join(gm, str(subject_name_initiate) + '.txt'),
                                                                     os.path.join(csf, str(subject_name_initiate) + '.txt')))
        subject_name_initiate += 1

    # Average responses 
    group_average_wm = os.path.join(output_folder_path, 'group_average_wm.txt')
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'responsemean'),
                                os.path.join(wm, '*'), group_average_wm))    
    if tissue == 'multi':         
        group_average_gm = os.path.join(output_folder_path, 'group_average_gm.txt')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'responsemean'),
                                os.path.join(gm, '*'), group_average_gm))
        
        group_average_csf = os.path.join(output_folder_path, 'group_average_csf.txt')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'responsemean'),
                                os.path.join(csf, '*'), group_average_csf))
    
