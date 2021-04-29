import flywheel
import datetime

'''
This gear submits Freesurfer recon-all gear for the TOME teplate which is 
located in tome, subject/session "mprageTemplate". The results are saved in 
mprageTemplate.
'''  

# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/freesurfer-recon-all')
analysis_label = 'freesurfer-recon-all_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Get the template 
acquisitions = fw.acquisitions.find('label=mprageTemplate')
mprage_template = acquisitions[0].files[2]

# Set the save destination 
save_destination = fw.get(acquisitions[0].session)

# Get the freesurfer license
freesurfer_license = project_files[0]

# Set config
config = {'subject_id': 'TOME_template'}

# Input dictionary 
inputs = {'anatomical': mprage_template, 'freesurfer_license': freesurfer_license}

print('submitting recon-all for mprage template')
analysis_ids = []
try:
    _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=save_destination)
    analysis_ids.append(_id)
except Exception as e:
    print(e)