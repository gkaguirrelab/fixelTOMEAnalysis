import os
from fury import window, actor
from dipy.io.streamline import load_tractogram

def roi_tractography(fod_temp, seed, roi, output_file, output_diagnostic_image, trekker_bin='', fod_amplitude=0.2, register=False, roi_structure=''):
    
    '''
    This function takes a fod image, seed and roi masks and uses trekker 
    (dmritrekker.github.io) to calculate tractography between these masks. 
    This wrapper was created to analyze TOME data. 
    '''
    
    command = '''%s -fod %s -seed_image %s -seed_count 1000 \
                 -pathway=require_entry %s -pathway=stop_at_exit %s \
                 -directionality one_sided -timeLimit 10 -minLength 5 \
                 -maxLength 400 -minFODamp %s -atMaxLength discard \
                 -minRadiusOfCurvature 2 -probeCount 1 -output %s
              ''' % (os.path.join(trekker_bin, 'trekker'), fod_temp, seed, 
                     roi, roi, fod_amplitude, output_file)
    
    os.system(command)
      
    print('Making plots')
    
    # Load fibre 
    fibre_data = load_tractogram(output_file, fod_temp)
    lines = fibre_data.streamlines

    # Set actor
    stream_actor = actor.line(lines)

    # Initiate renderer and scene
    renderer = window.Scene()
    renderer.add(stream_actor)
    renderer.set_camera(position=(-176.42, 118.52, 128.20),
                        focal_point=(113.30, 128.31, 76.56),
                        view_up=(0.18, 0.00, 0.98))
    
    # Display 
    window.record(renderer, out_path=output_diagnostic_image, size=(600, 600))
