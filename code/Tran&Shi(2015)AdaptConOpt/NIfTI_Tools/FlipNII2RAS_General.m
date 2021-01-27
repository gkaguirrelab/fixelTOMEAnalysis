function FlipNII2RAS_General(InputNII,NII_RAS)
%FlipNII2RAS_General(InputNII,NII_RAS)
%
%For Nifit files converted by dcm2nii from dicom, we want to flip along the axes to make it best
%aligned with the RAS definition and update related parameters. 
%
%Yonggang Shi
%May 2015
nii = load_untouch_nii(InputNII);

if nii.hdr.hist.sform_code == 1;
    R = [nii.hdr.hist.srow_x;nii.hdr.hist.srow_y;nii.hdr.hist.srow_z];
else %use qform
     b = nii.hdr.hist.quatern_b;
    c = nii.hdr.hist.quatern_c;
    d = nii.hdr.hist.quatern_d;

    if 1.0-(b*b+c*c+d*d) < 0
     if abs(1.0-(b*b+c*c+d*d)) < 1e-5
        a = 0;
     else
        error('Incorrect quaternion values in this NIFTI data.');
     end
    else
     a = sqrt(1.0-(b*b+c*c+d*d));
    end
    qfac = nii.hdr.dime.pixdim(1);
    if qfac==0, qfac = 1; end
    i = nii.hdr.dime.pixdim(2);
    j = nii.hdr.dime.pixdim(3);
    k = qfac * nii.hdr.dime.pixdim(4);

    R4 = [a*a+b*b-c*c-d*d     2*b*c-2*a*d        2*b*d+2*a*c
       2*b*c+2*a*d         a*a+c*c-b*b-d*d    2*c*d-2*a*b
       2*b*d-2*a*c         2*c*d+2*a*b        a*a+d*d-c*c-b*b];

    R4 = R4*diag([i;j;k]);
    T4 = [nii.hdr.hist.qoffset_x;
       nii.hdr.hist.qoffset_y;
       nii.hdr.hist.qoffset_z];
   R = [R4 T4];
end

sz = nii.hdr.dime.dim(2:4);
s = nii.hdr.dime.pixdim(2:4);
a = zeros(3,1);
[max_val,max_ind] = max(abs(R(:,1:3)*diag(1./s)),[],2);

for i = 1:3
    if R(i,max_ind(i))<0 %Need to flip this dimension
        R(:,max_ind(i)) = -R(:,max_ind(i));
        a(max_ind(i)) = sz(max_ind(i))-1; %because voxel index start with 0 in nifti
        nii.img = flipdim(nii.img,max_ind(i));        
    end;
end
R(:,4) = R(:,4) - R(:,1:3)*a; %correct for the shift;

%swap axis
[max_val,max_ind] = max(abs(R(:,1:3)*diag(1./s)),[],2);
nii.img = permute(nii.img,max_ind);
R(:,1:3) = R(:,max_ind);

%split into rotation and translation
T = R(:,4);
R = R(:,1:3);
R = R*diag(1./s); 
%compute quarternions
nii.hdr.hist.qform_code = 1;
a = 0.5*sqrt(1+R(1,1)+R(2,2)+R(3,3));
nii.hdr.hist.quatern_b = 0.25*(R(3,2)-R(2,3))/a;
nii.hdr.hist.quatern_c = 0.25*(R(1,3)-R(3,1))/a;
nii.hdr.hist.quatern_d = 0.25*(R(2,1)-R(1,2))/a;
nii.hdr.dime.pixdim(1) = 1;
nii.hdr.hist.qoffset_x = T(1);
nii.hdr.hist.qoffset_y = T(2);      
nii.hdr.hist.qoffset_z = T(3);
       
R = R*diag(s); %put the scale back
nii.hdr.hist.sform_code = 1;
nii.hdr.hist.srow_x(1:3) = R(1,:);
nii.hdr.hist.srow_x(4) = T(1);    
nii.hdr.hist.srow_y(1:3) = R(2,:);
nii.hdr.hist.srow_y(4) = T(2);     
nii.hdr.hist.srow_z(1:3) = R(3,:);
nii.hdr.hist.srow_z(4) = T(3);
        
nii.hdr.dime.dim(2:4) = nii.hdr.dime.dim(max_ind+1);
nii.hdr.dime.pixdim(2:4) = nii.hdr.dime.pixdim(max_ind+1);

nii.hdr.hist.magic = 'n+1';
save_untouch_nii(nii,NII_RAS);

