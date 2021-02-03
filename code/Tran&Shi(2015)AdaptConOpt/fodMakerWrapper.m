function fodMakerWrapper(constraints, sphereObject, workdir, outputPath, subjectId, inputDTI, DTIMask, bval, bvec, BValLowTHD, BValHighTHD, SPHMaxOrder, MinNumConstraint, NumOptiSteps, init_xi, xi_stepsize, xi_NumSteps, MaxNumFiberCrossingPerVoxel, UniformityFlag, NoiseFloor)

% Create the workdir and outputDir
system(['mkdir' ' ' workdir]);
system(['mkdir' ' ' outputPath]);

% Get input file parts
[filepath,name,ext] = fileparts(inputDTI);

% Run the RAS Flip script
fprintf('Reorienting to RAS \n')
flippedDTI = fullfile(workdir, ['RAS_' name ext]);
flippedMask = fullfile(outputPath, ['mask_' name ext]);
gradTable = fullfile(workdir, 'gradTable.txt');
maskGrad = fullfile(workdir, 'donotuse.txt');
FlipNII2RAS(inputDTI, flippedDTI, bval, bvec, gradTable)
FlipNII2RAS(DTIMask, flippedMask, bval, bvec, maskGrad)

% Create a folder for splitted DTI and split the DTI for memory efficiency
fprintf('Splitting DTI to speed up calculations \n')
split_times = '2';
splittedDataFolder = fullfile(workdir, 'splittedData');
system(['mkdir' ' ' splittedDataFolder]);
SplitHCPDTIData(inputDTI, DTIMask, DTIMask, split_times, splittedDataFolder, subjectId)

% Run the FOD 
fprintf('Making FOD images from DTI pieces \n')
splittedFODFolder = fullfile(outputPath, 'splittedFOD');
system(['mkdir' ' ' splittedFODFolder]);
splittedTissueFolder = fullfile(outputPath, 'splittedTissue');
system(['mkdir' ' ' splittedTissueFolder]);

for piece = 1:str2num(split_times)
    if piece<10
        splittedData = fullfile(splittedDataFolder, [subjectId '_Data_0' num2str(piece) '.nii']);
        splittedMask = fullfile(splittedDataFolder, [subjectId '_Mask_0' num2str(piece) '.nii']);
        outputFOD = fullfile(splittedFODFolder, ['FOD_0' num2str(piece) '.nii']);
        outputTissueMap = fullfile(splittedTissueFolder, ['Tissue_0' num2str(piece) '.nii']);
        fprintf(['Processing data:' ' ' subjectId '_Data_0' num2str(piece) '.nii' '\n'])
    else
        splittedData = fullfile(splittedDataFolder, [subjectId '_Data_' num2str(piece) '.nii']);
        splittedMask = fullfile(splittedDataFolder, [subjectId '_Mask_' num2str(piece) '.nii']);
        outputFOD = fullfile(splittedFODFolder, ['FOD_' num2str(piece) '.nii']);
        outputTissueMap = fullfile(splittedTissueFolder, ['Tissue_' num2str(piece) '.nii']);
        fprintf(['Processing data:' ' ' subjectId '_Data_' num2str(piece) '.nii' '\n'])        
    end
    FOD_AdaptiveConvexOpt_WholeVolume_KernelOptimization(constraints, sphereObject, gradTable, BValLowTHD, BValHighTHD, splittedData, '0', splittedMask, SPHMaxOrder, MinNumConstraint, NumOptiSteps, init_xi, xi_stepsize, xi_NumSteps, MaxNumFiberCrossingPerVoxel, UniformityFlag, NoiseFloor, outputFOD, outputTissueMap)
end
