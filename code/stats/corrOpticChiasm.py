import pandas as pd
import flywheel, os
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

def calculateOpticChiasmFixelCorr(left_hemi_fixels, right_hemi_fixels, workdir, output_dir):
    
    left_hemi = pd.read_csv(left_hemi_fixels)
    right_hemi = pd.read_csv(right_hemi_fixels)
    
    # Get subjects in a list
    sub_list = []
    subjects_column = left_hemi['subject']
    for s in subjects_column:
        sub_list.append(s[4:])
    
    # Get the mean column
    left_mean = left_hemi['mean']
    right_mean = right_hemi['mean']
    
    # Get the average of left and right
    average_mean = (left_mean + right_mean) / 2

    # Set flywheel parameters, loop through subjects and get recon-all zip files
    sub_archive_dict = {}
    fw = flywheel.Client()
    proj = fw.projects.find_first('label=tome')
    analyses = fw.get_analyses('projects', proj.id, 'sessions')
    for ana in analyses:
        if ana.label.startswith('freesurfer-recon-all'):
            analysis = ana
            ses = fw.get(analysis.parent.id)
            if ses.subject.code in sub_list:
                subject = ses.subject.code
                zipfile = analysis.get_file('freesurfer-recon-all_%s_%s.zip' % (subject, analysis.id))
                sub_archive_dict[subject] = zipfile
    
    # Get an empty list for optic_chiasm values
    optic_chiasm = []    
    
    # Loop through each subject in the order specified in the fixel csv files
    for ss in sub_list:
        aseg_save = os.path.join(workdir, 'aseg_%s.stats' % ss)
        sub_archive_dict[ss].download_zip_member('%s/stats/aseg.stats' % ss, aseg_save)
        
        # Get the optic chiasm mean values from the text file 
        with open(aseg_save,'r') as f:
            lines = f.read().split("\n")
        word = 'Optic-Chiasm'
        for i,line in enumerate(lines):
            if word in line: # or word in line.split() to search for full words
                optic_line = line  
                splitted_optic_line = optic_line.split()
                optic_index = splitted_optic_line.index('Optic-Chiasm')
                mean = splitted_optic_line[optic_index - 1]
                optic_chiasm.append(float(mean))
                
    # Make a dataframe from the optic chiasm values and save as csv output
    frame_dict = {'subject': sub_list, 'optic-chiasm-mean': optic_chiasm}
    frame = pd.DataFrame(frame_dict)
    frame.to_csv(os.path.join(output_dir, 'tome_optic_chiasm_mean.csv'), index=False)
     
    # Print correlation 
    return(average_mean, optic_chiasm)
    corr, _ = pearsonr(average_mean, optic_chiasm)
    print(corr)
    
    # Plot average fixel vs optic chiasm
    plt.scatter(average_mean, optic_chiasm)
    plt.show()
       
