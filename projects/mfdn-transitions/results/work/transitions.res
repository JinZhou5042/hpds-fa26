 
[MFDn Transitions]
Version = 0
Revision = 1.0.0-0-gdbe217c
Platform = 
Username = 
MPIranks  =        4
OMPthreads =        8
 
[PARAMETERS]
 
[Bra basis]
basisfilename = ../data/Z3-N3-Daejeon16-coul1-hw15.000-a_cm50-Nmax02-Mj1.0-lan600-tol1.0e-06/mfdn_MBgroups
num_protons   =        3
num_neutrons  =        3
Mj            =        1.0
parity        =        1
 
[Ket basis]
basisfilename = ../data/Z3-N3-Daejeon16-coul1-hw15.000-a_cm50-Nmax02-Mj1.0-lan600-tol1.0e-06/mfdn_MBgroups
num_protons   =        3
num_neutrons  =        3
Mj            =        1.0
parity        =        1
 
[State information]
smwffilename_bra = ../data/Z3-N3-Daejeon16-coul1-hw15.000-a_cm50-Nmax02-Mj1.0-lan600-tol1.0e-06/mfdn_smwf
num_bras =        1
brastate =        1
J_bra    =        1.0
n_bra    =        1
smwffilename_ket = ../data/Z3-N3-Daejeon16-coul1-hw15.000-a_cm50-Nmax02-Mj1.0-lan600-tol1.0e-06/mfdn_smwf
num_kets =        1
ketstate =        1
J_ket    =        1.0
n_ket    =        1
 
[RESULTS]
 
[Two-body observable]
#  J0  g0 Tz0  name
    0   0   0  ../data/identity_h2v15099
 
#   Jf  gf   nf    Ji  gi   ni              rme
   1.0   0    1   1.0   0    1   0.17320509E+01
 
[Two-body observable]
#  J0  g0 Tz0  name
    0   0   0  ../data/Tintr_h2v15099
 
#   Jf  gf   nf    Ji  gi   ni              rme
   1.0   0    1   1.0   0    1   0.13019831E+03
 
