import os, subprocess
import pandas as pd

def extract_fixel_values(input_dir, mrtrix_path, output_folder_path, left_track, right_track, track_density_thresh='1', smooth_fixels=False):
   
    '''
    input_dir: fixelAnalysis script 
    mrtrix_path: Path to mrtrix bin. If you can call mrtrix functions from the terminal, you can leave this empty ''
    output_folder_path: The output folder where the fixel files will be saved
    subject_fod_list: A python list that contains FOD images
    left_track: Left hemisphere track
    right_track: Right hemisphere track
    track_density_thresh: Select only those voxels that have the specified amount of fibres running through it
    smooth_fixels = Run fixel2fixel connectivity and smooth the voxels
    '''
    #### Process tractography ####
    # Set path to some input folders
    fixel_mask = os.path.join(input_dir, 'fixel_mask')
    
    # Convert vtk to tck
    tractography_folder = os.path.join(output_folder_path, 'tractography')
    os.system('mkdir %s' % tractography_folder)
    if not left_track == 'NA': 
        left_track_tck = os.path.join(tractography_folder, 'left_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), left_track, left_track_tck))
    if not left_track == 'NA':
        right_track_tck = os.path.join(tractography_folder, 'right_tract.tck')
        os.system('%s %s %s' % (os.path.join(mrtrix_path, 'tckconvert'), right_track, right_track_tck))
            
    # Combine the tracks if more than one exist 
    if not left_track == 'NA' and not right_track == 'NA':
        left_and_right_tck = os.path.join(tractography_folder, 'left_and_right_tracks.tck')
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'tckedit'), left_track_tck, right_track_tck, left_and_right_tck))
    elif not left_track == 'NA':
        left_and_right_tck = left_track
    elif not right_track == 'NA':
        left_and_right_tck = right_track
    else:
        raise RuntimeError('You need to specify at least one track to extract values from')
    
    # Calculate fixel2fixel measurements and smooth fixel data if requested
    if smooth_fixels == True:
        smoothed_fd_dir = os.path.join(input_dir, 'smooth_fd')
        smoothed_fc_dir = os.path.join(input_dir, 'smooth_fc')
        smoothed_log_fc_dir = os.path.join(input_dir, 'smooth_log_fc')
        smoothed_fdc_dir = os.path.join(input_dir, 'smooth_fdc')
        
        fixel_fixel_connectivity_dir = os.path.join(output_folder_path, 'fixel2fixelConn')
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelconnectivity'),
                                    fixel_mask, left_and_right_tck, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(input_dir, 'fd'),
                                                  smoothed_fd_dir, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(input_dir, 'fc'),
                                                  smoothed_fc_dir, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(input_dir, 'log_fc'),
                                                  smoothed_log_fc_dir, fixel_fixel_connectivity_dir))
        os.system('%s %s smooth %s -matrix %s' % (os.path.join(mrtrix_path, 'fixelfilter'), os.path.join(input_dir, 'fdc'),
                                                  smoothed_fdc_dir, fixel_fixel_connectivity_dir))        
        
    # Map tracks to the fixel template 
    fixel_folder_tracked = os.path.join(tractography_folder, 'fixel_folder_tracked')
    os.system('%s %s %s %s track_density.mif' % (os.path.join(mrtrix_path, 'tck2fixel'), left_and_right_tck,
                                              fixel_mask, fixel_folder_tracked))
    track_density_file = os.path.join(fixel_folder_tracked, 'track_density.mif')
    
    # Threshold track density
    track_density_thresholded = os.path.join(fixel_folder_tracked, 'thresh_track_density.mif')
    os.system('%s -abs %s %s %s' % (os.path.join(mrtrix_path, 'mrthreshold'), track_density_thresh, track_density_file, track_density_thresholded))

    # Create the output folder if it doesn't exist 
    if not os.path.exists(output_folder_path):
        os.system('mkdir %s' % output_folder_path)
    
    # Crop the fixels from subject FD, FC, and FDC 
    if smooth_fixels == False:     
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(input_dir, 'fd'), track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_fd')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(input_dir, 'fc'), track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_fc')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(input_dir, 'log_fc'), track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_log_fc')))    
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    os.path.join(input_dir, 'fdc'), track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_fdc')))
    elif smooth_fixels == True:
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_fd_dir, track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_fd')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_fc_dir, track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_fc')))
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_log_fc_dir, track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_log_fc')))    
        os.system('%s %s %s %s' % (os.path.join(mrtrix_path, 'fixelcrop'), 
                                    smoothed_fdc_dir, track_density_thresholded, 
                                    os.path.join(output_folder_path, 'cropped_fdc')))
    else:
        raise RuntimeError('smooth_fixels option was set to something other than False or True')
         
    # Extract FD, FC, log_FC and FDC stats from images and write them to a text file and create a pandas object for cvs save
    types = ['fd', 'fc', 'fdc', 'log_fc']
    for ty in types:
        pandasSubject = []
        pandasMean = []
        pandasMedian = []
        pandasStd = []
        pandasMax = []
        pandasMin = []
        fullPandasDict = {}
        for i in os.listdir(os.path.join(output_folder_path, 'cropped_%s' % ty)):
            if not i == 'index.mif' and not i =='directions.mif':
                # Get image name and path
                imname = i[:-4]
                pandasSubject.append(imname)
                impath = os.path.join(output_folder_path, 'cropped_%s' % ty, imname + '.mif')
                # Add mean
                mean_byte = subprocess.check_output("%s -output mean %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                mean_str = mean_byte.decode('utf-8')
                pandasMean.append(float(mean_str))
                # Add median
                median_byte = subprocess.check_output("%s -output median %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                median_str = median_byte.decode('utf-8')
                pandasMedian.append(float(median_str))          
                # Add std
                std_byte = subprocess.check_output("%s -output std %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                std_str = std_byte.decode('utf-8')
                pandasStd.append(float(std_str))                                         
                # Add min
                min_byte = subprocess.check_output("%s -output min %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                min_str = min_byte.decode('utf-8')
                pandasMin.append(float(min_str))                
                # Add max
                max_byte = subprocess.check_output("%s -output max %s" % (os.path.join(mrtrix_path, 'mrstats'), impath), shell=True)
                max_str = max_byte.decode('utf-8')
                pandasMax.append(float(max_str))    
        fullPandasDict['subject'] = pandasSubject
        fullPandasDict['mean'] = pandasMean
        fullPandasDict['median'] = pandasMedian
        fullPandasDict['std'] = pandasStd
        fullPandasDict['max'] = pandasMax
        fullPandasDict['min'] = pandasMin  
        dataFrame = pd.DataFrame(fullPandasDict)
        dataFrame.set_index('subject', inplace=True)
        dataFrame.to_csv(os.path.join(output_folder_path, '%s_stats.csv' % ty))
