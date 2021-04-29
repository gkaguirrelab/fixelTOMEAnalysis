import flywheel, datetime

'''
This gear submits register-thalamic-segmentations gear with the segment gear
The results are saved in mprageTemplate and the gear uses the latest
segment-thalamic-nuclei gear results located in the analysis container of 
mprageTemplate
''' 
 
# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/register-thalamic-segmentations')
analysis_label = 'register-thalamic-segmentations_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Get the template 
acquisitions = fw.acquisitions.find('label=all_mprage_images')

# Set the save destination 
save_destination = fw.get(acquisitions[0].session)

# Get the FOD template
fod_files = []
for i in save_destination.analyses:
    if i.label.startswith('mrtrix - createGroupFODTemplate'):
        fod_files.append(i)       
run_to_use = fod_files[-1]
for file in run_to_use.files:
    if file.name[-3:] == '.gz':
        fod_file = file 
        
# Get the latest freesurfer analysis
acquisitions = fw.acquisitions.find('label=mprageTemplate')
ses = fw.get(acquisitions[0].session)
freesurfer_runs = []
for i in ses.analyses:
    if i.label.startswith('freesurfer-recon-all'):
        freesurfer_runs.append(i)       
run_to_use = freesurfer_runs[-1]
for file in run_to_use.files:
    if file.name[-3:] == 'zip':
        freesurfer_file = file 

# Get the latest segment thalamic nuclei gear
segment_thalamic_gear = []
for i in ses.analyses:
    if i.label.startswith('segmentthalamicnuclei') or i.label.startswith('segment-thalamic-nuclei'):
        segment_thalamic_gear.append(i)       
run_to_use = segment_thalamic_gear[-1]
for file in run_to_use.files:
    if file.name[-3:] == 'zip':
        segmentation_zip = file 
        
# Get the freesurfer license
freesurfer_license = project_files[0]

# Set inputs
inputs = {'freesurferLicense': freesurfer_license, 
          'reconAllGearOutput': freesurfer_file,
          'thalamicSegmentationArchive': segmentation_zip,
          'targetImage': fod_file}

# Set configs 
config = {'subject_id': 'SubjectToMrtrixFOD',
          'verbose': '1'}

print('submitting register-thalamic-segmentations gear')
analysis_ids = []
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)