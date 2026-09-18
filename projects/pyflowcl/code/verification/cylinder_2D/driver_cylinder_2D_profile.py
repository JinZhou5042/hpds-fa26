import sys
import os
#import tracemalloc
#import linecache
import cProfile, pstats, io
from pstats import SortKey

# Add PyFlowCL src to Python path
sys.path.append('../../src')
#sys.path.append('/Users/jmacart/Bitbucket/PyFlowCL/src')

from PyFlowCL import PyFlowCL, Grid
from PyFlowCL.Library import CUDA_Util

# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self,Nx1,Nx2,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = 1

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'cylinder'

        # Initial conditions
        self.IC_opt='cylinder'

        # Nondimensional parameters
        self.Re = 320.0
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 1
        #self.explicit_filter = True

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        self.BC_thickness = 0.1
        self.BC_strength  = 1.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = 1e-4
        self.Nsteps = 100
        self.N_monitor = 10

        # Output options
        self.outDir = 'Output_cylinder_Nx1_{}_Ma{}_Re{}'.format(self.Nx1,
                                                                self.Ma,
                                                                self.Re)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000038000.h5'
        #self.add_noise = True

        # Compute device
        self.device = CUDA_Util.get_device()

        # Stats
        self.Cd_flag = False

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'cylinder'):
            R_min = 0.5
            R_max = 10.0
            sx = 3.0 # for exp grid
            Uniform = True #False
            self.grid = Grid.cylinder(self.device,self.Nx1,self.Nx2,self.Nx3,
                                      R_min,R_max,sx,Uniform)

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))

    
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 256; Nx2 = 256;  dt = 1e-3; Nsteps = 500
    #Nx1 = 256; Nx2 = 256;  dt = 1e-4; Nsteps = 100000 # Re=1
    
    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps)

    # Start malloc profiling
    #tracemalloc.start()

    profile_flag = False
    if profile_flag:
        pr = cProfile.Profile()
        pr.enable()
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)

    if profile_flag:
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

    # Print malloc profiling results
    #snapshot = tracemalloc.take_snapshot()
    #display_top(snapshot)

    #first_size, first_peak = tracemalloc.get_traced_memory()
    #print(f"{first_size=}, {first_peak=}")
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
