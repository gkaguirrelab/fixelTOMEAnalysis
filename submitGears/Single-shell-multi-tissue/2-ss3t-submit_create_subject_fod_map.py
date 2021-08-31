import flywheel
import datetime
import pandas as pd
import tqdm as tqdm

''''This script can be used to submit segmentthalamicnuclei gears for the TOME
subjects. 
Modify the subject_list to submit the gear for selected subjects. Does not 
overwrite the failed or stopped gear, so please delete those before running
'''

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

# subject_list = ['TOME_3008']
# Initialize gear stuff
now = datetime.datetime.now().strftime("%y/%m/%d_%H:%M")
fw = flywheel.Client()
proj = fw.projects.find_first('label=tome')
analyses = fw.get_analyses('projects', proj.id, 'sessions')
hcp_results = [ana for ana in analyses if ana.label.startswith('hcp-diff v0.1.5 [All_DTI_acqs]')]
qp = fw.lookup('gears/create-subject-fod-map')
analysis_label = 'SS3T - createSubjectFODMap_%s_%s' % (qp.gear.version, now)
project_files = proj.files

# Set config
config = {'convexOpt-BValHighTHD': '3500',
          'convexOpt-BValLowTHD': '500',
          'convexOpt-init_xi': '0.12',
          'convexOpt-MaxNumFiberCrossingPerVoxel': '4',
          'convexOpt-MinNumConstraint': '120',
          'convexOpt-NoiseFloor':'0',
          'convexOpt-NumOptiSteps':'30',
          'convexOpt-SPHMaxOrder':'8',
          'convexOpt-UniformityFlag':'1',
          'convexOpt-xi_NumSteps':'3',
          'convexOpt-xi_stepsize':'0.06',
          'method':'MRtrix sphericalDec',
          'mrTrix-n_threads': '6',
          'mrTrix-use_highest_b': True,
          'saveIntermediateFiles': True}

# Get the response functions 
response_gear = [ana for ana in analyses if ana.label.startswith('SS3T - calculateAverageResponseFunction')]
response_gear = response_gear[0]
wm = response_gear.get_file('group_average_wm.txt')
gm = response_gear.get_file('group_average_gm.txt')
csf = response_gear.get_file('group_average_csf.txt')

analysis_ids = []
fails = []
for analysis in hcp_results:
    ses = fw.get(analysis.parent.id)
    subject_name = ses.subject.code
    if subject_name in subject_list:
        input_file = analysis.get_file('%s_All_DTI_acqs_hcpdiff.zip' % subject_name)
        
        inputs = {'hcp_diff_archive': input_file, 'response_wm': wm, 'response_gm': gm, 'response_csf': csf}   
        print('submitting createSubjectFODMap for %s' % subject_name)
        try:
            _id = qp.run(analysis_label=analysis_label,
                          config=config, inputs=inputs, destination=ses, tags=['vm-n1-highmem-8_disk-1500G_swap-60G'])
            analysis_ids.append(_id)
        except Exception as e:
            print(e)
            fails.append(ses)