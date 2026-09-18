import os, re, sys, pickle
import numpy as np

N_list = (256,512,1024)

fname_list_all = sorted(os.listdir('.'))

for N in N_list:
    print(N)

    fname_list = []
    for fname in fname_list_all:
        if ('output_{}'.format(N) in fname):
            fname_list.append(fname)

    print(fname_list, len(fname_list))
    
    # Get data
    data = np.empty((len(fname_list),5))
    for ifile,fname in enumerate(fname_list):
        avg = 0.0
        n_avg = 0
        with open(fname, 'r') as f:
            for line in f:
                try:
                    time = float(re.sub('.*time=','',line))
                    if (time>0.0):
                        #print(time)
                        avg += time
                        n_avg += 1
                except:
                    continue
        # Done reading the file
        # Finalize average
        if (n_avg>0):
            avg /= float(n_avg)
        else:
            avg = 0.0
        NN,npx,npy,npz = re.findall(r'\d+', fname)
        data[ifile,:] = [NN,npx,npy,npz,avg]

    # Done looping over files
    print(data)

    # Dump data
    pickle.dump( data, open('timing_{}.dat'.format(N),'wb') )
