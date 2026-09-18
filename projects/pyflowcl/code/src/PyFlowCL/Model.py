"""
------------------------------------------------------------------------
PyFlowCL: A Python-native, compressible Navier-Stokes solver for
curvilinear grids
------------------------------------------------------------------------

@file Model.py

"""

__copyright__ = """
Copyright (c) 2022 University of Notre Dame
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


import torch
import torch.nn as nn

class NeuralNetworkModel_ELU(nn.Module):
    def __init__(self, H, num_inputs, num_outputs, C_out, alpha=1.0):
        super(NeuralNetworkModel_ELU, self).__init__()
        
        self.fc1 = nn.Linear(num_inputs, H).type(torch.DoubleTensor)
        self.fcG = nn.Linear(num_inputs, H).type(torch.DoubleTensor)
        
        self.fc2 = nn.Linear(H, H).type(torch.DoubleTensor)
        self.fc4 = nn.Linear(H, num_outputs).type(torch.DoubleTensor)
        
        self.C_out = C_out
        self.alpha = alpha
        
    def forward(self, x):
        
        L1 =  self.fc1( x ) 
        
        #H1 = torch.relu( L1 )
        H1 = torch.relu(L1) - torch.relu(- self.alpha*( torch.exp(L1) - 1) )
        
        L2 = self.fc2( H1 ) 
        
        #H2 = torch.relu(L2 )
        H2 = torch.relu(L2) - torch.relu(- self.alpha*( torch.exp(L2) - 1) )
        
        L3 =  self.fcG( x ) 
        G = torch.sigmoid(L3)
        

        H2_G = G*H2
        
        f_out = self.C_out*self.fc4( H2_G )
        
        return f_out    
