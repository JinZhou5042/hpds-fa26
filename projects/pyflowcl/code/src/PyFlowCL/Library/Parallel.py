"""
------------------------------------------------------------------------
PyFlowCL: A Python-native, compressible Navier-Stokes solver for
curvilinear grids
------------------------------------------------------------------------

@file Parallel.py

"""

__copyright__ = """
Copyright (c) 2022 Jonathan F. MacArt
"""

__license__ = """
 Permission is hereby granted, free of charge, to any person 
 obtaining a copy of this software and associated documentation 
 files (the "Software"), to deal in the Software without 
 restriction, including without limitation the rights to use, 
 copy, modify, merge, publish, distribute, sublicense, and/or 
 sell copies of the Software, and to permit persons to whom the 
 Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be 
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
 OTHER DEALINGS IN THE SOFTWARE.
"""


import numpy as np
import torch
from mpi4py import MPI


# ----------------------------------------------------
# Parallel communication functions
# ----------------------------------------------------
class Comms:
    def __init__(self, cfg):
        if (not MPI.Is_initialized()):
            MPI.Init()
        
        # Get MPI decomposition info
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

        # Check if we will use GPU Direct MPI
        # Default is False
        self.GPU_Direct = getattr(cfg, 'GPU_Direct', False)

    def finalize(self):
        MPI.Finalize()

    def parallel_reduction(self, sendBuf, comm, op):
        if (self.size>1):
            if comm is None:
                comm = self.comm
            if torch.is_tensor(sendBuf):
                # SendBuf is a PyTorch tensor
                if hasattr(sendBuf, "__size__"):
                    sendLen = len(sendBuf)
                    if self.GPU_Direct:
                        device = sendBuf.device
                    else:
                        origin_device = sendBuf.device
                        device = 'cpu'
                else:
                    sendLen = 1
                    device = 'cpu'
                recvBuf = torch.empty(sendBuf.shape, dtype=sendBuf.dtype, device=device)
                comm.Allreduce(sendBuf.to(device), recvBuf, op=op)
                if (sendLen==1):
                    out = recvBuf.item()
                else:
                    out = recvBuf
                    if not self.GPU_Direct:
                        out.to(origin_device)
            else:
                # SendBuf is a pure Python float
                out = comm.allreduce(sendBuf, op=op)
        else:
            # Serial computation; nothing to do
            out = sendBuf
        return out

    def parallel_sum(self, sendBuf, comm=None):
        return self.parallel_reduction(sendBuf, comm=comm, op=MPI.SUM)

    def parallel_max(self, sendBuf, comm=None):
        return self.parallel_reduction(sendBuf, comm=comm, op=MPI.MAX)

    def parallel_min(self, sendBuf, comm=None):
        return self.parallel_reduction(sendBuf, comm=comm, op=MPI.MIN)

    
# ----------------------------------------------------
# MPI decomposition
# ----------------------------------------------------
class Decomp:
    def __init__(self,cfg,grid,WP,WP_np):
        self.WP = WP
        self.WP_np = WP_np

        # Offloading settings
        self.device = cfg.device

        # Check if we will use GPU Direct MPI
        # Default is False
        self.GPU_Direct = getattr(cfg, 'GPU_Direct', False)
        
        # ---------------------------------------
        # MPI communicators
        # Get the global communicator
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

        # User-specified decomposition
        self.npx = cfg.nproc_x
        self.npy = cfg.nproc_y
        self.npz = cfg.nproc_z
        nproc_decomp = [self.npx,self.npy,self.npz]
        
        # Check the decomp
        if (self.size!=self.npx*self.npy*self.npz):
            raise Exception('\nNumber of MPI tasks does not match the specified domain decomposition\n')

        # Cartesian communicator to determine coordinates
        self.isper = ( grid.periodic_xi,
                       grid.periodic_eta,
                       True )
        self.cartComm = self.comm.Create_cart(nproc_decomp,periods=self.isper,
                                              reorder=False) # ONLY FOR FRONTIER
        
        # Proc's location in the cartesian communicator
        self.iproc,self.jproc,self.kproc = self.cartComm.Get_coords(self.rank)

        # Create line communicators
        # Along x
        dir = [True,False,False]
        self.cartCommX = self.cartComm.Sub(dir)
        #self.irank_x   = self.cartCommX.Get_rank()
        # Along y
        dir = [False,True,False]
        self.cartCommY = self.cartComm.Sub(dir)
        #self.irank_y   = self.cartCommY.Get_rank()
        # Along z
        dir = [False,False,True]
        self.cartCommZ = self.cartComm.Sub(dir)
        #self.irank_z   = self.cartCommZ.Get_rank()

        # Create plane communicators
        # Along xy
        dir = [True,True,False]
        self.cartCommXY = self.cartComm.Sub(dir)
        # Along xz
        dir = [True,False,True]
        self.cartCommXZ = self.cartComm.Sub(dir)
        # Along yz
        dir = [False,True,True]
        self.cartCommYZ = self.cartComm.Sub(dir)

        
        # ---------------------------------------
        # Domain decomposition
        
        # Grid size
        self.nx = grid.Nx1
        self.ny = grid.Nx2
        self.nz = grid.Nx3
        self.N = self.nx*self.ny*self.nz

        # Overlap size
        # 3 for derivatives, 4 for filtering
        # 6 for "extended interior" derivatives
        self.nover = 5

        # Global indexing
        self.nxo  = self.nx+2*self.nover
        self.nyo  = self.ny+2*self.nover
        self.nzo  = self.nz+2*self.nover
        self.imino = 0
        self.jmino = 0
        self.kmino = 0
        self.imaxo = self.imino+self.nxo-1
        self.jmaxo = self.jmino+self.nyo-1
        self.kmaxo = self.kmino+self.nzo-1
        self.imin  = self.imino+self.nover
        self.jmin  = self.jmino+self.nover
        self.kmin  = self.kmino+self.nover
        self.imax  = self.imin+self.nx-1
        self.jmax  = self.jmin+self.ny-1
        self.kmax  = self.kmin+self.nz-1
        
        # Decomposition:
        #   imin_loc, imax_loc, etc. are local positions
        #   in global grid but do NOT include overlap cells
        
        imin = 0
        q = int(self.nx/self.npx)
        r = int(np.mod(self.nx,self.npx))
        if ((self.iproc+1)<=r):
            self.nx_   = q+1
            self.imin_loc = imin + self.iproc*(q+1)
        else:
            self.nx_   = q
            self.imin_loc = imin + r*(q+1) + (self.iproc-r)*q
        self.imax_loc = self.imin_loc + self.nx_ - 1
        
        # y-deomposition
        jmin = 0
        q = int(self.ny/self.npy)
        r = int(np.mod(self.ny,self.npy))
        if ((self.jproc+1)<=r):
            self.ny_   = q+1
            self.jmin_loc = jmin + self.jproc*(q+1)
        else:
            self.ny_   = q
            self.jmin_loc = jmin + r*(q+1) + (self.jproc-r)*q
        self.jmax_loc = self.jmin_loc + self.ny_ - 1
        
        # z-decomposition
        kmin = 0
        q = int(self.nz/self.npz)
        r = int(np.mod(self.nz,self.npz))
        if ((self.kproc+1)<=r):
            self.nz_   = q+1
            self.kmin_loc = kmin + self.kproc*(q+1)
        else:
            self.nz_   = q
            self.kmin_loc = kmin + r*(q+1) + (self.kproc-r)*q
        self.kmax_loc = self.kmin_loc + self.nz_ - 1

        #print("rank={}\t imin_={}\timax_={}\tnx_={}\t jmin_={}\tjmax_={}\tny_={}\t kmin_={}\tkmax_={}\tnz_={}"
        #      .format(self.rank,
        #              self.imin_loc,self.imax_loc,self.nx_,
        #              self.jmin_loc,self.jmax_loc,self.ny_,
        #              self.kmin_loc,self.kmax_loc,self.nz_))

        # Local indexing including overlaps
        self.nxo_  = self.nx_+2*self.nover
        self.nyo_  = self.ny_+2*self.nover
        self.nzo_  = self.nz_+2*self.nover
        self.imino_ = 0
        self.jmino_ = 0
        self.kmino_ = 0
        self.imaxo_ = self.imino_+self.nxo_-1
        self.jmaxo_ = self.jmino_+self.nyo_-1
        self.kmaxo_ = self.kmino_+self.nzo_-1

        # Local indexing for interior only
        self.imin_ = self.imino_+self.nover
        self.jmin_ = self.jmino_+self.nover
        self.kmin_ = self.kmino_+self.nover
        self.imax_ = self.imin_+self.nx_-1
        self.jmax_ = self.jmin_+self.ny_-1
        self.kmax_ = self.kmin_+self.nz_-1

        # Eliminate z-overlaps if problem is 2D
        if (self.nz==1):
            self.nzo    = 1
            self.nz_    = 1
            self.nzo_   = 1
            self.kmaxo  = 0
            self.kmino_ = 0
            self.kmaxo_ = 0
            self.kmin_  = 0
            self.kmax_  = 0

        # Eliminate x-overlaps if problem is 1D
        if (self.nx==1):
            self.nxo    = 1
            self.nx_    = 1
            self.nxo_   = 1
            self.imaxo  = 0
            self.imino_ = 0
            self.imaxo_ = 0
            self.imin_  = 0
            self.imax_  = 0


    # ------------------------------------------------
    # Destructor
    def __del__(self):
        self.cartCommX.Free()
        self.cartCommY.Free()
        self.cartCommZ.Free()
        self.cartCommXY.Free()
        self.cartCommXZ.Free()
        self.cartCommYZ.Free()
        self.cartComm.Free()

        
    # ------------------------------------------------
    # Functions to move buffers to/from device if not using
    # GPU Direct MPI
    def from_device(self, x):
        return x if self.GPU_Direct else x.cpu()

    def to_device(self, x):
        return x if self.GPU_Direct else x.to(self.device)

        
    # ------------------------------------------------
    # Communicate overlap cells for generic state data
    def communicate_border(self,A):
        n1 = self.nxo_
        n2 = self.nyo_
        n3 = self.nzo_
        no = self.nover

        # x
        if (self.nx > 1):
            self.communicate_border_x(A,n1,n2,n3,no)
        # y
        self.communicate_border_y(A,n1,n2,n3,no)
        # z
        if (self.nz > 1):
            self.communicate_border_z(A,n1,n2,n3,no)
        
    # ------------------------------------------------
    # Communicate overlap cells for 2D data
    def communicate_border_2D(self,A):
        n1 = self.nxo_
        n2 = self.nyo_
        n3 = 1
        no = self.nover

        # x
        if (self.nx > 1):
            self.communicate_border_x(A,n1,n2,n3,no)
        # y
        self.communicate_border_y(A,n1,n2,n3,no)
        
        
    def communicate_border_2D_ADJOINT(self,A):
        n1 = self.nxo_
        n2 = self.nyo_
        n3 = 1
        no = self.nover

        # x
        if (self.nx > 1):
            self.communicate_border_x_ADJOINT(A,n1,n2,n3,no)
        # y
        self.communicate_border_y_ADJOINT(A,n1,n2,n3,no)        
        
            
    # --------------------------------------------
    # Communicate overlap cells in the x-direction
    def communicate_border_x(self,A,n1,n2,n3,no):
        sendbuf = self.from_device(A.detach()[no:2*no,:,:].contiguous())
        recvbuf = torch.empty_like(sendbuf)

        # Send left buffer to left neighbor
        isource,idest = self.cartComm.Shift(0,-1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received left buffer to the right overlap cells
        if (isource!=MPI.PROC_NULL):
            A[n1-no:n1,:,:].copy_(self.to_device(recvbuf))

        # Right buffer
        sendbuf = self.from_device(A.detach()[n1-2*no:n1-no,:,:].contiguous())
        
        # Send right buffer to right neighbor
        isource,idest = self.cartComm.Shift(0,+1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received right buffer to the left overlap cells
        if (isource!=MPI.PROC_NULL):
            A[0:no,:,:].copy_(self.to_device(recvbuf))

        # Clean up
        del recvbuf
        
        
    # --------------------------------------------
    # Communicate overlap cells in the x-direction for adjoint
    def communicate_border_x_ADJOINT(self,A,n1,n2,n3,no):
        # Left buffer
        sendbuf = self.from_device(A[0:1*no,:,:].contiguous())
        recvbuf = torch.empty_like(sendbuf)
        
        # Send left buffer to left neighbor
        isource,idest = self.cartComm.Shift(0,-1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received left buffer to the right overlap cells
        if (isource!=MPI.PROC_NULL):
            A[-2*no:-1*no,:,:] += self.to_device(recvbuf)

        # Right buffer
        sendbuf = self.from_device(A[-1*no:,:,:].contiguous())
        recvbuf = torch.empty_like(sendbuf)
        
        # Send right buffer to right neighbor
        isource,idest = self.cartComm.Shift(0,+1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received right buffer to the left overlap cells
        if (isource!=MPI.PROC_NULL):
            A[1*no:2*no,:,:] += self.to_device(recvbuf)

        # Clean up
        del recvbuf        
        
        
    # --------------------------------------------
    # Communicate overlap cells in the y-direction
    def communicate_border_y(self,A,n1,n2,n3,no):
        # Lower buffer
        sendbuf = self.from_device(A.detach()[:,no:2*no,:].contiguous())
        recvbuf = torch.empty_like(sendbuf)
        
        # Send lower buffer to lower neighbor
        isource,idest = self.cartComm.Shift(1,-1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received lower buffer to the upper overlap cells
        if (isource!=MPI.PROC_NULL):
            A[:,n2-no:n2,:].copy_(self.to_device(recvbuf))

        # Upper buffer
        sendbuf = self.from_device(A.detach()[:,n2-2*no:n2-no,:].contiguous())
        
        # Send upper buffer to upper neighbor
        isource,idest = self.cartComm.Shift(1,+1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received upper buffer to the lower overlap cells
        if (isource!=MPI.PROC_NULL):
            A[:,0:no,:].copy_(self.to_device(recvbuf))

        # Clean up
        del recvbuf

        
    # --------------------------------------------
    # Communicate overlap cells in the y-direction
    def communicate_border_y_ADJOINT(self,A,n1,n2,n3,no):
        # Lower buffer
        sendbuf = self.from_device(A[:,0*no:1*no,:].contiguous())
        recvbuf = torch.empty_like(sendbuf)
        
        # Send lower buffer to lower neighbor
        isource,idest = self.cartComm.Shift(1,-1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received lower buffer to the upper overlap cells
        if (isource!=MPI.PROC_NULL):
            A[:,-2*no:-1*no,:] += self.to_device(recvbuf)

        # Upper buffer
        sendbuf = self.from_device(A[:,-1*no:,:].contiguous())
        recvbuf = torch.empty_like(sendbuf)
        
        # Send upper buffer to upper neighbor
        isource,idest = self.cartComm.Shift(1,+1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received upper buffer to the lower overlap cells
        if (isource!=MPI.PROC_NULL):
            A[:,1*no:2*no,:] += self.to_device(recvbuf)

        # Clean up
        del recvbuf
        
        
    # --------------------------------------------
    # Communicate overlap cells in the z-direction
    def communicate_border_z(self,A,n1,n2,n3,no):
        # Front buffer
        sendbuf = self.from_device(A[:,:,no:2*no].contiguous())
        recvbuf = torch.empty_like(sendbuf)
        
        # Send front buffer to front neighbor
        isource,idest = self.cartComm.Shift(2,-1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received front buffer to the back overlap cells
        if (isource!=MPI.PROC_NULL):
            A[:,:,n3-no:n3].copy_(self.to_device(recvbuf))

        # Back buffer
        sendbuf = self.from_device(A[:,:,n3-2*no:n3-no].contiguous())
        
        # Send back buffer to back neighbor
        isource,idest = self.cartComm.Shift(2,+1)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self.cartComm.Sendrecv(sendbuf,idest,0,recvbuf,isource,0)

        # Copy the received back buffer to the front overlap cells
        if (isource!=MPI.PROC_NULL):
            A[:,:,0:no].copy_(self.to_device(recvbuf))

        # Clean up
        del recvbuf
