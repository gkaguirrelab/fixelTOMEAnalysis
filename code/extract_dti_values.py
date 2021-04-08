import os, imageio
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt

def extract_dti_values(metric_images, workdir, output_folder_path, left_track, right_track, tckmap_template, n_threads='2', warpfolder='', mrtrix_path='', freesurfer_path='', ants_path='', fslpath='', track_density_thresh='1'):

    '''
    metric_image: input image list. all images need to be the same type (FA,MD,etc.)
    DTI measures. Pass other metric images to other_metrics flag as a python list to move the tracks to 
    them.
    workdir: Wordir folder where intermediate files will be saved
    output_folder_path: The output folder where the fixel files will be saved
    left_track: Left hemisphere track
    right_track: Right hemisphere track
    tckmap_template = Template in which the tracts were calculated
    warpfolder = Pass a warpfolder outputted by this gear to skip the subject warps 
    mrtrix_warp = warp tracks to another coordinates using a mrtrix warp file
    mrtrix_path: Path to mrtrix bin. If you can call mrtrix functions from the terminal, you can leave this empty ''
    freesurfer_path: path to freesurfer bin 
    track_density_thresh: Select only those voxels that have the specified amount of fibres running through it
    '''

    # Set some functions
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
            
        figure_save_path = os.path.join(output_folder, subject_id + '_' + filename)     
        plt.savefig(figure_save_path)    
    
        return figure_save_path 
    
    def make_gif(image_folder, gif_name, output_folder):
        
        # Make a gif out of multiple images
        images = []
        for filename in os.listdir(image_folder):
            images.append(imageio.imread(os.path.join(image_folder, filename)))
            imageio.mimsave('/%s/%s.gif' % (output_folder, gif_name), images, duration=0.7)

    ### Process tractography ####    
    # Convert vtk to tck
    tractography_folder = os.path.join(workdir, 'tractography')
    os.system('mkdir %s' % tractography_folder)
    if not left_track == 'NA': 
        left_track_tck = os.path.join(tractography_folder, 'left_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, left_track_tck))
    if not right_track == 'NA':
        right_track_tck = os.path.join(tractography_folder, 'right_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, right_track_tck))
            
    # Combine the tracks if more than one exist 
    if not left_track == 'NA' and not right_track == 'NA':
        left_and_right_tck = os.path.join(tractography_folder, 'left_and_right_tracks.tck')
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'tckedit'), left_track_tck, right_track_tck, left_and_right_tck))
    elif not left_track == 'NA':
        left_and_right_tck = left_track_tck
    elif not right_track == 'NA':
        left_and_right_tck = right_track_tck
    else:
        raise RuntimeError('You need to specify at least one track to extract values from')
    
    # Calculate track density map    
    track_density_map = os.path.join(tractography_folder, 'track_density_map.nii.gz')
    os.system('%s %s %s -template %s' % (os.path.join(mrtrix_path, 'tckmap'), left_and_right_tck, 
                                          track_density_map, tckmap_template))
    
    # Threshold the track density map
    thresholded_track = os.path.join(tractography_folder, 'thresholded.nii.gz')
    os.system('%s %s -abs %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_map, 
                                    track_density_thresh, thresholded_track))
    
    # Initiate pandas object
    pandasSubject = []
    pandasMean = []
    pandasMedian = []
    pandasStd = []
    pandasMax = []
    pandasMin = []
    fullPandasDict = {}

    # Make warp dir 
    warp_workdir = os.path.join(workdir, 'warp_workdir')
    os.system('mkdir %s' % warp_workdir)

    # Extract the template image for the warp 
    extracted_template = os.path.join(workdir, 'extracted_template.nii.gz')
    os.system('%s %s %s 0 1' % (os.path.join(fslpath,'fslroi'), tckmap_template, extracted_template))
    
    # Create an image folder 
    image_folder = os.path.join(workdir, 'images')
    os.system('mkdir %s' % image_folder)
    main_gif_folder = os.path.join(workdir, 'main_gif_folder')
    os.system('mkdir %s' % main_gif_folder)  
    gif_folder = os.path.join(main_gif_folder, 'gifs')
    os.system('mkdir %s' % gif_folder)
    
    # Set metric name
    metric_name = os.path.split(metric_images[0])[1][-9:-7]
    
    # Initiate the html file 
    html_file = open('%s/index.html' % main_gif_folder,'w')
    html_content = ''
    
    for subj in metric_images:

        # Get subject name and metric name
        subject_id = os.path.split(subj)[1][:-10]
        pandasSubject.append(subject_id)
        
        # Warp the image which the track was based on and warp it to the target   
        if warpfolder == '':
            output_name = os.path.join(warp_workdir, 'tckmap2%s' % subject_id)
            output_warped = os.path.join(warp_workdir, 'tckmap2%sWarped.nii.gz' % subject_id)
            output_inverse_warped = os.path.join(warp_workdir, 'tckmap2%sInverseWarped.nii.gz' % subject_id)   
            output_inverse_warp = os.path.join(warp_workdir, 'tckmap2%s1InverseWarp.nii.gz' % subject_id)   
            output_warp = os.path.join(warp_workdir, 'tckmap2%s1Warp.nii.gz' % subject_id)
            output_affine = os.path.join(warp_workdir, 'tckmap2%s0GenericAffine.mat' % subject_id)
        else:
            output_warped = os.path.join(warpfolder, 'tckmap2%sWarped.nii.gz' % subject_id)
            output_inverse_warped = os.path.join(warpfolder, 'tckmap2%sInverseWarped.nii.gz' % subject_id)   
            output_inverse_warp = os.path.join(warpfolder, 'tckmap2%s1InverseWarp.nii.gz' % subject_id)   
            output_warp = os.path.join(warpfolder, 'tckmap2%s1Warp.nii.gz' % subject_id)
            output_affine = os.path.join(warpfolder, 'tckmap2%s0GenericAffine.mat' % subject_id)            
            
        if warpfolder == '':
            command = 'ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s; %s --verbose 1 --dimensionality 3 --float 0 --collapse-output-transforms 1 \
--output [ %s,%s,%s ] --interpolation Linear --use-histogram-matching 0 \
--winsorize-image-intensities [ 0.005,0.995 ] --initial-moving-transform [ %s,%s,1 ] \
--transform Rigid[ 0.1 ] --metric MI[ %s,%s,1,32,Regular,0.25 ] \
--convergence [ 1000x500x250x100,1e-6,10 ] --shrink-factors 8x4x2x1 \
--smoothing-sigmas 3x2x1x0vox --transform Affine[ 0.1 ] \
--metric MI[ %s,%s,1,32,Regular,0.25 ] --convergence [ 1000x500x250x100,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox --transform SyN[ 0.1,3,0 ] \
--metric CC[ %s,%s,1,4 ] --convergence [ 100x70x50x20,1e-6,10 ] \
--shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox' % (n_threads, os.path.join(ants_path, 'antsRegistration'),
                                                            output_name, output_warped, 
                                                            output_inverse_warped, subj, 
                                                            extracted_template, subj, 
                                                            extracted_template, subj, 
                                                            extracted_template, subj,
                                                            extracted_template)
        
            os.system(command)

        # Make template image
        input_img = nib.load(subj)
        input_img_data = input_img.get_fdata()
        x = int(len(input_img_data[:,1,1])/2)
        y = int(len(input_img_data[1,:,1])/2)
        z = int(len(input_img_data[1,1,:])/2)
        
        subject_image_folder = os.path.join(image_folder, subject_id)
        os.system('mkdir %s' % subject_image_folder)
        make_plot('template', output_warped, 'NA', 'Template warped to %s' % subject_id, 'warped_template_%s.png' % subject_id, x, y, z, [1, 1, 1, 1, 1, 1], subject_image_folder)
        make_plot('template', subj, 'NA', 'Template warped to %s' % subject_id, 'subject_image_%s.png' % subject_id, x, y, z, [1, 1, 1, 1, 1, 1], subject_image_folder)
        
        make_gif(subject_image_folder, subject_id, gif_folder)
        html_content = html_content + '<h1>Surface</h1>\n<img src="./gifs/%s" style="float: left; width: 30%%; margin-right: 1%%; margin-bottom: 0.5em;" alt="%s">\n<p style="clear: both;">\n' % (subject_id + '.gif', subject_id)
               
        # Move the track to the target dti space
        binary_track_mask_warped = os.path.join(warp_workdir, 'binary_mask_warped.nii.gz')
        os.system('%s -d 3 -i %s -r %s -o %s -n NearestNeighbor -t [ %s, 1 ] -t %s' % (os.path.join(ants_path, 'antsApplyTransforms'),
                                                                                        thresholded_track, subj, binary_track_mask_warped,
                                                                                        output_affine, output_inverse_warped))
        
        # Extract the tracks from the metric
        extracted_metric_image = os.path.join(warp_workdir, '%s_%s_extracted.nii.gz' % (subject_id, metric_name))
        os.system('%s %s -mas %s %s' % (os.path.join(fslpath, 'fslmaths'),
                                        subj, binary_track_mask_warped, extracted_metric_image))
        
        # Get the mean, median, std, max, min
        mean_raw = os.popen('%s %s -M' % (os.path.join(fslpath, 'fslstats'), extracted_metric_image)).read()
        mean = float(mean_raw)
        pandasMean.append(mean)
        
        median_raw = os.popen('%s %s -P 50' % (os.path.join(fslpath, 'fslstats'), extracted_metric_image)).read()
        median = float(median_raw)        
        pandasMedian.append(median)
        
        std_raw = os.popen('%s %s -S' % (os.path.join(fslpath, 'fslstats'), extracted_metric_image)).read()
        std = float(std_raw)
        pandasStd.append(std)
        
        min_max_raw = os.popen('%s %s -R' % (os.path.join(fslpath, 'fslstats'), extracted_metric_image)).read()
        min_max_list = min_max_raw.split()
        minimum = float(min_max_list[0])
        maximum = float(min_max_list[1])
        pandasMax.append(maximum)
        pandasMin.append(minimum)
    
    # Create the csv file
    fullPandasDict['subject'] = pandasSubject
    fullPandasDict['mean'] = pandasMean
    fullPandasDict['median'] = pandasMedian
    fullPandasDict['std'] = pandasStd
    fullPandasDict['max'] = pandasMax
    fullPandasDict['min'] = pandasMin  
    dataFrame = pd.DataFrame(fullPandasDict)
    dataFrame.set_index('subject', inplace=True)
    dataFrame.to_csv(os.path.join(output_folder_path, '%s_stats.csv' % metric_name))   
    
    # Create the html file and close
    html_file.write(html_content)
    html_file.close()    
    os.system('cd %s; zip -r %s *' % (main_gif_folder, os.path.join(output_folder_path, 'warp_results.html.zip')))

    return warp_workdir    
