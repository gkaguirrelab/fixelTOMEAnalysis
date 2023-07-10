function a = MeshArea2(coord,trg)
%a = MeshArea2(coord,trg)

a = 0;
for i=1:size(trg,1)
    a = a + TrgArea(coord(trg(i,1),:),coord(trg(i,2),:),coord(trg(i,3),:));
end
