import flywheel
import datetime
import pandas as pd
import tqdm as tqdm

''''This script can be used to submit the gear that calculates DTI metrics for 
the TOME subjects. The gear is the same for the fixel calculation gear. 
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
now = datetime.datetime.now().strftime("%y_%m_%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
hcp_results = [ana for ana in analyses if ana.label.startswith('hcp-diff v0.1.5 [All_DTI_acqs]')]
qp = fw.lookup('gears/create-subject-fod-map')
analysis_label = 'DTImetrics - createSubjectFODMap_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Set config
config = {'method':'DTI metrics'}

analysis_ids = []
fails = []
for analysis in hcp_results:
    ses = fw.get(analysis.parent.id)
    subject_name = ses.subject.code
    input_file = analysis.get_file('%s_All_DTI_acqs_hcpdiff.zip' % subject_name)
    
    inputs = {'hcp_diff_archive': input_file}   
    print('submitting createSubjectFODMap for %s' % subject_name)
    try:
        _id = qp.run(analysis_label=analysis_label,
                      config=config, inputs=inputs, destination=ses)
        analysis_ids.append(_id)
    except Exception as e:
        print(e)
        fails.append(ses)