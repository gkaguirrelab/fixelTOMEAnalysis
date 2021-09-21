import flywheel, datetime

# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
qp = fw.lookup('gears/segmentthalamicnuclei')
analysis_label = 'HCP - segment-thalamic-nuclei_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# # Subject list
subject_list = ['TOME_3001','TOME_3002','TOME_3003','TOME_3004','TOME_3005',
                'TOME_3007','TOME_3008','TOME_3009','TOME_3011','TOME_3012',
                'TOME_3013','TOME_3014','TOME_3015','TOME_3016','TOME_3017',
                'TOME_3018','TOME_3019','TOME_3020','TOME_3021','TOME_3022',
                'TOME_3023','TOME_3024','TOME_3025','TOME_3026','DISCARTED_TOME_3027',
                'TOME_3028','TOME_3029','TOME_3030', 'TOME_3031','TOME_3032',
                'TOME_3033','TOME_3034','TOME_3035','TOME_3036','TOME_3037','TOME_3038',
                'TOME_3039','TOME_3040','TOME_3042','TOME_3043','TOME_3044',
                'TOME_3045','TOME_3046']

# Get freesurfer license 
freesurfer_license = proj.files[0]

# Subjects that have HCP struct runs
struct = [ana for ana in analyses if ana.label.startswith('hcp-struct')]

# Set config
config = {'n_threads':6, 'input_is_hcp_archive':True}

# Loop through subjects and submit thalamic nuclei
for st in struct:
    subject_id = st.files[1].name[0:9]
    if subject_id in subject_list:
        destination = fw.get(st.parent.id)
        struct_input = st.get_file('%s_hcpstruct.zip' % subject_id)
        
        inputs = {'reconAllGearOutput': struct_input, 'freesurferLicense':freesurfer_license}      
        _id = qp.run(analysis_label=analysis_label,
                  config=config, inputs=inputs, destination=destination, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
        print('Submitting {subject_id}'.format(subject_id=subject_id))
    
    