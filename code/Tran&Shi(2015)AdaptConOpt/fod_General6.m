%% FOD with isotropic
% d(end) = ratio of isotropic compartment
function d = fod_General6(params,xi)
%For the general case that every direction has a different b-value. The
%matrix BG is formed a priori. 
%% Find FOD Coefficients
% gamma = 10,100, or 1000;% regularizatoin for the sum of iso and aniso components
% xi:0.1~2 : regulaization for sparsity

% persistent options;
% R = (params.maxOrder+1)*(params.maxOrder+2)/2;

%% Quadprogram from Matlab
% arg min 1/2 x'*H*x + f'*x subject to Ax<=b, where H = aH + iH
% aH = BGnew'*BGnew;% anisotrpic part
af = -params.BGnew'*params.s;
% Constraints
[mc,nc] = size(params.BC);
A = zeros(mc+2,nc+2);
A(1:mc,1:nc) = -params.BC;
A(mc+1,nc+1) = -1;
b = zeros(mc+2,1);
%for noise floor modeling
A(mc+2,nc+2) = -1;
b(mc+2) = 0;

H = params.aH;
f = af + xi*params.FODSumMtx';

%regularization for uniformity
% H = H + params.RegPar*params.AllSumMtx'*params.AllSumMtx;
% f = f -params.RegPar*2*params.AllSumMtx';

%  options = optimset('MaxIter',10*(R+size(params.BC,1)),'Algorithm','interior-point-convex','Display','off','TolFun',1e-6,'TolCon',1e-6);
% 
% d = quadprog(H,f,A,b,[],[],[],[],zeros(R+1,1),options);

% d = cplexqp(H,f,A,b);

if params.UniformityFlag==0
    d = qpip(H,f,A,b);
else
    d= qpip(H,f,A,b,params.AllSumMtx,1-params.NoiseFloor);
end;

