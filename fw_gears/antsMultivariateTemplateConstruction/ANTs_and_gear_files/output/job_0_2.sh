/opt/ants/bin/N4BiasFieldCorrection -d 3 -b [ 200 ] -c [ 50x50x40x30,0.00000001 ] -i /tmp/input_images/1.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0.nii.gz -o /flywheel/v0/output/antsBTPtemplate01.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0Repaired.nii.gz -r 0 -s 2 --verbose 1
 /opt/ants/bin/antsRegistration -d 3 --float 1 --verbose 1 -u 1 -w [ 0.01,0.99 ] -z 1 -r [ /flywheel/v0/output/antsBTPtemplate0.nii.gz,/tmp/input_images/1.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0.nii.gz,1 ] -t Rigid[ 0.1 ] -m MI[ /flywheel/v0/output/antsBTPtemplate0.nii.gz,/flywheel/v0/output/antsBTPtemplate01.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0Repaired.nii.gz,1,32,Regular,0.25 ] -c [ 1000x500x250x0,1e-6,10 ] -f 6x4x2x1 -s 4x2x1x0 -t Affine[ 0.1 ] -m MI[ /flywheel/v0/output/antsBTPtemplate0.nii.gz,/flywheel/v0/output/antsBTPtemplate01.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0Repaired.nii.gz,1,32,Regular,0.25 ] -c [ 1000x500x250x0,1e-6,10 ] -f 6x4x2x1 -s 4x2x1x0 -t SyN[ 0.1,3,0 ] -m CC[ /flywheel/v0/output/antsBTPtemplate0.nii.gz,/flywheel/v0/output/antsBTPtemplate01.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0Repaired.nii.gz,1,4 ] -c [ 100x100x70x20,1e-9,10 ] -f 6x4x2x1 -s 3x2x1x0 -o /flywheel/v0/output/antsBTP1.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.00
 /opt/ants/bin/antsApplyTransforms -d 3 --float 1 --verbose 1 -i /flywheel/v0/output/antsBTPtemplate01.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.0Repaired.nii.gz -o /flywheel/v0/output/antsBTPtemplate01.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.00WarpedToTemplate.nii.gz -r /flywheel/v0/output/antsBTPtemplate0.nii.gz -t /flywheel/v0/output/antsBTP1.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.001Warp.nii.gz -t /flywheel/v0/output/antsBTP1.3.12.2.1107.5.2.43.66044.2019041010404569669868732.0.0.000GenericAffine.mat

