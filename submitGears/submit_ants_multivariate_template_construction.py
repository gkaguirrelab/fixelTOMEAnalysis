import flywheel
import datetime
import pandas as pd
import tqdm as tqdm

''''
This script can be used to submit antsMultivariateTemplateConstruction gears for the TOME
subjects. Does not overwrite the failed or stopped gear, so please delete those before running
'''

# Initialize gear stuff
now = datetime.datetime.now().strftime("%d/%m/%y_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/ants-multivariate-template-construction')
analysis_label = 'antsMultivariateTemplateConstruction_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Find the subjects that have an hcp-diff run
hcp_results = [ana for ana in analyses if ana.label.startswith('hcp-diff v0.1.5 [All_DTI_acqs]')]

# Set configs
config = {'a': '1',
          'b': '0',
          'd': '3',
          'e': '1',
          'f': '6x4x2x1',
          'g': '0.25',
          'i': '4',
          'j': '6',
          'k': '1',
          'l': '1',
          'm': 'CC',
          'n': '1',
          'o': 'TOME',
          'q': '100x100x70x20',
          'r': '0',
          's': '3x2x1x0',
          't': 'SyN',
          'u': '20:00:00',
          'v': '8gb',
          'w': '1',
          'y': '1',
          'saveLogSeparately': '1'}


# Loop thorugh the subjects that have an hcp-diff run
inputs = {}
counter = 0
for analysis in hcp_results:
    # Get session and subject name
    ses = fw.get(analysis.parent.id)
    subject_name = ses.subject.code
    print('Getting subject %s' % subject_name)
    
    # Set gear save destination to subject TOME_3045
    if subject_name == 'TOME_3045':
        save_destination = ses 

    # Set the input name and create a dictionary key for key/value input
    counter += 1
    if counter < 10:
        val = '0' + str(counter)
    else:
        val = str(counter)
    input_t1_key = 'image%s' % val
    
    # Find and loop through the T1 images and only assign to the dictionary if
    # they are nifti MPRAGE and not axial 
    t1_acq_all = ses.acquisitions.find('label=~^T1')
    for acq in t1_acq_all:
        if 'MPR' in acq.label and not 'axial' in acq.label and not 'Axial' in acq.label and not 'AXIAL' in acq.label:
                for mp in acq.files:
                    if '.nii.gz' in mp.name:
                        value = mp
                        inputs[input_t1_key] = value

# Submit the gear  
analysis_ids = []
fails = []      
print('submitting antsMultivariateTemplateConstruction for TOME')
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=save_destination, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    fails.append(ses)