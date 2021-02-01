function SplitHCPDTIData(Data,GradDev,Mask,NumSplit,OutputDir,SubjID)
%SplitHCPDTIData(Data,GradDev,Mask,NumSplit,OutputDir,SubjID)
%
%Split the HCP diffusion data into NumSplit equal parts. This is useful for
%high order FOD computation. 
NumSplit = str2num(NumSplit);
nii_Data = load_untouch_nii(Data);
nii_GradDev = load_untouch_nii(GradDev);
nii_Mask = load_untouch_nii(Mask);

n = sum(nii_Mask.img(:)>0);
count = 1;
SliceIndexArr = zeros(NumSplit,1);
s = 0;
for i = 1:size(nii_Mask.img,3)
    im = nii_Mask.img(:,:,i);
    s = s + sum(im(:)>0);
    if s>count*n/NumSplit
        SliceIndexArr(count) = i;
        count = count + 1;
    end;
end
SliceIndexArr(end) = i;

nii2 = nii_Mask;
nii3 = nii_Data;
nii4 = nii_GradDev;
for i = 1:NumSplit
    if i<10
        SplitMaskName = [OutputDir '/' SubjID '_Mask_0' num2str(i) '.nii'];
        SplitDataName = [OutputDir '/' SubjID '_Data_0' num2str(i) '.nii'];
        SplitGradDevName = [OutputDir '/' SubjID '_GradDev_0' num2str(i) '.nii'];        
    else
        SplitMaskName = [OutputDir '/' SubjID '_Mask_' num2str(i) '.nii'];
        SplitDataName = [OutputDir '/' SubjID '_Data_' num2str(i) '.nii'];
        SplitGradDevName = [OutputDir '/' SubjID '_GradDev_' num2str(i) '.nii'];        
    end;
    if i==1
        nii2.img = nii_Mask.img(:,:,1:SliceIndexArr(i));    
        nii3.img = nii_Data.img(:,:,1:SliceIndexArr(i),:);
        nii4.img = nii_GradDev.img(:,:,1:SliceIndexArr(i),:);
    else
        nii2.img = nii_Mask.img(:,:,SliceIndexArr(i-1)+1:SliceIndexArr(i));
        nii3.img = nii_Data.img(:,:,SliceIndexArr(i-1)+1:SliceIndexArr(i),:);
        nii4.img = nii_GradDev.img(:,:,SliceIndexArr(i-1)+1:SliceIndexArr(i),:);
        
    end;
    nii2.hdr.dime.dim(4) = size(nii2.img,3);
    nii3.hdr.dime.dim(4) = size(nii2.img,3);
    nii4.hdr.dime.dim(4) = size(nii2.img,3);
    
    save_untouch_nii(nii2,SplitMaskName);
    save_untouch_nii(nii3,SplitDataName);
    save_untouch_nii(nii4,SplitGradDevName);
    
end;
