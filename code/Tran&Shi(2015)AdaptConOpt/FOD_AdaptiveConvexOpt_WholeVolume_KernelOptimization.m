function FOD_AdaptiveConvexOpt_WholeVolume_KernelOptimization(constraints, sphereObject, GradTable,BValLowTHD,BValHighTHD,Data,GradDev,Mask,SPHMaxOrder,MinNumConstraint, NumOptiSteps,init_xi,xi_stepsize,xi_NumSteps,MaxNumFiberCrossingPerVoxel,UniformityFlag,NoiseFloor, SPH_Coef_Nifti, TissueMap_Nifti)
%FOD_AdaptiveConvexOpt_WholeVolume_KernelOptimization(GradTable,Data,Mask,GradTHD,SPHMaxOrder,MinNumConstraint,MaxNumFiberCrossingPerVoxel,FOD_THD, xi_stepsize,xi_NumSteps,SPH_Coef_Nifti, TissueMap_Nifti)
%
%FOD reconstruction with adaptive convex optimization. 
%GradTable: Nx4 text file. Each row: (grad_direction[x y z], bvalue[b])
%Data: Nifti file for the diffusion data. XYZD
%

%InitValue for  kernel optimization: For two shell MS data:
%\lambda2=0.0003;\lambda_Diso = 7e-4; For HCP data: \lambda2 = 2e-4;
%\lambda_Diso = 54-4;

NumOptiSteps = str2num(NumOptiSteps); %Num of rounds of optimization

%Try different initial kernel parameters for 
% InitKernelParSet = [0.0017 0.0003 0.0009;0.0017 0.0003 0.0007];
InitKernelParSet = [0.0017 0.000 0.0010]; %ball and stick model

DeltaStep = 5e-5;

%this is the maximum number of fiber crossings we assume in a voxel. This
%is used to tune the sparsity of the reconstructed FODs
MaxNumFiberCrossingPerVoxel = str2num(MaxNumFiberCrossingPerVoxel);
%Minumum magnitude of peaks considered as a fiber direction
params.NoiseFloor = str2num(NoiseFloor);

init_xi = str2num(init_xi); %initial xi
xi_stepsize = str2num(xi_stepsize);
xi_NumSteps = str2num(xi_NumSteps);

SPHMaxOrder = str2num(SPHMaxOrder);
MinNumConstraint = str2num(MinNumConstraint);

[nii.hdr,nii.filetype,nii.fileprefix,nii.machine] = load_nii_hdr(Data);
NumOfSlices = nii.hdr.dime.dim(4);
sz = nii.hdr.dime.dim(2:5);

%Load data and gradient table
GradTable = load(GradTable);
B0_Ind = find(GradTable(:,4)<100);

DTI_Ind = find(GradTable(:,4)>str2num(BValLowTHD) & GradTable(:,4)<str2num(BValHighTHD));
GradVec = GradTable(DTI_Ind,1:3);
BVal = GradTable(DTI_Ind,4);


%prepare the data structure params
load (constraints)

for i = 1:length(ConstraintSet)
    if length(ConstraintSet{i})>=MinNumConstraint
        MinConstraintIndex = i;
        break;
    end;
end;

params.object = sphereObject;
[coord,n,trg] = ReadObjShape(params.object);
%mesh neighboring structure for detecting peaks in FODs
VertNbrCellArr = MeshNeiboringVertices(coord,trg);
Area = MeshArea2(coord,trg);

params.MDirection = GradVec;
params.MSphere = coord;
params.maxOrder = SPHMaxOrder;
params.bval = BVal;
params.bval = round(params.bval/50)*50;%Assume all bvals are rounded to 50s. For HCP, bvals are around 1000,2000,3000. To speed up the matrixG_Multishell and matrixG_grad_MultiShell calculation. 

%eigen-values for the kernel. The sharper the kernel, the better angle
%resolution, but more likely to generate false positives. 
params.lambda1 = 0.0017;
params.lambda2 =  0.000;    
params.Diso = 0.0010;

%Generate matrices with consisits of samples of spherical harmonics on
%point samples on the unit sphere
%This is the matrix for point samples of gradient directions
params.B = matrixB(params.MDirection,params.maxOrder);
%This is the matrix for point samples for FOD representation
params.BS = matrixB(params.MSphere,params.maxOrder);
params.G = matrixG_MultiShell(params);
params.BG = params.B.*params.G;
Npoints = size(params.BS,1);%2562;% for sphere 5120

[m,n] = size(params.BG);
params.BGnew = zeros(m,n+2);
params.BGnew(1:m,1:n) = params.BG;
params.BGnew(:,n+1) = exp(-params.bval*params.Diso); %isotropic component
params.BGnew(:,n+2) = 1; %noise floor
params.aH = params.BGnew'*params.BGnew;

params.FODSumMtx = zeros(1,size(params.BS,2)+2); % (fod iso-componewnt noisefloor)
params.FODSumMtx(1) = sqrt(4*pi);
params.AllSumMtx = params.FODSumMtx;
params.AllSumMtx(end-1:end) = 1;

params.UniformityFlag = str2num(UniformityFlag);

params.s = zeros(length(params.MDirection),1);
R = (params.maxOrder+1)*(params.maxOrder+2)/2; % number of SH basis functions

%calculate FOD reconstruction for the selected slice. 
nii_spharm = load_untouch_nii(Data,[],[],[],[],[],1);
nii_spharm.hdr.dime.dim(4) = NumOfSlices;
nii_spharm.hdr.dime.dim(5) = R;
nii_spharm.hdr.dime.datatype = 16;%float32
nii_spharm.hdr.dime.bitpix = 32;
nii_spharm.img = zeros(sz(1),sz(2),sz(3),R,'single');

nii_tissuemap = load_untouch_nii(Data,[],[],[],[],[],1);
nii_tissuemap.hdr.dime.dim(4) = NumOfSlices;
nii_tissuemap.hdr.dime.dim(5) = 5;
nii_tissuemap.hdr.dime.datatype = 16;%float32
nii_tissuemap.hdr.dime.bitpix = 32;
nii_tissuemap.img = zeros(sz(1),sz(2),sz(3),5,'single');

for k=1:NumOfSlices
    disp(['Slice ' num2str(k)]);
    %only load the specific slice
    nii = load_untouch_nii(Data,[],[],[],[],[],k);
    S0 = mean(nii.img(:,:,:,B0_Ind),4);
    S_Max = max(nii.img(:,:,:,DTI_Ind),[],4);
    Mask_NII = load_untouch_nii(Mask,[],[],[],[],[],k);
    if length(GradDev)==1
        GradDevFlag = 0;
    else
        GradDev_NII = load_untouch_nii(GradDev,[],[],[],[],[],k);
        GradDevFlag = 1;
    end;

    for i = 1:sz(1)
        for j = 1:sz(2)      
            if Mask_NII.img(i,j,1)>0  && S_Max(i,j,1)<2*S0(i,j,1)     
                if GradDevFlag>0
                    %Compute New Bval and Bvec at the current voxel using grad_dev
                    GradCorrectionMtx = reshape(squeeze(GradDev_NII.img(i,j,1,:)),3,3);
                    %%Modified 5/2/2016. Because the GradDev matrix is generated by FSL, I
                    %believe it assumes the LPS orientation. To fix this,
                    %we first flip the sign of the x- and y- component of
                    %the gradient vector, multiply it with the
                    %GradCorrectionMtx, and then flip the sign of the x-
                    %and y- component again. We did not involve the rotation matrix to the RAS space since it is the identitity matrix for HCP data. 
                    %This results in the following correction. 
                    GradCorrectionMtx(1:2,3) = -GradCorrectionMtx(1:2,3); %Modified 5/2/2016. 
                    GradCorrectionMtx(3,1:2) = -GradCorrectionMtx(3,1:2); %Modified 5/2/2016. 
                    
                    IMtx = eye(3);
                    CorrectedBVec = GradVec*(IMtx + GradCorrectionMtx)';
                    CorrectedBVec_Norm = sqrt(sum(CorrectedBVec.^2,2));
                    CorrectedBVec = CorrectedBVec./repmat(CorrectedBVec_Norm,1,3);
                    CorrectedBVal = BVal.*(CorrectedBVec_Norm.^2);
                    params.MDirection = CorrectedBVec;
                    params.bval = CorrectedBVal;
                    params.bval = round(params.bval/50)*50; %Assume all bvals are rounded to 50s. For HCP, bvals are around 1000,2000,3000. To speed up the matrixG_Multishell and matrixG_grad_MultiShell calculation. 
                    %Recompute B Matrix
                    params.B = matrixB(params.MDirection,params.maxOrder);
                end
                %Data samples on gradient directions
                params.s(:) = double(nii.img(i,j,1,DTI_Ind));
                params.s = params.s./double(S0(i,j,1));
                if max(params.s)>1
                    params.s = params.s./max(params.s);
                end;
                
                params.s = params.s - params.NoiseFloor; %subtract a common noise floor if provided

                xi = init_xi;            
                for ii=1:xi_NumSteps
                    final_xi = xi;
                    OptiEnergy = 1000000;
                    if ii==1
                        PeakTHD = 0.025;
                    end
                    for hh = 1:size(InitKernelParSet,1) %Try different set of initial values for kernel parameters to avoid local minima
                        %Recompute G, and BG matrices with initial kernel parameters
                        params.lambda1 = InitKernelParSet(hh,1);
                        params.lambda2 =  InitKernelParSet(hh,2);    
                        params.Diso = InitKernelParSet(hh,3);

                        params.G = matrixG_MultiShell(params);
                        params.BG = params.B.*params.G;

                        [m,n] = size(params.BG);
                        params.BGnew = zeros(m,n+2);
                        params.BGnew(1:m,1:n) = params.BG;
                        params.BGnew(:,n+1) = exp(-params.bval*params.Diso);
                        params.BGnew(:,n+2) = 1;
                        params.aH = params.BGnew'*params.BGnew;          

                        %Set up the constraint matrix. Initially select a minimal set
                        %of point samples where the FOD is constrained to be positive
                        params.BC = params.BS(ConstraintSet{MinConstraintIndex},:);
                        %Data samples on gradient directions

                        %Iteratively solve for the FOD until most of it is positive:
                        %Here 25 is a threshold. 
                        ConstraintIndex = MinConstraintIndex;
                        ConstraintSearchStepSize = 5;
                        while 1
                            d = fod_General6(params,xi);                          
                            params.d = d;
                            y = params.BS*d(1:end-2);           
                            if abs(sum(y(y>0))/sum(y(y<0)))>25 || ConstraintIndex == length(ConstraintSet)
                                break;
                            else
                                ConstraintIndex = ConstraintIndex + ConstraintSearchStepSize;
                                if ConstraintIndex>length(ConstraintSet)
                                    break;
                                end;
                                params.BC = params.BS(ConstraintSet{ConstraintIndex},:);
                            end;
                        end;

                        if j==9
                            disp('stop');
                        end;
                        s_hat = params.BGnew*d;
                        aaa = Area*sum(y)/length(y);
                        old_Energy = 0.5*sum((params.s-s_hat).^2) + xi*aaa;
                        old_params = params;
                        Flag = false; %If energy is decreased 
        
                        for jj = 1:NumOptiSteps %optimization in each iteration         
                            Flag = false;
                            old_grad = zeros(3,1);

                            for kk=1:0 %disable the optimization of lambda2
                                [dG_dLambda1, dG_dLambda2] = matrixG_grad_MultiShell(params);
                                grad2 = (params.s-params.BGnew*d)'*((params.B.*dG_dLambda2)*d(1:end-2));
                                %detect oscillation           
                                if old_grad(2)*grad2<0
                                   break;
                                else
                                   old_grad(2) = grad2;
                                end;            
                                if kk==1
                                    StepSize = DeltaStep/abs(grad2);                
                                else
                                    StepSize = min(StepSize, DeltaStep/abs(grad2));                
                                end;

                                if abs(StepSize*grad2)<5e-6 || params.lambda2 + StepSize*grad2<0.1e-4 || params.lambda2 + StepSize*grad2>4.5e-4
                                    break;
                                end;         

                                params.lambda2 = params.lambda2 + StepSize*grad2;               
                                params.G = matrixG_MultiShell(params);
                                params.BG = params.B.*params.G;
                                [m,n] = size(params.BG);
                                params.BGnew = zeros(m,n+2);
                                params.BGnew(1:m,1:n) = params.BG;
                                params.BGnew(:,n+1) = exp(-params.bval*params.Diso);
                                params.BGnew(:,n+2) = 1;
                                params.aH = params.BGnew'*params.BGnew;        

                                %compute the solution
                                d = fod_General6(params,xi);
                                params.d = d;
                                y = params.BS*d(1:end-2);

                                %compute energy
                                s_hat = params.BGnew*d;
                                aaa = Area*sum(y)/length(y);
                                Energy = 0.5*sum((params.s-s_hat).^2) + xi*aaa;
                                if Energy>=old_Energy
                                    params = old_params;
                                    break;
                                else
                                    old_Energy = Energy;
                                    old_params = params;
                                    Flag = true;
                                end;              

                             end


                            for kk=1:3
                                grad3 = (params.s-params.BGnew*d)'*(-params.bval.*exp(-params.bval*params.Diso))*d(end-1);
                                %detect oscillation           
                               if old_grad(3)*grad3<0
                                   break;
                               else
                                   old_grad(3) = grad3;
                               end;           

                                if kk==1
                                    StepSize = DeltaStep/abs(grad3);                
                                else
                                    StepSize = min(StepSize, DeltaStep/abs(grad3));  
                                end;

                               if abs(StepSize*grad3)<5e-6 || params.Diso + StepSize*grad3<1e-4 
                                   break;
                               end;             

                                params.Diso = params.Diso + StepSize*grad3;
                                [m,n] = size(params.BG);
                                params.BGnew(:,n+1) = exp(-params.bval*params.Diso);
                                params.aH = params.BGnew'*params.BGnew;

                                %compute the solution
                                d = fod_General6(params,xi);
                                params.d = d;
                                y = params.BS*d(1:end-2);

                                %Compute the energy
                                s_hat = params.BGnew*d;
                                aaa = Area*sum(y)/length(y);
                                Energy = 0.5*sum((params.s-s_hat).^2) + xi*aaa;
                                if Energy>=old_Energy
                                    params = old_params;
                                    break;
                                else
                                    old_Energy = Energy;
                                    old_params = params;
                                    Flag = true;
                                end;
                            end


                            for kk=1:0 %disable optimization for lambda1
                                [dG_dLambda1, dG_dLambda2] = matrixG_grad_MultiShell(params);
                                grad1 = (params.s-params.BGnew*d)'*((params.B.*dG_dLambda1)*d(1:end-2));
                                %detect oscillation           
                               if old_grad(1)*grad1<0
                                   break;
                               else
                                   old_grad(1) = grad1;
                               end;            

                                if kk==1
                                    StepSize = DeltaStep/abs(grad1);             
                                else
                                    StepSize = min(StepSize, DeltaStep/abs(grad1));              
                                end;

                                if abs(StepSize*grad1)<5e-6 || params.lambda1 + StepSize*grad1<1e-3 || params.lambda1 + StepSize*grad1>2e-3
                                    break;
                                end; 
                                params.lambda1 = params.lambda1 + StepSize*grad1;
                                params.G = matrixG_MultiShell(params);
                                params.BG = params.B.*params.G;
                                [m,n] = size(params.BG);
                                params.BGnew = zeros(m,n+2);
                                params.BGnew(1:m,1:n) = params.BG;
                                params.BGnew(:,n+1) = exp(-params.bval*params.Diso);    
                                params.BGnew(:,n+2) = 1;
                                params.aH = params.BGnew'*params.BGnew;
                                %compute solution
                                d = fod_General6(params,xi);
                                params.d = d;                    
                                y = params.BS*d(1:end-2);

                                %compute energy
                                s_hat = params.BGnew*d;
                                aaa = Area*sum(y)/length(y);
                                Energy = 0.5*sum((params.s-s_hat).^2) + xi*aaa;
                                if Energy>=old_Energy
                                    params = old_params;
                                    break;
                                else
                                    old_Energy = Energy;
                                    old_params = params;
                                    Flag = true;
                                end;

                           end  

                            if Flag==false %converged because of no energy decrease in this round of optimization
                               break;
                            end
                        end

                        if old_Energy < OptiEnergy
                            OptiEnergy = old_Energy;
                            OptiParams = old_params;
                        end    
                    end
                                 
                
                    %Check for sparsity of FOD
                    y = OptiParams.BS*OptiParams.d(1:end-2);
                    ind_fod = find(y>PeakTHD);
                    if isempty(ind_fod)
                        break;
                    end
                    N = length(ind_fod);
                    count = 0;
                    x = zeros(N,1);
                    for m = 1:N
                        if y(ind_fod(m))>max(y(VertNbrCellArr{ind_fod(m)}))
                            count = count + 1;
                            x(m) = 1;
                        end;
                    end;
               
                    %Test how dominant the lagest fibers are with respect to
                    %all the peaks.
                    a = sort(y(ind_fod(x==1)));                      
                    if isempty(a)
                        break;
                    end;
                    a = a(end:-2:1);

                    if ii==1 %determine the target number of peaks: max(a)>0.5: FOD_THD = max(a)/5; 0.25<max(a)<=0.5: FOD_THD= 0.1; max(a)<0.25: FOD_THD = max(0.05,max(a)/2.5); max(a)<0.125: FOD_THD = 0.05;
                        FOD_THD = min(max(0.05,max(a)/2.5),max(0.1,max(a)/5));
                        NumBigPeaks = length(find(a>=FOD_THD));
                        NumSmallPeaks = length(find(a<FOD_THD & a>0.05 ));
                        if NumBigPeaks>=MaxNumFiberCrossingPerVoxel
                            TargetNumPeaks = MaxNumFiberCrossingPerVoxel;
                        else
                            TargetNumPeaks = NumBigPeaks + min(1,NumSmallPeaks);
                        end;   
                        if TargetNumPeaks>=1
                            PeakTHD  = max(0.05,a(TargetNumPeaks)/2);
                        else
                            PeakTHD = 0.05;
                        end;           
                    end;
                    count = length(find(a>PeakTHD));
                    if count<=TargetNumPeaks
                        break;
                    end;
                                   
                    xi = xi + xi_stepsize;
                end
                
                y = OptiParams.BS*OptiParams.d(1:end-2);
                nii_spharm.img(i,j,k,:) = single(OptiParams.d(1:end-2));
                nii_tissuemap.img(i,j,k,1) = single(4*pi*sum(y(y>0))/length(y));
                nii_tissuemap.img(i,j,k,2) = single(OptiParams.d(end-1));
                nii_tissuemap.img(i,j,k,3) = single(OptiParams.d(end)+OptiParams.NoiseFloor);
                nii_tissuemap.img(i,j,k,4) = OptiParams.Diso;
                nii_tissuemap.img(i,j,k,5) = final_xi;
                

            end
        end;
    end
end

save_untouch_nii(nii_spharm,SPH_Coef_Nifti);
save_untouch_nii(nii_tissuemap,TissueMap_Nifti);
