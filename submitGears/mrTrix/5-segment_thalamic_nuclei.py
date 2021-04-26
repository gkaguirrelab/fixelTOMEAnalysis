import flywheel, datetime

'''
This gear submits segment-thalamic-nuclei gear on the TOME Freesurfer results 
The results are saved in mprageTemplate and the gear uses the latest recon-all
gear result located in the analysis container of mprageTemplate
'''  

# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/segmentthalamicnuclei')
analysis_label = 'segment-thalamic-nuclei_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Get the template 
acquisitions = fw.acquisitions.find('label=mprageTemplate')

# Set the save destination 
save_destination = fw.get(acquisitions[0].session)

# Get the latest freesurfer analysis
freesurfer_runs = []
for i in save_destination.analyses:
    if i.label.startswith('freesurfer-recon-all'):
        freesurfer_runs.append(i)       
run_to_use = freesurfer_runs[-1]
for file in run_to_use.files:
    if file.name[-3:] == 'zip':
        freesurfer_file = file 
        
# Get the freesurfer license
freesurfer_license = project_files[0]

# Set inputs
inputs = {'freesurferLicense': freesurfer_license, 
          'reconAllGearOutput': freesurfer_file}

# Set configs 
config = {}

print('submitting segmentThalamicNuclei gear')
analysis_ids = []
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)