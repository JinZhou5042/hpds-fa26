%% AME60614 Fa'21 - PS1 - P1
clear;clc

syms h

% -----------------------------------------------
% Set up stencils

% 3-point right-biased
A_3pt_R=[1 1 1; 
    0 h 2*h; 
    0 h^2/2 2*h^2;];
HOT_3pt_R = [0 h^3/6 (2*h)^3/6];

% 3-point left-biased
A_3pt_L = [1 1 1;
    (-2*h) -h 0;
    [(-2*h)^2 (-h)^2 0]/2;];
HOT_3pt_L = [(-2*h)^3 (-h)^3 0]/6;

% 5-point right-biased
A_5pt_R=[1 1 1 1 1; 
    0 h 2*h 3*h 4*h; 
    0 h^2/2 2*h^2 9*h^2/2 16*h^2/2; 
    0 h^3/6 4*h^3/3 9*h^3/2 64*h^3/6;
    0 h^4/24 2*h^4/3 27*h^4/8 256*h^4/24];
HOT_5pt_R = [0 h^5/120 32*h^5/120 243*h^5/120 1024*h^5/120];
HOT_5pt_R_2 = [0 h^6 (2*h)^6 (3*h)^6 (4*h)^6]/720;

% 5-point left-biased
A_5pt_L = [1 1 1 1 1;
    (-4*h) (-3*h) (-2*h) -h 0;
    [(-4*h)^2 (-3*h)^2 (-2*h)^2 (-h)^2 0]/2;
    [(-4*h)^3 (-3*h)^3 (-2*h)^3 (-h)^3 0]/6;
    [(-4*h)^4 (-3*h)^4 (-2*h)^4 (-h)^4 0]/24];
HOT_5pt_L = [(-4*h)^5 (-3*h)^5 (-2*h)^5 (-h)^5 0]/120;

% 5-pt central
A_5pt_C = [1 1 1 1 1;
    -2*h -h 0 h 2*h;
    2*h^2 h^2/2 0 h^2/2 2*h^2;
    -4*h^3/3 -h^3/6 0 h^3/6 4*h^3/3;
    2*h^4/3 h^4/24 0 h^4/24 2*h^4/3];
HOT_5pt_C = [-32*h^5/120 -h^5/120 0 h^5/120 32*h^5/120];
HOT_5pt_C_2 = [(-2*h)^6/720 (-h)^6/720 0 h^6/720 (2*h)^6/720];


% -----------------------------------------------
% Compute derivatives
% 1st derivatives
disp('------------------------------')
b = [0;1;0];

disp('1st deriv - 3pt right-biased');
coeff = A_3pt_R\b;
disp(coeff)
disp(HOT_3pt_R*coeff);

disp('1st deriv - 3pt left-biased');
coeff = A_3pt_L\b;
disp(coeff)
disp(HOT_3pt_L*coeff)


% 2nd derivative
disp('------------------------------')
b = [0;0;1];

disp('2nd deriv - 3pt right-biased');
coeff = A_3pt_R\b;
disp(coeff)
disp(HOT_3pt_R*coeff);

disp('2nd deriv - 3pt left-biased');
coeff = A_3pt_L\b;
disp(coeff)
disp(HOT_3pt_L*coeff)

b = [0;0;1;0;0];
disp('2nd deriv - 5pt right-biased');
coeff = A_5pt_R\b;
disp(coeff)
disp(HOT_5pt_R*coeff)

disp('2nd deriv - 5pt left-biased');
coeff = A_5pt_L\b;
disp(coeff)
disp(HOT_5pt_L*coeff)


% 4th derivative
disp('------------------------------')
b = [0;0;0;0;1];

disp('4th deriv - 5pt right-biased');
coeff = A_5pt_R\b;
disp(coeff)
disp(HOT_5pt_R*coeff)

disp('4th deriv - 5pt left-biased');
coeff = A_5pt_L\b;
disp(coeff)
disp(HOT_5pt_L*coeff)

disp('4th deriv - 5pt central');
coeff = A_5pt_C\b;
disp(coeff)
disp(HOT_5pt_C*coeff)
disp(HOT_5pt_C_2*coeff)
