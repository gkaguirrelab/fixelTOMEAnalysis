import flywheel, datetime

'''
This gear submits trackSingleFODTract gear to calculate left and right 
hemisphere optic tracks.
The results are saved in all_mprage_images and the gear uses the latest
register-thalamic-segmentations gear results
''' 

# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/track-single-fod-tract')
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
        
# Get the aseg and FSvoxel space 
segment_thalamic_gear = []
for i in save_destination.analyses:
    if i.label.startswith('register-thalamic-segmentations'):
        segment_thalamic_gear.append(i)       
run_to_use = segment_thalamic_gear[-1]
for file in run_to_use.files:
    if file.name[-11:] == 'aseg.nii.gz':
        aseg = file
    if file.name[-19:] == 'FSvoxelSpace.nii.gz':  
        thalamicSeg = file
        
# Set inputs
inputs = {'FOD_image': fod_file, 
          'ROI_mask': thalamicSeg,
          'seed_image': aseg}        

# Set configs for left track and submit
analysis_label = 'left - track-single-fod-tract_%s_%s' % (qp.gear.version, now)
config = {'dilateSeedMask': '1',
          'extractROILabel': '8109',
          'extractSeedLabel': '85',
          'minFODamp': '0.2',
          'outputFileName': 'leftOpticTrack',
          'seed_count': '12000'}
print('submitting track-single-fod-tract gear for the left track')
analysis_ids = []
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)
        
# Set configs for left track and submit
analysis_label = 'right - track-single-fod-tract_%s_%s' % (qp.gear.version, now)
config = {'dilateSeedMask': '1',
          'extractROILabel': '8209',
          'extractSeedLabel': '85',
          'minFODamp': '0.2',
          'outputFileName': 'rightOpticTrack',
          'seed_count': '12000'}
print('submitting track-single-fod-tract gear for the right track')
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)