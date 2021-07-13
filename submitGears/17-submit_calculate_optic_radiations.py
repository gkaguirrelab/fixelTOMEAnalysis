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
qp = fw.lookup('gears/trace-optic-radiation')
analysis_label = 'traceOpticRadiation_%s_%s' % (qp.gear.version, now)
project_files = proj.files
subjects = proj.subjects()

bayesprf = [ana for ana in analyses if ana.label.startswith('bayesprf')]
struct = [ana for ana in analyses if ana.label.startswith('hcp-struct')]
recon_all = [ana for ana in analyses if ana.label.startswith('freesurfer-recon-all')]
subject_fod = [ana for ana in analyses if ana.label.startswith('mrtrix - createSubjectFODMap')]
segment_thalamic = [ana for ana in analyses if ana.label.startswith('segmentThalamicNuclei')]

calculate_fixels = [ana for ana in analyses if ana.label.startswith('calculateFixels')]
template_fod = [ana for ana in analyses if ana.label.startswith('mrtrix - createGroupFODTemplate')]
calculate_fixels = calculate_fixels[0]
template_fod = template_fod[0]
intermediate_files_input = calculate_fixels.get_file('intermediate_files.zip')
template_fod_input = template_fod.get_file('FODtemplate.nii.gz')

# Subject list
subject_list = ['TOME_3001','TOME_3002','TOME_3003','TOME_3004','TOME_3005',
                'TOME_3007','TOME_3008','TOME_3009','TOME_3011','TOME_3012',
                'TOME_3013','TOME_3014','TOME_3015','TOME_3016','TOME_3017',
                'TOME_3018','TOME_3019','TOME_3020','TOME_3021','TOME_3022',
                'TOME_3023','TOME_3024','TOME_3025','TOME_3026','DISCARTED_TOME_3027',
                'TOME_3028','TOME_3029','TOME_3030', 'TOME_3031','TOME_3032',
                'TOME_3033','TOME_3034','TOME_3035','TOME_3036','TOME_3037','TOME_3038',
                'TOME_3039','TOME_3040','TOME_3042','TOME_3043','TOME_3044',
                'TOME_3045','TOME_3046']

for sub in subjects:
    subject_id = sub.id
    subject_label = sub.label
    if subject_label in subject_list:
        for bayes in bayesprf:
            if bayes.parents.subject == subject_id:
                bayes_input = bayes.get_file('%s_inferred_volume.zip' % subject_label)
        for st in struct:
            if st.parents.subject == subject_id:
                struct_input = st.get_file('%s_hcpstruct.zip' % subject_label)
        for recon in recon_all:
            if recon.parents.subject == subject_id:
                for fil in recon.files:
                    if fil.name[-3:] == 'zip':
                        recon_input = fil
        for fod in subject_fod:
            if fod.parents.subject == subject_id:
                session_id = fod.parents.session
                fod_input = fod.get_file('preproc_wm_fod_%s.nii.gz' % subject_label)      
        for seg in segment_thalamic:
            if seg.parents.subject == subject_id:
                seg_input = seg.get_file('%s.zip' % subject_label)  
        inputs = {'bayesianPRFOutput': bayes_input, 'calculateFixelIntermediateArchive': intermediate_files_input, 
                  'hcpStructArchive': struct_input, 'reconAllOutput': recon_input,
                  'subjectFOD': fod_input, 'subthalamicSegmentationOutput': seg_input, 
                  'templateFOD': template_fod_input}   
        analysis_ids = []
        fails = []
        print('submitting %s' % subject_label)
        try:
            _id = qp.run(analysis_label=analysis_label,
                          inputs=inputs, destination=fw.get(session_id))
            analysis_ids.append(_id)
        except Exception as e:
            print(e)