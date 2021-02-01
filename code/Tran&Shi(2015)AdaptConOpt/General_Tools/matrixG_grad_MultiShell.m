function [dG_dLambda1, dG_dLambda2] = matrixG_grad_MultiShell(params)
% [dG_dLambda1, dG_dLambda2] = matrixG_grad_MultiShell(params)
%
%  Compute the gradient with respect to the matrix G

dG_dLambda1 = zeros(size(params.B));
dG_dLambda2 = zeros(size(params.B));
bval_set = unique(params.bval);
for i = 1:length(bval_set);
    ind = find(params.bval==bval_set(i));
    [g,h1,h2] = SHCoefficient(params.lambda1,params.lambda2,bval_set(i));
    h1 = h1(1:(params.maxOrder/2+1));
    h2 = h2(1:(params.maxOrder/2+1));
    
    dG_dLambda1(ind,1) = h1(1);
    dG_dLambda1(ind,2:6) = h1(2); %l=2
    dG_dLambda1(ind,7:15) = h1(3); %l=4;
    
    if params.maxOrder>4
        dG_dLambda1(ind,16:28) = h1(4); % l=6
    end;
    if params.maxOrder>6
        dG_dLambda1(ind,29:45) = h1(5); % l = 8;
    end
    if params.maxOrder>8
       dG_dLambda1(ind,46:66) = h1(6); % l = 10;
    end
    if params.maxOrder>10
        dG_dLambda1(ind,67:91) = h1(7); % l = 12;
    end
     
    dG_dLambda2(ind,1) = h2(1);
    dG_dLambda2(ind,2:6) = h2(2); %l=2
    dG_dLambda2(ind,7:15) = h2(3); %l=4;
    
    if params.maxOrder>4
        dG_dLambda2(ind,16:28) = h2(4); % l=6
    end;
    if params.maxOrder>6
        dG_dLambda2(ind,29:45) = h2(5); % l = 8;
    end
    if params.maxOrder>8
       dG_dLambda2(ind,46:66) = h2(6); % l = 10;
    end
    if params.maxOrder>10
        dG_dLambda2(ind,67:91) = h2(7); % l = 12;
    end
end;
