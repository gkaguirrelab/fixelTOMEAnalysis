import flywheel
import datetime
import pandas as pd
import tqdm as tqdm

''''This script can be used to submit segmentthalamicnuclei gears for the TOME
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
now = datetime.datetime.now().strftime("%d/%m/%y_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
hcp_results = [ana for ana in analyses if ana.label.startswith('hcp-diff v0.1.5 [All_DTI_acqs]')]
qp = fw.lookup('gears/ants-multivariate-template-construction')
analysis_label = 'antsMultivariateTemplateConstruction_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Set config
config = {'a': '1',
          'b': '0',
          'd': '3',
          'e': '1',
          'f': '6x4x2x1',
          'g': '0.25',
          'i': '4',
          'j': '2',
          'k': '1',
          'l': '1',
          'm': 'CC',
          'n': '1',
          'o': 'antsBTP',
          'q': '100x100x70x20',
          'r': '0',
          's': '3x2x1x0',
          't': 'SyN',
          'u': '20:00:00',
          'v': '8gb',
          'w': '1',
          'y': '1'}

analysis_ids = []
fails = []
inputs_fod = {}
counter = 0
for analysis in hcp_results:
    ses = fw.get(analysis.parent.id)
    subject_name = ses.subject.code
    print('Getting subject %s' % subject_name)
    
    # Set destination to TOME_3045
    if subject_name == 'TOME_3045':
        save_destination = ses

    # Get the input name 
    counter += 1
    if counter < 10:
        val = '0' + str(counter)
    else:
        val = str(counter)

    # Get keys
    input_t1_key = 'image%s' % val
    
    # Values
    t1_acq_all = ses.acquisitions.find('label=~^T1')
    for acq in t1_acq_all:
        if 'MPR' in acq.label:
            mprage = acq
            for mp in mprage.files:
                if '.nii.gz' in mp.name:
                    inputs_fod[input_t1_key] = mp
     
print('submitting antsMultivariateTemplateConstruction for TOME')
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs_fod, destination=save_destination, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    fails.append(ses)