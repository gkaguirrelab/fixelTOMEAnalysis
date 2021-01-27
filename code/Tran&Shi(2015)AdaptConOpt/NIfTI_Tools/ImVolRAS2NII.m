function ImVolRAS2NII(im,res,OutputNII)
%ImVolRAS2NII(im,res,OutputNII)
%
%Generate a nifti file from an image volume in RAS orienation.

% if length(size(im))==3
%     im = permute(im,[2 1 3]);
% end;
% if length(size(im))==4
%     im = permute(im,[2 1 3 4]);
% end;

nii = make_nii(im,res);
srow_x = [res(1) 0 0 -size(im,1)*res(1)/2];
srow_y = [0 res(2) 0 -size(im,2)*res(2)/2];
srow_z = [0 0 res(3) -size(im,3)*res(3)/2];

nii.hdr.hist.srow_x = srow_x;
nii.hdr.hist.srow_y = srow_y;
nii.hdr.hist.srow_z = srow_z;
nii.hdr.hist.sform_code = 1;

R = [nii.hdr.hist.srow_x;nii.hdr.hist.srow_y;nii.hdr.hist.srow_z];
s = nii.hdr.dime.pixdim(2:4);
T = R(:,4);
R = R(:,1:3);
R = R*diag(1./s);
nii.hdr.hist.qform_code = 1;
a = 0.5*sqrt(1+R(1,1)+R(2,2)+R(3,3));
nii.hdr.hist.quatern_b = 0.25*(R(3,2)-R(2,3))/a;
nii.hdr.hist.quatern_c = 0.25*(R(1,3)-R(3,1))/a;
nii.hdr.hist.quatern_d = 0.25*(R(2,1)-R(1,2))/a;
nii.hdr.dime.pixdim(1) = 1;
nii.hdr.hist.qoffset_x = T(1);
nii.hdr.hist.qoffset_y = T(2);
nii.hdr.hist.qoffset_z = T(3);
rmfield(nii.hdr.hist,'originator');
nii.hdr.hist.magic='n+1';
nii.untouch=1;

save_untouch_nii(nii,OutputNII);