function Gmtx = matrixG_MultiShell(params)
% Gmtx = matrixG_MultiShell(params)
%
% Generate the matrix G for the general case that every point could have
% different b_values

Gmtx = zeros(size(params.B));
bval_set = unique(params.bval);

for i = 1:length(bval_set);
    ind = find(params.bval==bval_set(i));
    g = SHCoefficient(params.lambda1,params.lambda2,bval_set(i));
    g = g(1:(params.maxOrder/2+1));
    Gmtx(ind,1) = g(1);
    Gmtx(ind,2:6) = g(2); %l=2
    Gmtx(ind,7:15) = g(3); %l=4;
    if params.maxOrder>4
        Gmtx(ind,16:28) = g(4); % l=6
    end;
    if params.maxOrder>6
        Gmtx(ind,29:45) = g(5); % l = 8;
    end
    if params.maxOrder>8
       Gmtx(ind,46:66) = g(6); % l = 10;
    end
    if params.maxOrder>10
        Gmtx(ind,67:91) = g(7); % l = 12;
    end
    if params.maxOrder>12
        Gmtx(ind,92:120) = g(8); % l = 14;
    end
    if params.maxOrder>14
        Gmtx(ind,121:153) = g(9); % l = 16;
    end
end;   
