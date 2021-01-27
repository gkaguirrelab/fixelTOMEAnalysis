function area = TrgArea(pt1,pt2,pt3)
% area = TrgArea(pt1,pt2,pt3)
% Compute the area of a face in triangular meshes.

d1 = pt2 - pt1;
d2 = pt3 - pt1;
nd1 = norm(d1);
nd2 = norm(d2);
if(nd1*nd2>0)
    ip = sum(d1.*d2)/(nd1*nd2);
    ip = min(1,ip);
    ip = max(-1,ip);
    area = 0.5*nd1*nd2*sqrt(1-ip*ip);
else
    area = 0;
end;
