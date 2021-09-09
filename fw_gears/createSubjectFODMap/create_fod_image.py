import os 

def create_fod_image(preprocessed_dti, mask, bvecs, bvals, response_wm, response_gm, response_csf, lmax, mrtrix_bin_path, subject_id, workdir, output_dir, use_highest_b=False, n_threads='0'):

    # Create the workdir and output_dir if they don't exist    
    if not os.path.exists(workdir):
        os.system('mkdir %s' % workdir)
    if not os.path.exists(output_dir):
        os.system('mkdir %s' % output_dir)
    
    # Find the highest b-val if use_highest_b is specified and also adjust the
    if use_highest_b == True:       
        file_bval=open(bvals)
        output_list = file_bval.read().split(' ')
        output_list_integer_bval = [int(x) for x in output_list]
        maximum_b = max(output_list_integer_bval)
        
    # Create a log file path  
    log = os.path.join(workdir, 'log.txt')
    
    # Convert Pre-processed DTI to mif format. Embed bvec bval and do b-value 
    # extraction if used the highest b
    preprocessed_dti_mif = os.path.join(workdir, os.path.split(preprocessed_dti)[1].replace('.nii.gz', '.mif'))
    if use_highest_b == False:
        os.system('%s %s -fslgrad %s %s %s > %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), preprocessed_dti, bvecs, bvals, preprocessed_dti_mif, log))  
    else:
        embedded_image = os.path.join(workdir, 'b_embedded.mif')
        os.system('%s %s -fslgrad %s %s %s > %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), preprocessed_dti, bvecs, bvals, embedded_image, log))  
        os.system('%s -shells 0,%s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'dwiextract'), str(maximum_b), embedded_image, preprocessed_dti_mif, log))
                        
    # Calculate 3-tissue functions for individual subjects if it doesn't exist
    if response_wm == '':
        print('Calculating 3-tissue response function')
        response_wm = os.path.join(workdir, 'response_wm.txt')
        response_gm = os.path.join(workdir, 'response_gm.txt')    
        response_csf = os.path.join(workdir, 'response_csf.txt')    
        os.system('%s dhollander %s -fslgrad %s %s %s %s %s -scratch %s >> %s' % (os.path.join(mrtrix_bin_path, 'dwi2response'),
                                                                                  preprocessed_dti_mif, bvecs, bvals, 
                                                                                  response_wm, response_gm, response_csf, workdir, log))
    # Remove the middle b values if doing highest_b 
    if use_highest_b == True and not response_wm == '':
        with open(response_wm) as f:
            wm_text = f.readlines()
            wm_text_size = len(wm_text)     
        new_response_wm = os.path.join(workdir, 'extracted_response_wm')
        new_response_gm = os.path.join(workdir, 'extracted_response_gm')
        new_response_csf = os.path.join(workdir, 'extracted_response_csf')
        if wm_text_size == 5:
            os.system('awk \'NR != 3\' %s > %s' % (response_wm, new_response_wm))
            os.system('awk \'NR != 3\' %s > %s' % (response_gm, new_response_gm))
            os.system('awk \'NR != 3\' %s > %s' % (response_csf, new_response_csf))
            response_wm = new_response_wm
            response_gm = new_response_gm
            response_csf = new_response_csf
        if wm_text_size == 6:              
            os.system('awk \'NR != 3\' %s > %s' % (response_wm, new_response_wm))
            new_new_response_wm = os.path.join(workdir, 'double_extracted_response_wm.txt')
            os.system('awk \'NR != 3\' %s > %s' % (new_response_wm, new_new_response_wm))
            response_wm = new_new_response_wm             
            os.system('awk \'NR != 3\' %s > %s' % (response_gm, new_response_gm))
            new_new_response_gm = os.path.join(workdir, 'double_extracted_response_gm.txt')
            os.system('awk \'NR != 3\' %s > %s' % (new_response_gm, new_new_response_gm))
            response_gm = new_new_response_gm
            os.system('awk \'NR != 3\' %s > %s' % (response_csf, new_response_csf))
            new_new_response_csf = os.path.join(workdir, 'double_extracted_response_csf.txt')
            os.system('awk \'NR != 3\' %s > %s' % (new_response_csf, new_new_response_csf))
            response_csf = new_new_response_csf    
    
    # Upsample DWI images and the mask to isotropic 1.25mm
    print('Upsampling DWI')
    upsampled_dti = os.path.join(workdir, 'upsampled_%s_dti.mif' % subject_id)
    upsampled_mask = os.path.join(workdir, 'upsampled_%s_mask.mif' % subject_id)
    os.system('%s %s regrid -vox 1.25 %s -nthreads %s >> %s' % (os.path.join(mrtrix_bin_path, 'mrgrid'),
                                                                preprocessed_dti_mif, upsampled_dti, n_threads, log))
    os.system('%s %s regrid -vox 1.25 %s -nthreads %s >> %s' % (os.path.join(mrtrix_bin_path, 'mrgrid'),
                                                                mask, upsampled_mask, n_threads, log))
    
    # Create the FOD image
    print('Making a FOD image')
    wm_fod = os.path.join(workdir, 'wm_fod.mif')
    gm_fod = os.path.join(workdir, 'gm_fod.mif')
    csf_fod = os.path.join(workdir, 'csf_fod.mif')
    if use_highest_b == False:
        os.system('%s -version' % os.path.join(mrtrix_bin_path, 'dwi2fod'))
        if lmax == 'NA':
            os.system('%s msmt_csd %s %s %s %s %s %s %s -mask %s -nthreads %s >> %s' % (os.path.join(mrtrix_bin_path, 'dwi2fod'), upsampled_dti,
                                                                                        response_wm, wm_fod, response_gm, gm_fod, response_csf, csf_fod,
                                                                                        upsampled_mask, n_threads, log))
        else:
            os.system('%s msmt_csd %s %s %s %s %s %s %s -mask %s -lmax %s -nthreads %s >> %s' % (os.path.join(mrtrix_bin_path, 'dwi2fod'), upsampled_dti,
                                                                                                 response_wm, wm_fod, response_gm, gm_fod, response_csf, csf_fod,
                                                                                                 upsampled_mask, lmax, n_threads, log))
    else:
        os.system('%s -version' % os.path.join(mrtrix_bin_path, 'ss3t_csd_beta1'))
        os.system('%s -mask %s -nthreads %s %s %s %s %s %s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'ss3t_csd_beta1'), upsampled_mask, n_threads, upsampled_dti,
                                                                           response_wm, wm_fod, response_gm, gm_fod, response_csf, csf_fod, log))        
        
    # Calculate a more conservetive mask from the upsampled data for the next
    # step (bias coorection and intensity normalization)
    normalize_mask = os.path.join(workdir, 'normalize_mask.mif')
    os.system('%s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'dwi2mask'), upsampled_dti, normalize_mask, log))
    
    # Correct and intensity normalize the image. This step is suggested even
    # if a previous field correction was applied. It will coorect residual 
    # intensity inhomogeneities
    print('Correcting FOD intensity')
    normalized_wm_fod = os.path.join(output_dir, 'preproc_wm_fod_%s.mif' % subject_id)
    normalized_gm_fod = os.path.join(output_dir, 'preproc_gm_fod_%s.mif' % subject_id)
    normalized_csf_fod = os.path.join(output_dir, 'preproc_csf_fod_%s.mif' % subject_id)
    os.system('%s %s %s %s %s %s %s -mask %s >> %s' % (os.path.join(mrtrix_bin_path, 'mtnormalise'), wm_fod, normalized_wm_fod,
                                                       gm_fod, normalized_gm_fod, csf_fod, normalized_csf_fod, normalize_mask, log))
    
    # Save nifti versions of the images
    normalized_wm_fod_nifti = os.path.join(output_dir, 'preproc_wm_fod_%s.nii.gz' % subject_id)
    normalized_gm_fod_nifti = os.path.join(output_dir, 'preproc_gm_fod_%s.nii.gz' % subject_id)
    normalized_csf_fod_nifti = os.path.join(output_dir, 'preproc_csf_fod_%s.nii.gz' % subject_id)
    os.system('%s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), normalized_wm_fod, normalized_wm_fod_nifti, log))
    os.system('%s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), normalized_gm_fod, normalized_gm_fod_nifti, log))
    os.system('%s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), normalized_csf_fod, normalized_csf_fod_nifti, log))
    
    # Output the upsampled mask in mif and nifti formats
    mask_new_path = os.path.join(output_dir, 'upsampled_%s_mask.nii.gz' % subject_id)    
    os.system('cp %s %s' % (upsampled_mask, output_dir))
    os.system('%s %s %s >> %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), upsampled_mask, mask_new_path, log))