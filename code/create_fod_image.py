import os 

def create_fod_image(preprocessed_dti, mask, bvecs, bvals, response_wm, response_gm, response_csf, lmax, mrtrix_bin_path, subject_id, workdir, output_dir):

    # Create the workdir and output_dir if they don't exist    
    if not os.path.exists(workdir):
        os.system('mkdir %s' % workdir)
    if not os.path.exists(output_dir):
        os.system('mkdir %s' % output_dir)
    
    # Convert Pre-processed DTI to mif forma
    preprocessed_dti_mif = os.path.join(workdir, os.path.split(preprocessed_dti)[1].replace('.nii.gz', '.mif'))
    os.system('%s %s %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), preprocessed_dti, preprocessed_dti_mif))
    
    # Calculate 3-tissue functions for individual subjects
    if response_wm == '':
        print('Calculating 3-tissue response function')
        response_wm = os.path.join(workdir, 'response_wm.txt')
        response_gm = os.path.join(workdir, 'response_gm.txt')    
        response_csf = os.path.join(workdir, 'response_csf.txt')    
        os.system('%s dhollander %s -fslgrad %s %s %s %s %s -scratch %s' % (os.path.join(mrtrix_bin_path, 'dwi2response'),
                                                                                preprocessed_dti_mif, bvecs, bvals, 
                                                                                response_wm, response_gm, response_csf, workdir))
    
    # Upsample DWI images and the mask to isotropic 1.25mm
    print('Upsampling DWI')
    upsampled_dti = os.path.join(workdir, 'upsampled_%s_dti.mif' % subject_id)
    upsampled_mask = os.path.join(workdir, 'upsampled_%s_mask.mif' % subject_id)
    os.system('%s %s regrid -vox 1.25 %s' % (os.path.join(mrtrix_bin_path, 'mrgrid'),
                                                    preprocessed_dti_mif, upsampled_dti))
    os.system('%s %s regrid -vox 1.25 %s' % (os.path.join(mrtrix_bin_path, 'mrgrid'),
                                                    mask, upsampled_mask))
    
    # Create the FOD image
    print('Making a FOD image')
    wm_fod = os.path.join(workdir, 'wm_fod.mif')
    gm_fod = os.path.join(workdir, 'gm_fod.mif')
    csf_fod = os.path.join(workdir, 'csf_fod.mif')
    os.system('%s msmt_csd %s %s %s %s %s %s %s -mask %s -lmax %s -fslgrad %s %s' % (os.path.join(mrtrix_bin_path, 'dwi2fod'), upsampled_dti,
                                                                                     response_wm, wm_fod, response_gm, gm_fod, response_csf, csf_fod,
                                                                                     upsampled_mask, lmax, bvecs, bvals))
    
    # Calculate a more conservetive mask from the upsampled data for the next
    # step (bias coorection and intensity normalization)
    normalize_mask = os.path.join(workdir, 'normalize_mask.mif')
    os.system('%s %s %s -fslgrad %s %s' % (os.path.join(mrtrix_bin_path, 'dwi2mask'), upsampled_dti, normalize_mask, bvecs, bvals))
    
    # Correct and intensity normalize the image. This step is suggested even
    # if a previous field correction was applied. It will coorect residual 
    # intensity inhomogeneities
    print('Correcting FOD intensity')
    normalized_wm_fod = os.path.join(output_dir, 'preproc_wm_fod_%s.mif' % subject_id)
    normalized_gm_fod = os.path.join(output_dir, 'preproc_gm_fod_%s.mif' % subject_id)
    normalized_csf_fod = os.path.join(output_dir, 'preproc_csf_fod_%s.mif' % subject_id)
    os.system('%s %s %s %s %s %s %s -mask %s' % (os.path.join(mrtrix_bin_path, 'mtnormalise'), wm_fod, normalized_wm_fod,
                                                 gm_fod, normalized_gm_fod, csf_fod, normalized_csf_fod, normalize_mask))
    
    # Save nifti versions of the images
    normalized_wm_fod_nifti = os.path.join(output_dir, 'preproc_wm_fod_%s.nii.gz' % subject_id)
    normalized_gm_fod_nifti = os.path.join(output_dir, 'preproc_gm_fod_%s.nii.gz' % subject_id)
    normalized_csf_fod_nifti = os.path.join(output_dir, 'preproc_csf_fod_%s.nii.gz' % subject_id)
    os.system('%s %s %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), normalized_wm_fod, normalized_wm_fod_nifti))
    os.system('%s %s %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), normalized_gm_fod, normalized_gm_fod_nifti))
    os.system('%s %s %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), normalized_csf_fod, normalized_csf_fod_nifti))
    
    # Output the upsampled mask in mif and nifti formats
    mask_new_path = os.path.join(output_dir, 'upsampled_%s_mask.nii.gz' % subject_id)    
    os.system('cp %s %s' % (upsampled_mask, output_dir))
    os.system('%s %s %s' % (os.path.join(mrtrix_bin_path, 'mrconvert'), upsampled_mask, mask_new_path))
