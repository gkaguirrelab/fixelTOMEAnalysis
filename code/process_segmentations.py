import os 

def process_segmentations(aparc_aseg, thalamic_segmentations, nu_mgz, fod_image, ants_path, afni_path, mrtrix_path, freesurfer_path, workdir, output_path):
    
    '''
    This functions extracts the optic chiasm, left and right LGN and moves them
    to the FOD space to be used with the TOME FOD images.
    
    Inputs:
        aparc_aseg= Freesurfer aparc+asge.mgz
        thalamic_segmentations = Freesurfer subthalamic segmentation labels
        nu_mgz = Freesurfer nu.mgz to be used for registrations 
        fod_image = fod image
        ants_path = Path to where ants bin is located. Enter empty string if you can
                    call the commands from terminal
        afni_path = Path to where afni bin is located. Enter empty string if you can
                    call the commands from terminal
        mrtrix_path = Path to mrtrix.
        freesurfer_path = Path to where FS bin is located. Enter empty string if you can
                    call the commands from terminal
        workdir = Temporary workdir where the intermediate files will be saved
        output_path = Final output path where the output will be saved
    '''
# Register nu.mgz to FOD image
    fod_image_name = os.path.split(fod_image)[1]
    fod_converted = os.path.join(output_path, fod_image_name.replace('mif.gz', 'nii.gz'))
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'mrconvert'), fod_image, fod_converted))

    nu_nifti = os.path.join(workdir, 'nu.nii.gz')
    nu_reoriented = os.path.join(workdir, 'oriented_nu.nii.gz')
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'), nu_mgz, nu_nifti))
    os.system('%s -orient rai -prefix %s -input %s' % (os.path.join(afni_path, '3dresample'), nu_reoriented, nu_nifti))

    registered_nu = os.path.join(workdir, 'nu2fodWarped.nii.gz')
    inversed_registered_nu = os.path.join(workdir, 'nu2fodInverseWarped.nii.gz')
    generic_affine = os.path.join(workdir, 'nu2fod0GenericAffine.mat')
    registration_command = 'cd %s; %s --verbose 1 --dimensionality 3 ' \
                           '--float 0 --collapse-output-transforms 1 ' \
                           '--output [ %s,%s,%s ] ' \
                           '--interpolation Linear --use-histogram-matching 0 --winsorize-image-intensities [ 0.005,0.995 ] ' \
                           '--initial-moving-transform [ %s,%s,1 ] '\
                           '--transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] ' \
                           '--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox' % (workdir, os.path.join(ants_path, 'antsRegistration'), 
                                                                                       'nu2fod', 'nu2fodWarped.nii.gz', 'nu2fodInverseWarped.nii.gz',
                                                                                       fod_converted, nu_reoriented, fod_converted, nu_reoriented)
    os.system(registration_command)

# Extract optic chiasm
    optic_chiasm_mgz = os.path.join(workdir, 'optic_chiasm.mgz')
    optic_chiasm_nifti = os.path.join(workdir, 'optic_chiasm.nii.gz')
    optic_chiasm_reoriented = os.path.join(workdir, 'reoriented_optic_chiasm.nii.gz')
    optic_chiasm_registered = os.path.join(output_path, 'registered_optic_chiasm.nii.gz')
    os.system('%s %s 85 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'),
                               aparc_aseg, optic_chiasm_mgz))
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'),
                            optic_chiasm_mgz, optic_chiasm_nifti))
    os.system('%s -orient rai -prefix %s -input %s' % (os.path.join(afni_path, '3dresample'),
                                                       optic_chiasm_reoriented, optic_chiasm_nifti))
    os.system('%s -d 3 -i %s -r %s -o %s -n NearestNeighbor -t %s -v' % (os.path.join(ants_path, 'antsApplyTransforms'),
                                                                         optic_chiasm_reoriented, fod_converted, optic_chiasm_registered,
                                                                         generic_affine))
    
# Extract left LGN
    left_lgn_mgz = os.path.join(workdir, 'left_lgn.mgz')
    left_lgn_nifti = os.path.join(workdir, 'left_lgn.nii.gz')
    left_lgn_reoriented = os.path.join(workdir, 'reoriented_left_lgn.nii.gz')
    left_lgn_registered = os.path.join(output_path, 'registered_left_lgn.nii.gz')
    os.system('%s %s 8109 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'),
                               thalamic_segmentations, left_lgn_mgz))
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'),
                            left_lgn_mgz, left_lgn_nifti))
    os.system('%s -orient rai -prefix %s -input %s' % (os.path.join(afni_path, '3dresample'),
                                                       left_lgn_reoriented, left_lgn_nifti))
    os.system('%s -d 3 -i %s -r %s -o %s -n NearestNeighbor -t %s -v' % (os.path.join(ants_path, 'antsApplyTransforms'),
                                                                         left_lgn_reoriented, fod_converted, left_lgn_registered,
                                                                         generic_affine))
    
# Extract right LGN
    right_lgn_mgz = os.path.join(workdir, 'right_lgn.mgz')
    right_lgn_nifti = os.path.join(workdir, 'right_lgn.nii.gz')
    right_lgn_reoriented = os.path.join(workdir, 'reoriented_right_lgn.nii.gz')
    right_lgn_registered = os.path.join(output_path, 'registered_right_lgn.nii.gz')
    os.system('%s %s 8209 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'),
                               thalamic_segmentations, right_lgn_mgz))
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'),
                            right_lgn_mgz, right_lgn_nifti))
    os.system('%s -orient rai -prefix %s -input %s' % (os.path.join(afni_path, '3dresample'),
                                                       right_lgn_reoriented, right_lgn_nifti))
    os.system('%s -d 3 -i %s -r %s -o %s -n NearestNeighbor -t %s -v' % (os.path.join(ants_path, 'antsApplyTransforms'),
                                                                         right_lgn_reoriented, fod_converted, right_lgn_registered,
                                                                         generic_affine))    
    
    return(fod_converted, registered_nu, optic_chiasm_registered, left_lgn_registered, right_lgn_registered)