import flywheel, datetime

''''
This script can be used to submit submit-calculate-fixels gear for the TOME
subjects. Saves the results to all_mprage_images.
'''

# Initialize gear stuff
now = datetime.datetime.now().strftime("%d/%m/%y_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/calculate-fixels')
analysis_label = 'SS3T - calculateFixels_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Find the subjects that have an hcp-diff run
hcp_results = [ana for ana in analyses if ana.label.startswith('SS3T - createSubjectFODMap')]

# Set configs
config = {'fmls_peak_value': '0.25',
          'save_intermediate_files': True}

# Set destination
acquisitions = fw.acquisitions.find('label=all_mprage_images') 
save_destination = fw.get(acquisitions[0].session)

# Loop thorugh the subjects that have an hcp-diff run
input_fod = {}
input_mask = {}
counter = 0
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
    input_fod_key = 'fodImage%s' % val
    input_mask_key = 'maskImage%s' % val
    
    # Main folder
    input_fod_value = analysis.get_file('preproc_wm_fod_%s.nii.gz' % subject_name)
    input_mask_value = analysis.get_file('upsampled_%s_mask.nii.gz' % subject_name)
    
    # Set inputs
    input_fod[input_fod_key] = input_fod_value
    input_mask[input_mask_key] = input_mask_value

# Combine fod and mask inputs
input_fod.update(input_mask)

# Get group template
tome_analyses = save_destination.analyses
for i in tome_analyses:
    if 'SS3T - createGroupFODTemplate' in i.label:
        group_template_analysis = i
        group_template = group_template_analysis.get_file('FODtemplate.nii.gz')
        input_fod['fodTemplate'] = group_template     
        
# Submit the gear  
analysis_ids = []
fails = []      
print('submitting mrtrix calculate fixels for TOME')
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=input_fod, destination=save_destination, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    fails.append(ses)