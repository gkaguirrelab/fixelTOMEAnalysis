import os

def roi_tractography(fod_temp, seed, roi, output_file, trekker_bin='', 
                     directionality='one_sided', timeLimit='10',minLength='5',
                     maxLength='400', minFODamp='0.2', seed_count='1000',
                     atMaxLength='discard', minRadiusOfCurvature='2', probeCount='1'):
    
    '''
    This function takes a fod image, seed and roi masks and uses trekker 
    (dmritrekker.github.io) to calculate tractography between these masks. 
    This wrapper was created to analyze TOME data. 
    '''
    
    command = '%s -fod %s -seed_image %s -pathway=require_entry %s -pathway=stop_at_exit %s -directionality %s -timeLimit %s -minLength %s -maxLength %s -minFODamp %s -seed_count %s -atMaxLength %s -minRadiusOfCurvature %s -probeCount %s -output %s'  % (os.path.join(trekker_bin, 'trekker'), fod_temp, seed, 
                                                                                                                                                                                                                                                              roi, roi, directionality, timeLimit, minLength,
                                                                                                                                                                                                                                                              maxLength, minFODamp, seed_count,
                                                                                                                                                                                                                                                              atMaxLength, minRadiusOfCurvature, probeCount, output_file)
   
    log_path = os.path.split(output_file)[0]
    os.system(command + ' > %s/trekker.log' % log_path)
      
