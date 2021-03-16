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
          'A': '1',
          'b': '0',
          'd': '3',
          'e': '1',
          'f': '6x4x2x1',
          'g': '0.2',
          'i': '4',
          'j': '6',
          'k': '1',
          'l': '1',
          'm': 'CC',
          'n': '1',
          'o': 'TOME',
          'q': '100x100x70x20',
          'r': '1',
          's': '3x2x1x0',
          't': 'SyN',
          'w': '1',
          'y': '1',
          'saveLogSeparately': '0'}

# Loop thorugh the subjects that have an hcp-diff run
inputs = {}
counter = 0
acquisitions = fw.acquisitions.find('label=all_mprage_images') 
save_destination = fw.get(acquisitions[0].session)
for analysis in hcp_results:
    # Get session and subject name
    ses = fw.get(analysis.parent.id)
    subject_name = ses.subject.code
    print('Getting subject %s' % subject_name)

    # Set the input name and create a dictionary key for key/value input
    counter += 1
    if counter < 10:
        val = '0' + str(counter)
    else:
        val = str(counter)
    input_t1_key = 'image%s' % val
    
    # Main folder
    for acq in acquisitions:
        parent_folder = acq

    # Get image
    value = parent_folder.get_file(subject_name + '.nii.gz')
    
    # Set inputs
    inputs[input_t1_key] = value

# Use TOME_3040 as the initial target
inputs['aTargetImage'] = inputs['image27']

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