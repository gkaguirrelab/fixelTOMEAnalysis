import flywheel
import datetime
import pandas as pd
import tqdm as tqdm

''''This script can be used to submit FOD template gear for the TOME
subjects. 
Modify the subject_list to submit the gear for selected subjects. Does not 
overwrite the failed or stopped gear, so please delete those before running
'''

# Subject list
subject_list = ['TOME_3001','TOME_3002','TOME_3003','TOME_3004','TOME_3005',
                'TOME_3007','TOME_3008','TOME_3009','TOME_3011','TOME_3012',
                'TOME_3013','TOME_3014','TOME_3015','TOME_3016','TOME_3017',
                'TOME_3018','TOME_3019','TOME_3020','TOME_3021','TOME_3022',
                'TOME_3023','TOME_3024','TOME_3025','TOME_3026','DISCARTED_TOME_3027',
                'TOME_3028','TOME_3029','TOME_3030', 'TOME_3031','TOME_3032',
                'TOME_3033','TOME_3034','TOME_3035','TOME_3036','TOME_3037','TOME_3038',
                'TOME_3039','TOME_3040','TOME_3042','TOME_3043','TOME_3044',
                'TOME_3045','TOME_3046']

# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
hcp_results = [ana for ana in analyses if ana.label.startswith('mrtrix - createSubjectFODMap')]
qp = fw.lookup('gears/create-group-fod-template')
analysis_label = 'mrtrix - createGroupFODTemplate_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Set destination
acquisitions = fw.acquisitions.find('label=all_mprage_images') 
save_destination = fw.get(acquisitions[0].session)

# Set config
config = {'voxelSize': '1.25'}

# Set the initial input dictionary
analysis_ids = []
fails = []
inputs_fod={}
inputs_mask={}
counter = 0
for analysis in hcp_results:
    
    # Get session name and subject_name
    ses = fw.get(analysis.parent.id)
    subject_name = ses.subject.code    
    
    # Get the input name 
    counter += 1
    if counter < 10:
        val = '0' + str(counter)
    else:
        val = str(counter)
    
    # Get keys
    input_fod_key = 'fodImage%s' % val
    input_mask_key = 'maskImage%s' % val
    
    # Get values
    input_fod = analysis.get_file('preproc_wm_fod_%s.mif' % subject_name)
    input_mask = analysis.get_file('upsampled_%s_mask.mif' % subject_name)
    
    # Combine
    inputs_fod[input_fod_key] = input_fod
    inputs_mask[input_mask_key] = input_mask

inputs_fod.update(inputs_mask)
print('submitting createGroupFODTemplate for TOME')
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs_fod, destination=save_destination, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    fails.append(ses)