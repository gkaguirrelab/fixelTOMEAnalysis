import os, imageio
import nibabel as nib
import matplotlib.pyplot as plt

def construct_optic_radiations(hcp_struct_archive, freesurfer_archive, bayesprf_inferred_volume_archive, segment_thalamic_segmentations_archive, 
                               subjectFOD, FODtemplate, calculateFixelsIntermediate, workdir, outputdir, minFODamp='0.2', track_density_thresh='1', numTracks='10000', freesurfer_path='', 
                               ants_path='', fsl_path='', mrtrix_path='', trekker_path=''):

    def make_plot(subject_id, base_image, overlay, title, filename, x, y, z, apect_ratio_vector, output_folder):
        
        # This function simply gets two MRI images as inputs and overlays them 
        # using different colors for each image. Used as a diagnostic image.
            
        fig, (ax1, ax2, ax3) = plt.subplots(1,3)
        fig.suptitle(title, fontsize=20)
    
        epi_img = nib.load(base_image)
        epi_img_data = epi_img.get_fdata()
        ax1.imshow(epi_img_data[x,:,:], cmap="gray", aspect = apect_ratio_vector[0])
        ax2.imshow(epi_img_data[:,y,:], cmap="gray", aspect = apect_ratio_vector[1])
        ax3.imshow(epi_img_data[:,:,z], cmap="gray", aspect = apect_ratio_vector[2])
        ax1.axis('off')
        ax2.axis('off')
        ax3.axis('off')  
        
        if overlay != 'NA':
            epi_img = nib.load(overlay)
            epi_img_data = epi_img.get_fdata()
            ax1.imshow(epi_img_data[x,:,:], cmap="hot", alpha=0.4, aspect = apect_ratio_vector[3])
            ax2.imshow(epi_img_data[:,y,:], cmap="hot", alpha=0.4, aspect = apect_ratio_vector[4])
            ax3.imshow(epi_img_data[:,:,z], cmap="hot", alpha=0.4, aspect = apect_ratio_vector[5])
            ax1.axis('off')
            ax2.axis('off')
            ax3.axis('off')
    
        plt.savefig(os.path.join(output_folder, subject_id + '_' + filename))    
    
    def make_gif(image_folder, gif_name, output_folder):
        
        # Make a gif out of multiple images
        images = []
        for filename in os.listdir(image_folder):
            images.append(imageio.imread(os.path.join(image_folder, filename)))
            imageio.mimsave('/%s/%s.gif' % (output_folder, gif_name), images, duration=0.7)
    
    # Create workdir and outputdir if it doesn't exist 
    if not os.path.exists(workdir):
        os.system('mkdir %s' % workdir)
    if not os.path.exists(outputdir):
        os.system('mkdir %s' % outputdir)
        
    # Get the subject id from hcp-struct zip archive
    subject_id = os.path.split(hcp_struct_archive)[1][:-14]
    
    # Create a nested workdir with the subject id 
    subject_workdir = os.path.join(workdir, subject_id)
    os.system('mkdir %s' % subject_workdir)
    
    # Extract the higres skull stripped T1 from the struct archive and convert it to nifti
    higres_mgz_extracted = os.path.join(subject_workdir, 'brain.hires.mgz')
    higres_nifti = os.path.join(subject_workdir, 'brain.hires.nii.gz')
    os.system('unzip -q -j %s %s/T1w/%s/mri/brain.hires.mgz -d %s' % (hcp_struct_archive, subject_id, subject_id, subject_workdir))
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'), higres_mgz_extracted, higres_nifti))
    
    # Extract the bayesprf varea and convert to nifti
    os.system('unzip -q %s -d %s' % (bayesprf_inferred_volume_archive, subject_workdir))
    varea_mgz = os.path.join(subject_workdir, 'inferred_varea.mgz')
    V1 = os.path.join(subject_workdir, 'V1.nii.gz')
    os.system('%s %s 1 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), varea_mgz, V1))
    
    # Extract LGN from thalamic nuclei and convert to nifti
    os.system('unzip -q %s -d %s' % (segment_thalamic_segmentations_archive, subject_workdir))
    thalamic_segmentations = os.path.join(subject_workdir, 'ThalamicNuclei.v12.T1.FSvoxelSpace.mgz')
    left_lgn = os.path.join(subject_workdir, 'left_lgn.nii.gz')
    right_lgn = os.path.join(subject_workdir, 'right_lgn.nii.gz')
    os.system('%s %s 8109 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), thalamic_segmentations, left_lgn))
    os.system('%s %s 8209 %s' % (os.path.join(freesurfer_path, 'mri_extract_label'), thalamic_segmentations, right_lgn))
    
    # Get the first volume of FOD image for registration
    single_frame_FOD = os.path.join(subject_workdir, 'single_frame_FOD.nii.gz')   
    single_frame_FOD_template = os.path.join(subject_workdir, 'single_frame_FOD_template.nii.gz')   
    os.system('%s %s %s 0 1' % (os.path.join(fsl_path, 'fslroi'), subjectFOD, single_frame_FOD))
    os.system('%s %s %s 0 1' % (os.path.join(fsl_path, 'fslroi'), FODtemplate, single_frame_FOD_template))
    
    # Do an affine registration between highres image and FOD template 
    output_name = os.path.join(subject_workdir, 'highres2fod')
    output_warped = os.path.join(subject_workdir, 'highres2fod1Warped.nii.gz')
    generic_affine = os.path.join(subject_workdir, 'highres2fod0GenericAffine.mat')
    output_inverse_warped = os.path.join(subject_workdir, 'highres2fod1InverseWarped.nii.gz')
    
    ants_run = '%s --verbose 1 --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 --winsorize-image-intensities [ 0.005,0.995 ] \
--initial-moving-transform [ %s,%s,1 ] --transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox \
--transform Affine[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox' % (os.path.join(ants_path, 'antsRegistration'), 
                                                            output_name, output_warped, 
                                                            output_inverse_warped,
                                                            single_frame_FOD, higres_nifti, 
                                                            single_frame_FOD, higres_nifti,
                                                            single_frame_FOD, higres_nifti)
    os.system(ants_run)
    
    # Move V1 to subject FOD space
    warped_v1 = os.path.join(subject_workdir, 'warped_V1.nii.gz')
    os.system('%s -d 3 -i %s -r %s -n NearestNeighbor -t %s -o %s' % (os.path.join(ants_path, 'antsApplyTransforms'), V1, single_frame_FOD, generic_affine, warped_v1))
    
    # LGN was constructed with a different version of recon-all. So we do a rigid registration between the standalone freesurfer 
    # brain.mgz file and HCP-struct freesurfer higres run and then apply the warp we calculated above to move the segmentations to 
    # the FOD coordinate space.
    freesurfer_orig_mgz_extracted = os.path.join(subject_workdir, 'brain.mgz')
    freesurfer_orig_nifti = os.path.join(subject_workdir, 'brain.nii.gz')
    os.system('unzip -q -j %s %s/mri/brain.mgz -d %s' % (freesurfer_archive, subject_id, subject_workdir))
   
    
    freesurfer_output_name = os.path.join(subject_workdir, 'brain2hires')
    freesurfer_output_warped = os.path.join(subject_workdir, 'brain2hires1Warped.nii.gz')
    freesurfer_generic_affine = os.path.join(subject_workdir, 'brain2hires0GenericAffine.mat')
    freesurfer_output_inverse_warped = os.path.join(subject_workdir, 'brain2hires1InverseWarped.nii.gz')   
    os.system('%s %s %s' % (os.path.join(freesurfer_path, 'mri_convert'), freesurfer_orig_mgz_extracted, freesurfer_orig_nifti))
    ants_run = '%s --verbose 1 --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 --winsorize-image-intensities [ 0.005,0.995 ] \
--initial-moving-transform [ %s,%s,1 ] --transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox ' % (os.path.join(ants_path, 'antsRegistration'), 
                                                                                                        freesurfer_output_name, freesurfer_output_warped, 
                                                                                                        freesurfer_output_inverse_warped,
                                                                                                        higres_nifti, freesurfer_orig_nifti, 
                                                                                                        higres_nifti, freesurfer_orig_nifti)
    os.system(ants_run)
    
    # Apply warps
    warped_lgn_left = os.path.join(subject_workdir, 'warped_left_lgn.nii.gz')
    warped_lgn_right = os.path.join(subject_workdir, 'warped_right_lgn.nii.gz') 
    os.system('%s -d 3 -i %s -r %s -n NearestNeighbor -t %s -t %s -o %s' % (os.path.join(ants_path, 'antsApplyTransforms'), left_lgn, single_frame_FOD, generic_affine, freesurfer_generic_affine, warped_lgn_left))
    os.system('%s -d 3 -i %s -r %s -n NearestNeighbor -t %s -t %s -o %s' % (os.path.join(ants_path, 'antsApplyTransforms'), right_lgn, single_frame_FOD, generic_affine, freesurfer_generic_affine, warped_lgn_right))
    
    # Do tractography
    left_track = os.path.join(subject_workdir, 'left_optic_radiation.vtk')
    right_track = os.path.join(subject_workdir, 'right_optic_radiation.vtk')
    os.system('%s -fod %s -seed_image %s -seed_count %s -pathway=require_entry %s -pathway=stop_at_exit %s -minFODamp %s -output %s -maxLength 100 -atMaxLength discard -directionality one_sided > %s/trekker_left.log' % (os.path.join(trekker_path, 'trekker'),
                                                                                                                                                                                                                                subjectFOD, warped_lgn_left,
                                                                                                                                                                                                                                numTracks, warped_v1, warped_v1, minFODamp, 
                                                                                                                                                                                                                                left_track, outputdir))
    os.system('%s -fod %s -seed_image %s -seed_count %s -pathway=require_entry %s -pathway=stop_at_exit %s -minFODamp %s -output %s -maxLength 100 -atMaxLength discard -directionality one_sided > %s/trekker_right.log' % (os.path.join(trekker_path, 'trekker'),
                                                                                                                                                                                                                                subjectFOD, warped_lgn_right,
                                                                                                                                                                                                                                numTracks, warped_v1, warped_v1, minFODamp, 
                                                                                                                                                                                                                                right_track, outputdir))
    # Convert tracks to tck 
    tck_left = os.path.join(outputdir, '%s_native_left_optic_radiation.tck' % subject_id)
    tck_right = os.path.join(outputdir, '%s_native_right_optic_radiation.tck' % subject_id)
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, tck_left))
    os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, tck_right))    
    
    # Make volumetric density masks
    tck_left_density = os.path.join(outputdir, '%s_native_left_optic_radiation_density.nii.gz' % subject_id)
    tck_right_density = os.path.join(outputdir, '%s_native_right_optic_radiation_density.nii.gz' % subject_id)
    os.system('%s %s -template %s %s' % (os.path.join(mrtrix_path, 'tckmap'), tck_left, single_frame_FOD, tck_left_density))
    os.system('%s %s -template %s %s' % (os.path.join(mrtrix_path, 'tckmap'), tck_right, single_frame_FOD, tck_right_density))
    
    # Threshold density maps 
    thresholded_density_left = os.path.join(outputdir, '%s_native_left_optic_radiation_density_thresholded.nii.gz' % subject_id)
    thresholded_density_right = os.path.join(outputdir, '%s_native_right_optic_radiation_density_thresholded.nii.gz' % subject_id)    
    os.system('%s -abs %s %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_thresh, tck_left_density, thresholded_density_left))
    os.system('%s -abs %s %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_thresh, tck_right_density, thresholded_density_right))

    # Extract the warp file from the intermediate fixel archive
    os.system('unzip -q -j %s subjects/preproc_wm_fod_%s/warp_calculations/subject2template_warp.mif -d %s' % (calculateFixelsIntermediate, subject_id, subject_workdir))
    fod_warp = os.path.join(subject_workdir, 'subject2template_warp.mif')
    
    # Warp the tracks to FOD template space 
    track_mask_in_template_left = os.path.join(outputdir, '%s_mask_left_in_FOD_template.nii.gz' % subject_id)
    track_mask_in_template_right = os.path.join(outputdir, '%s_mask_right_in_FOD_template.nii.gz' % subject_id)
    combined_template_track_volumes = os.path.join(outputdir, '%s_mask_combined_in_FOD_template.nii.gz' % subject_id)
    os.system('%s -warp %s -interp nearest -datatype bit -template %s %s %s' % (os.path.join(mrtrix_path, 'mrtransform'),
                                                                                fod_warp, single_frame_FOD_template,
                                                                                thresholded_density_left, track_mask_in_template_left))    
    os.system('%s -warp %s -interp nearest -datatype bit -template %s %s %s' % (os.path.join(mrtrix_path, 'mrtransform'),
                                                                                fod_warp, single_frame_FOD_template,
                                                                                thresholded_density_right, track_mask_in_template_right))
    os.system('%s %s -add %s %s' % (os.path.join(fsl_path, 'fslmaths'), track_mask_in_template_left, track_mask_in_template_right, combined_template_track_volumes))
    
    # Plot tracks
    combined_native_tracks = os.path.join(outputdir, 'native_combined_optic_radiation.tck')
    os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'tckedit'), tck_left, tck_right, combined_native_tracks))
    os.system('Xvfb :1 -screen 0 1024x768x16 & DISPLAY=:1 %s %s -noannotations -tractography.load %s -mode 3 -tractography.slab 0 -imagevisible 0 -capture.folder %s -capture.prefix %s -capture.grab -exit' % (os.path.join(mrtrix_path, 'mrview'),
                                                                                                                                                                                                                subjectFOD, combined_native_tracks,
                                                                                                                                                                                                                outputdir, 'track'))
    os.system('Xvfb :99 -screen 0 1024x768x16 & DISPLAY=:99 %s %s -noannotations -tractography.load %s -mode 2 -tractography.slab 0 -capture.folder %s -capture.prefix %s -capture.grab -exit' % (os.path.join(mrtrix_path, 'mrview'),
                                                                                                                                                                                                  subjectFOD, combined_native_tracks,
                                                                                                                                                                                                  outputdir, 'track_on_fod_noSlab'))
    # Plot registration quality fs to hires
    image_workdir = os.path.join(subject_workdir, 'images')
    os.system('mkdir %s' % image_workdir)
    freesurfer_to_hires = os.path.join(image_workdir, 'freesurfer_to_hires')
    os.system('mkdir %s' % freesurfer_to_hires)
    coordinate_image = nib.load(higres_nifti)
    x = coordinate_image.shape[0]//2
    y = coordinate_image.shape[1]//2    
    z = coordinate_image.shape[2]//2
    make_plot(subject_id, higres_nifti, 'NA', 'fs_to_hires', 'hi.png', x, y, z, [1,1,1,1,1,1,1], freesurfer_to_hires)
    make_plot(subject_id, freesurfer_output_warped, 'NA', 'fs_to_hires', 'fs.png', x, y, z, [1,1,1,1,1,1,1], freesurfer_to_hires)
    make_gif(freesurfer_to_hires, 'fs_to_hires_qa', outputdir)
            
    # Plot registration quality fs to hires
    hires_to_fod = os.path.join(image_workdir, 'hires_to_fod')
    os.system('mkdir %s' % hires_to_fod)
    coordinate_image = nib.load(single_frame_FOD)
    x = coordinate_image.shape[0]//2
    y = coordinate_image.shape[1]//2    
    z = coordinate_image.shape[2]//2
    make_plot(subject_id, output_warped, 'NA', 'hires_to_fod', 'hi.png', x, y, z, [1,1,1,1,1,1,1], hires_to_fod)
    make_plot(subject_id, single_frame_FOD, 'NA', 'hires_to_fod', 'fs.png', x, y, z, [1,1,1,1,1,1,1], hires_to_fod)
    make_gif(hires_to_fod, 'hires_to_fod', outputdir)
    
    # Mask in template space
    os.system('Xvfb :55 -screen 0 1024x768x16 & DISPLAY=:55 %s %s -noannotations -overlay.load %s -mode 4 -capture.folder %s -capture.prefix %s -capture.grab -exit' % (os.path.join(mrtrix_path, 'mrview'),
                                                                                                                                                                        single_frame_FOD, combined_template_track_volumes,
                                                                                                                                                                        outputdir, 'volume_mask_in_FOD_template'))