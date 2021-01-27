%% Description
% This function calculate for l = 0,2,4,6,8,14,16 for G. For H1 and H2 we
% stop at l = 12.
% G = 2*pi* int P_l(t) exp(-b*lambda2*(1-t^2) - b*lambda1*t^2) for t =-1:1
% H1 = {\partial G}/{\partial lambda1}
% H2 = {\partial G}/{\partial lambda2}
% Last updated: Oct 23th, 2012 

function [G,H1,H2]=SHCoefficient(lambda1,lambda2,b)
%% maxl=8, lambda1 and lambda2 are eigenvalues at a voxel
% b = 1000;
b1 = b*(lambda1-lambda2);
b2   = erf(sqrt(b1));
%% Temp int e^{-b1*t^2}t^{l}, l= 0,2,4,6,8,10,12,14,16,18
% using Wolframalpha to calculate a0,a2,a4,a6,a8 and G(:)
a0 = sqrt(pi/b1)*b2;
a2 = sqrt(pi)*b2/(2*b1^(1.5))-1.0/(b1*exp(b1));
a4 = -(3+2*b1)/(exp(b1)*2*b1^2) + (3*sqrt(pi)*b2)/(4*b1^2.5);
a6 = 15*sqrt(pi)*b2/(8*b1^3.5)-(4*b1^2+10*b1+15)/(4*b1^3*exp(b1));
a8 = 105*sqrt(pi)*b2/(16*b1^4.5) - (2*b1*(2*b1*(2*b1+7)+35)+105)/(8*b1^4*exp(b1));
a10 = 945*sqrt(pi)*b2/(32*b1^5.5) - (2*b1*(2*b1*(2*b1*(2*b1+9)+63)+315)+945)/(16*b1^5*exp(b1));
a12 = 10395*sqrt(pi)*b2/(64*b1^6.5) - (2*b1*(2*b1*(2*b1*(4*b1^2+22*b1+99)+693)+3465)+10395)/(32*b1^6*exp(b1)) ;
a14 = 135135*sqrt(pi) *b2/(128*b1^7.5)-(64*b1^6 + 416*b1^5 + 2288*b1^4 + 10296*b1^3+36036*b1^2 + 90090*b1+135135)/(64*b1^7*exp(b1));
a16 = 2027025*sqrt(pi) *b2/(256*b1^8.5)-(128*b1^7 + 960*b1^6 + 6240*b1^5 + 34320*b1^4 + 154440*b1^3 + 540540*b1^2 + 1351350*b1 + 2027025)/(128*b1^8*exp(b1));

%% G_l(lambda1,lambda2) := Ratio between the SH coefficients of s and those of the fod, l= 0,2,4,6,8
G(1) = a0; % l = 0
G(2) = 1.5*a2-0.5*a0; % l= 2
G(3) = 35/8*a4-15/4*a2+3/8*a0; % l = 4
G(4) = (231*a6 - 315*a4 + 105*a2 - 5*a0)/16.0; % l = 6
G(5) = (6435*a8 - 12012*a6 + 6930*a4 - 1260*a2 + 35*a0)/128.0; % l = 8
G(6) = (46189*a10 - 109395*a8 + 90090*a6 - 30030*a4 + 3465*a2 - 63*a0)/256.0; % l = 10
G(7) = (676039*a12 - 1939938*a10 + 2078505*a8 - 1021020*a6 + 225225*a4 - 18018*a2 + 231*a0)/1024.0; % l = 12
G(8) = (5014575*a14 - 16900975*a12 + 22309287*a10 - 14549535*a8 + 4849845*a6 - 765765*a4 + 45045*a2 - 429*a0)/2048.0; %  l = 14
G(9) = (300540195*a16 - 1163381400*a14 + 1825305300*a12 - 1487285800*a10 + 669278610*a8 - 162954792*a6 + 19399380*a4 - 875160*a2 + 6435*a0)/32768; % l = 16
G = G*2*pi*exp(-b*lambda2);
if sum(isnan(G))>0
                disp('error')
end
%% H1 = \dfrac{\partial G}{\partial \lambda_1}
H1 = zeros(size(G));
H1(1) = a2; % l = 0
H1(2) = (3*a4-a2)/2;% l = 2
H1(3) = (35*a6-30*a4+3*a2)/8;% l = 4
H1(4) = (231*a8 - 315*a6 + 105*a4 - 5*a2)/16;%  l = 6
H1(5) = (6435*a10 - 12012*a8 + 6930*a6 - 1260*a4 + 35*a2)/128; % l = 8
H1(6) = (46189*a12 - 109395*a10 + 90090*a8 - 30030*a6 + 3465*a4 - 63*a2)/256.0; % l = 10
H1(7) = (676039*a14 - 1939938*a12 + 2078505*a10 - 1021020*a8 + 225225*a6 - 18018*a4 + 231*a2)/1024; % l = 12

H1 = -2*b*pi*exp(-b*lambda2)*H1;
%% H2 = \dfrac{\partial G}{\partial \lambda_2}
H2 = zeros(size(G));
H2 = -b*G-H1;










    