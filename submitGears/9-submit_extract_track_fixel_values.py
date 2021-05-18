import flywheel, datetime

''''
This script can be used to submit extract-track-fixel-values gear for the TOME
subjects. Saves the results to all_mprage_images.
'''

# Initialize gear stuff
now = datetime.datetime.now().strftime("%d/%m/%y_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/extract-track-fixel-values')
analysis_label = 'extractTrackFixelValues_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Get the template 
acquisitions = fw.acquisitions.find('label=all_mprage_images')

# Set the save destination 
save_destination = fw.get(acquisitions[0].session)

# Get the calculateFixel gear output
fixel_files = []
for i in save_destination.analyses:
    if i.label.startswith('calculateFixels'):
        fixel_files.append(i)       
run_to_use = fixel_files[-1]
for file in run_to_use.files:
    if 'results' in file.name:
        calculate_fixel_results = file 
        
# Get the trackSingleFodTrack left gear output
left_track_values = []
for i in save_destination.analyses:
    if i.label.startswith('left - track-single-fod-tract'):
        left_track_values.append(i)       
run_to_use = left_track_values[-1]
for file in run_to_use.files:
    if 'leftOpticTrack' in file.name:
        left_track = file         
        
# Get the trackSingleFodTrack right gear output
right_track_values = []
for i in save_destination.analyses:
    if i.label.startswith('right - track-single-fod-tract'):
        right_track_values.append(i)       
run_to_use = right_track_values[-1]
for file in run_to_use.files:
    if 'rightOpticTrack' in file.name:
        right_track = file                 

# Set configs for left track and submit
config = {'track_density_thresh': '1'}
        
# Set inputs for left and submit
inputs = {'calculateFixelResults': calculate_fixel_results, 
          'leftROI': left_track}        
analysis_label = 'left - extractTrackFixelValues_%s_%s' % (qp.gear.version, now)
print('submitting extract-track-fixel-values gear for the left track')       
analysis_ids = []
try:
    _id = qp.run(analysis_label=analysis_label,
                 config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)
    
# Set inputs for right and submit
inputs = {'calculateFixelResults': calculate_fixel_results, 
          'rightROI': right_track}        
analysis_label = 'right - extractTrackFixelValues_%s_%s' % (qp.gear.version, now)
print('submitting extract-track-fixel-values gear for the right track')       
analysis_ids = []
try:
    _id = qp.run(analysis_label=analysis_label,
                 config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)
        