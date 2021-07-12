import os

def calculateMaskIntersection(mask_list, fsl_path, workdir, output_dir):
    output_mask = os.path.join(workdir, 'combined_mask.nii.gz')
    base_string = '%s -t %s' % (os.path.join(fsl_path, 'fslmerge'), output_mask)
    for i in mask_list:
        base_string = base_string + ' ' + i
    os.system(base_string)
   
    intersection_mask = os.path.join(output_dir, 'intersection_mask.nii.gz')
    os.system('%s %s -Tmean -thr 1 %s' % (os.path.join(fsl_path, 'fslmaths'), output_mask, intersection_mask))
