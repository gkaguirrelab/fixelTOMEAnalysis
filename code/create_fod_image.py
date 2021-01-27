import os 

def create_fod_image(preprocessed_dti, mask, bvecs, bvals, mrtrix_bin_path, fsl_bin_path, subject_id, workdir, output_dir):

    # Create the workdir and output_dir if they don't exist    
    if not os.path.exists(workdir):
        os.system('mkdir %s' % workdir)
    if not os.path.exists(output_dir):
        os.system('mkdir %s' % output_dir)

    # Calculate 3-tissue functions for individual subjects
    response_wm = os.path.join(workdir, 'response_wm.txt')
    response_gm = os.path.join(workdir, 'response_gm.txt')    
    response_csf = os.path.join(workdir, 'response_csf.txt')    
    os.system('%s dhollander %s -fslgrad %s %s %s %s %s' % (os.path.join(mrtrix_bin_path, 'dwi2response'),
                                                                         preprocessed_dti, bvecs, bvals, 
                                                                         response_wm, response_gm, response_csf))
    
    # Upsample DWI images and the mask to isotropic 1.25mm
    upsampled_dti = os.path.join(workdir, 'upsampled_%s_dti.mif' % subject_id)
    upsampled_mask = os.path.join(workdir, 'upsampled_%s_mask.mif' % subject_id)
    os.system('%s %s regrid -vox 1.25 %s' % (os.path.join(mrtrix_bin_path, 'mrgrid'),
                                             preprocessed_dti, upsampled_dti))
    os.system('%s %s regrid -vox 1.25 %s' % (os.path.join(mrtrix_bin_path, 'mrgrid'),
                                             mask, upsampled_mask))
    
    # Create the FOD image
    wm_fod = os.path.join(workdir, 'wm_fod.mif')
    gm_fod = os.path.join(workdir, 'gm_fod.mif')
    csf_fod = os.path.join(workdir, 'csf_fod.mif')
    os.system('%s msmt_csd %s %s %s %s %s %s %s -mask %s -lmax 8,8,8' % (os.path.join(mrtrix_bin_path, 'dwi2fod'), upsampled_dti,
                                                                         response_wm, wm_fod, response_gm, gm_fod, response_csf, csf_fod,
                                                                         upsampled_mask))
    
    # Calculate a more conservetive mask from the upsampled data for the next
    # step (bias coorection and intensity normalization)
    normalize_mask = os.path.join(workdir, 'normalize_mask.mif')
    os.system('%s %s %s' % (os.path.join(mrtrix_bin_path, 'dwi2mask'), upsampled_dti, normalize_mask))
    
    # Correct and intensity normalize the image. This step is suggested even
    # if a previous field correction was applied. It will coorect residual 
    # intensity inhomogeneities
    normalized_wm_fod = os.path.join(output_dir, 'preproc_wm_fod_%s.nii.gz' % subject_id)
    normalized_gm_fod = os.path.join(output_dir, 'preproc_gm_fod_%s.nii.gz' % subject_id)
    normalized_csf_fod = os.path.join(output_dir, 'preproc_csf_fod_%s.nii.gz' % subject_id)
    os.system('%s %s %s %s %s %s %s -mask %s' % (os.path.join(mrtrix_bin_path, 'mtnormalise'), wm_fod, normalized_wm_fod,
                                                 gm_fod, normalized_gm_fod, csf_fod, normalized_csf_fod, normalize_mask))
    
    
    
    
    