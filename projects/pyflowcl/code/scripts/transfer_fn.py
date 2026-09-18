import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

pc = ['#000000','#ce282a','#255bcb','#2dce65',
      '#a21d8e','#f1ab65','#89b6d4']

from matplotlib import cm,rc
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('text', usetex=True)

# ---------------------------------------------------
# Transfer function
def T(w,alpha,beta,a,b,c=0,d=0,e=0):
    return ((a + b*np.cos(w) + c*np.cos(2*w) + d*np.cos(3*w) + e*np.cos(4*w)) / 
            (1 + 2*alpha*np.cos(w) + 2*beta*np.cos(2*w)))

w = np.linspace(0,np.pi,400)

# ---------------------------------------------------
# Lele 1992, Gaitonde & Visbal AFRL 1998 - 8th order
def coeff_f8(alpha):
    a = (93 + 70*alpha)/128
    b = (7  + 18*alpha)/16
    c = (-7 + 14*alpha)/32
    d = (1  -  2*alpha)/16
    e = (-1 +  2*alpha)/128
    return a,b,c,d,e

# Explicit
alpha = 0.0
a,b,c,d,e = coeff_f8(alpha)
T_f8_alpha0 = T(w,alpha,0.0,a,b,c,d,e)

# Tridiag
alpha = 0.495
a,b,c,d,e = coeff_f8(alpha)
T_f8_alpha0_49 =T(w,alpha,0.0,a,b,c,d,e)


# ---------------------------------------------------
# Lele 1992 (C.2.5) - 6th order
def coeff_f6(alpha,beta):
    a = (11 + 10*alpha - 10*beta)/16
    b = (15 + 34*alpha + 30*beta)/32
    c = (-3 + 6*alpha + 26*beta)/16
    d = (1 - 2*alpha + 2*beta)/32
    return a,b,c,d

# Explicit
alpha = 0.0; beta = 0
a,b,c,d = coeff_f6(alpha,beta)
T_f6_alpha0 = T(w,alpha,beta,a,b,c,d)

# Tridiag
alpha = 0.495; beta = 0
a,b,c,d = coeff_f6(alpha,beta)
T_f6_alpha0_49 = T(w,alpha,beta,a,b,c,d)


# ---------------------------------------------------
# Gaitonde & Visbal AFRL 1998 - 4th order
def coeff_f4(alpha):
    a = 5/8 + 3*alpha/4
    b = 1/2 + alpha
    c = -1/8 + alpha/4
    return a,b,c

# Explicit
alpha = 0.0
a,b,c = coeff_f4(alpha)
T_f4_alpha0 = T(w,alpha,0.0,a,b,c)

# Tridiag
alpha = 0.495
a,b,c = coeff_f4(alpha)
T_f4_alpha0_49 = T(w,alpha,0.0,a,b,c)


# ---------------------------------------------------
# Gaitonde & Visbal AFRL 1998 - 2nd order
def coeff_f2(alpha):
    a = 1/2 + alpha
    b = 1/2 + alpha
    return a,b

# Explicit
alpha = 0.0
a,b = coeff_f2(alpha)
T_f2_alpha0 = T(w,alpha,0.0,a,b)

# Tridiag
alpha = 0.495
a,b = coeff_f2(alpha)
T_f2_alpha0_49 = T(w,alpha,0.0,a,b)


# ---------------------------------------------------
# Lele 1992 (C.2.6) - 4th order
#alpha = 0.0
#beta = 0
#a = (2 + 3*alpha)/4
#b = (9 + 16*alpha + 10*beta)/16
#c = (alpha + 4*beta)/4
#d = (6*beta-1)/16

#T_c26 = T(w,alpha,beta,a,b,c,d)


# ---------------------------------------------------
# Lele 1992 (C.2.8) - 6th order
#alpha = 0
#beta  = 3/10
#a = 1/2
#b = 3/4
#c = 3/10
#d = 1/20

#T_c28 = T(w,alpha,beta,a,b,c,d)


# ---------------------------------------------------
# Plots - central
fix,ax = plt.subplots(figsize=(7,5))

plt.plot(w,np.ones(len(w)),label='Exact',color='k')

plt.plot(w,T_f8_alpha0,   label='F8, $\\alpha=0.0$', c=pc[1])
plt.plot(w,T_f8_alpha0_49,label='F8, $\\alpha=0.495$', c=pc[1], linestyle='--')

plt.plot(w,T_f6_alpha0,   label='F6, $\\alpha=0.0$', c=pc[2])
plt.plot(w,T_f6_alpha0_49,label='F6, $\\alpha=0.495$', c=pc[2], linestyle='--')

plt.plot(w,T_f4_alpha0,   label='F4, $\\alpha=0.0$', c=pc[3])
plt.plot(w,T_f4_alpha0_49,label='F4, $\\alpha=0.495$', c=pc[3], linestyle='--')

plt.plot(w,T_f2_alpha0,   label='F2, $\\alpha=0.0$', c=pc[4])
plt.plot(w,T_f2_alpha0_49,label='F2, $\\alpha=0.495$', c=pc[4], linestyle='--')

#plt.plot(w,T_c26,label='F4 old', c=pc[4])
#plt.plot(w,T_c28,label='(C.2.8)')

plt.xlabel('$\omega$')
plt.ylabel('$T(\omega)$')
plt.xlim([0,np.pi])
plt.legend(frameon=False)
plt.tight_layout()
#plt.show()
plt.savefig('plot_filter_transfer_central.pdf')
plt.close()
