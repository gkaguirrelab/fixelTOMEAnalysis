import flywheel, datetime

''''
This script can be used to submit calculate-mask-intersection gear for the TOME
subjects. Saves the results to all_mprage_images.
'''

# Initialize gear stuff
now = datetime.datetime.now().strftime("%d/%m/%y_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/calculate-mask-intersection')
project_files = proj.files

# Find the subjects that have an hcp-diff run
trace_optic_radiation = [ana for ana in analyses if ana.label.startswith('traceOpticRadiation')]

# Set destination
acquisitions = fw.acquisitions.find('label=all_mprage_images') 
save_destination = fw.get(acquisitions[0].session)

# Loop thorugh the subjects that have an hcp-diff run
input_mask = {}
counter = 0
for analysis in trace_optic_radiation:
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
    input_mask_key = 'mask%s' % val
    
    # Main folder
    input_mask_value = analysis.get_file('%s_mask_left_in_FOD_template.nii.gz' % subject_name)
    
    # Set inputs
    input_mask[input_mask_key] = input_mask_value
    
# Submit the gear  
analysis_label = 'left_calculateMaskIntersection_%s_%s' % (qp.gear.version, now)
analysis_ids = []
fails = []      
config = {'outputFileName': 'left_mask'}
print('submitting calculate-mask-intersection for TOME')
try:
    _id = qp.run(analysis_label=analysis_label,
                 config=config, inputs=input_mask, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    fails.append(ses)
    
input_mask = {}
counter = 0
for analysis in trace_optic_radiation:
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
    input_mask_key = 'mask%s' % val
    
    # Main folder
    input_mask_value = analysis.get_file('%s_mask_right_in_FOD_template.nii.gz' % subject_name)
    
    # Set inputs
    input_mask[input_mask_key] = input_mask_value
    
# Submit the gear  
analysis_label = 'right_calculateMaskIntersection_%s_%s' % (qp.gear.version, now)
analysis_ids = []
fails = []     
config = {'outputFileName': 'right_mask'} 
print('submitting calculate-mask-intersection for TOME')
try:
    _id = qp.run(analysis_label=analysis_label,
                 config=config, inputs=input_mask, destination=save_destination)
except Exception as e:
    print(e)
    fails.append(ses)