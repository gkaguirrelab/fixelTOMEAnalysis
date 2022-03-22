import flywheel
import datetime
import pandas as pd
import tqdm as tqdm

''''This script can be used to submit DTI extract values gear for the TOME
subjects. 
Modify the subject_list to submit the gear for selected subjects. Does not 
overwrite the failed or stopped gear, so please delete those before running
'''

# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client('upenn.flywheel.io:dEDBvqRHFRoLbW0u0Q')
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
hcp_results = [ana for ana in analyses if ana.label.startswith('DTImetrics')]
qp = fw.lookup('gears/extract-track-dti-values')
project_files = proj.files

# Set destination
acquisitions = fw.acquisitions.find('label=all_mprage_images') 
save_destination = fw.get(acquisitions[0].session)

# Set config
config = {'voxelSize': '1.25', 'save_warp_archive':True, 'track_density_thresh': '1', 'n_threads': '7','input_is_processed':True}

# Set the initial input dictionary
analysis_ids = []
fails = []
inputs_dti={}
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
    input_dti_key = 'dtiImage%s' % val
    
    # Get values
    input_fa = analysis.get_file('%s_FA.nii.gz' % subject_name)

    # Combine
    inputs_dti[input_dti_key] = input_fa

# Get left, right roi and group template
tome_analyses = analyses
for i in tome_analyses:
    if 'SS3T - createGroupFODTemplate' in i.label:
        group_template_analysis = i
        group_template = group_template_analysis.get_file('FODtemplate.nii.gz')
        inputs_dti['template'] = group_template    
    if 'SS3T - left - calculateMaskIntersection' in i.label:
        left_roi_analysis = i
        left_roi = left_roi_analysis.get_file('left_mask.nii.gz')
        LROI = left_roi
    if 'SS3T - right - calculateMaskIntersection' in i.label:
        right_roi_analysis = i
        right_roi = right_roi_analysis.get_file('right_mask.nii.gz')
        RROI = right_roi 
    if 'SS3T - calculateFixels' in i.label:
        main_analysis = i
        warp_file = main_analysis.get_file('intermediate_files.zip')   

print('submitting LeftFA - extractTrackDTIValues for TOME')
try:
    analysis_label = 'LeftFA-OR - extractTrackDTIValues_%s_%s' % (qp.gear.version, now)
    inputs_dti['ROIOne'] = LROI
    inputs_dti['warpArchive'] = warp_file
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs_dti, destination=save_destination, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    fails.append(ses)  