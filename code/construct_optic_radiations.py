import os

def construct_optic_radiations(hcp_struct_archive, bayesprf_inferred_volume_archive, segment_thalamic_segmentations_archive, FODtemplate, workdir, outputdir,
                               freesurfer_path='', ants_path='', fsl_path):
    
    # Create workdir and outputdir if it doesn't exist 
    if not os.path.exists(workdir):
        os.system('mkdir %s' % workdir)
    if not os.path.exists(outputdir):
        os.system('mkdir %s' % outputdir)
        
    # Get the subject id from hcp-struct zip archive
    subject_id = hcp_struct_archive[:-14]
    
    # Create a nested workdir with the subject id 
    subject_workdir = os.path.join(workdir, subject_id)
    
    # Extract the higres skull stripped T1 from the struct archive and convert it to nifti
    higres_mgz_extracted = os.path.join(subject_workdir, 'brain.hires.mgz')
    higres_nifti = os.path.join(subject_workdir, 'brain.hires.nii.gz')
    os.system('unzip -j %s %s/T1w/%s/mri/brain.hires.mgz -d %s' % hcp_struct_archive, subject_id, subject_id, higres_mgz_extracted)
    os.system('%s %s %s' % os.path.join(freesurfer_path, 'mri_convert'), higres_mgz_extracted, higres_nifti)
    
    # Extract the bayesprf varea and convert to nifti
    os.system('unzip %s -d %s' % (bayesprf_inferred_volume_archive, subject_workdir))
    varea_mgz = os.path.join(subject_workdir, 'inferred.varea.mgz')
    V1 = os.path.join(subject_workdir, 'V1.nii.gz')
    os.system('%s %s %s' % os.path.join(freesurfer_path, 'mri_extract_label'), varea_mgz, V1)
    
    # Extract LGN from thalamic nuclei and convert to nifti
    os.system('unzip %s -d %s' % (segment_thalamic_segmentations_archive, subject_workdir))
    thalamic_segmentations = os.path.join(subject_workdir, 'ThalamicNuclei.v12.T1.FSvoxelSpace.mgz')
    left_lgn = os.path.join(subject_workdir, 'left_lgn.nii.gz')
    right_lgn = os.path.join(subject_workdir, 'right_lgn.nii.gz')
    os.system('%s %s 8109 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), thalamic_segmentations, left_lgn))
    os.system('%s %s 8209 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), thalamic_segmentations, right_lgn))
    
    # Get the first volume of FOD image for registration
    single_frame_FOD = os.path.join(subject_workdir, 'single_frame_FOD.nii.gz')
    os.system('%s %s -nth 0 %s' % (os.path.join(freesurfer_path, 'mri_convert'), FODtemplate, single_frame_FOD))
    
    # Do an affine registration between highres image and FOD template 
    
    ants_run = '''antsRegistration --verbose 1 --dimensionality 3 --float 0 \
    --collapse-output-transforms 1 --output [ abece,abeceWarped.nii.gz,abeceInverseWarped.nii.gz ] \
    --interpolation Linear --use-histogram-matching 0 --winsorize-image-intensities [ 0.005,0.995 ] \
    --initial-moving-transform [ nu.mgz,left_LGN.nii.gz,1 ] --transform Rigid[ 0.1 ] --metric MI[ nu.mgz,left_LGN.nii.gz,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox --transform Affine[ 0.1 ] --metric MI[ nu.mgz,left_LGN.nii.gz,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox

    os.system('')
    