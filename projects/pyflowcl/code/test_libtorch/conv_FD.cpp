#include <torch/torch.h>
#include <iostream>
using namespace torch::indexing;

#define pi 3.141592653589793238462643383279502884


void RHS( torch::Tensor u,
	  torch::Tensor udot,
	  torch::Tensor x_xi,
	  torch::Tensor y_xi,
	  torch::Tensor x_eta,
	  torch::Tensor y_eta,
	  torch::Tensor inv_Jac,
	  double d_xi, double d_eta) {

  // Grid size
  int Nx = 512;
  int Ny = 512;
  
  // Convective velocities
  double cx = 1.0;
  double cy = 1.0;
  
  torch::Tensor E = ( cx * y_eta - cy * x_eta ) * u;

  torch::Tensor xl = torch::cat({ E.index({Slice(Nx-1,Nx), Slice(0,Ny)}),
				  E.index({Slice(0, Nx-1), Slice(0,Ny)}) }, 0);

  torch::Tensor xr = torch::cat({ E.index({Slice(1,Nx), Slice(0,Ny)}),
				  E.index({Slice(0, 1), Slice(0,Ny)}) }, 0);

  torch::Tensor xi_term = -( xr - xl ) / (2.0*d_xi);

  
  E = ( cy * x_xi  - cx * y_xi  ) * u;

  xl = torch::cat({ E.index({ Slice(0,Nx), Slice(Ny-1,Ny) }) ,
		    E.index({ Slice(0,Nx), Slice(0, Ny-1) }) }, 1);

  xr = torch::cat({ E.index({ Slice(0,Nx), Slice(1,Ny) }) ,
		    E.index({ Slice(0,Nx), Slice(0, 1) }) }, 1);

  torch::Tensor eta_term = -( xr - xl ) / (2.0*d_eta);

  udot = inv_Jac * (xi_term + eta_term);
}


double get_energy( torch::Tensor u ) {
  return torch::sum( u*u ).item().to<double>();
}
  

int main() {
  //torch::Tensor tensor = torch::rand({2, 3});
  //std::cout << tensor << std::endl;

  // Grid size
  int Nx = 512;
  int Ny = 512;

  // Sopping condition
  int Nsteps = 2000;
  double dt  = 1e-3;

  auto options =
    torch::TensorOptions()
    .dtype(torch::kFloat64)
    .layout(torch::kStrided);
    //.device(torch::kCUDA, 1)
    //.requires_grad(true);

  // ----------------------------------------------------
  // Grid
  double eta_min = 0.25;
  double eta_max = 4.0;

  torch::Tensor xi_grid  = torch::linspace(0, 2.0*pi, Nx+1, options);
  torch::Tensor eta_grid = torch::linspace(eta_min, eta_max, Ny+1, options);

  double d_xi  = 2.0*pi/(float) Nx;
  double d_eta = (eta_max - eta_min)/(float) Ny;

  std::vector<torch::Tensor> Grid = torch::meshgrid({ xi_grid.index({Slice(0,Nx)}),
						      eta_grid.index({Slice(0,Ny)}) });
  torch::Tensor Xi  = Grid[0];
  torch::Tensor Eta = Grid[1];
  
  torch::Tensor x_xi  = -Eta * torch::sin(Xi);
  torch::Tensor y_xi  = -Eta * torch::cos(Xi);
  torch::Tensor x_eta = torch::cos(Xi);
  torch::Tensor y_eta = torch::sin(Xi);

  torch::Tensor inv_Jac = 1.0/(x_xi * y_eta - x_eta * y_xi);

  torch::Tensor X = Eta * torch::cos(Xi);
  torch::Tensor Y = Eta * torch::sin(Xi);
  //std::cout << Y.dtype() << std::endl; // double

  // ----------------------------------------------------
  // Initial condition
  torch::Tensor U = torch::zeros({Nx,Ny}, options);
  //std::cout << U.dtype() << std::endl; // double

  double xloc = -2.0;
  double yloc = 0.0;
  
  for (int i=0; i<Nx; i++) {
    for (int j=0; j<Ny; j++) {
      double x = X[i][j].item().to<double>();
      double y = Y[i][j].item().to<double>();
      if (std::abs(x - xloc)<=1.0 &&
	  std::abs(y - yloc)<=1.0) {
	U[i][j] = ( std::exp(1.0 / (std::pow(x - xloc,2) - 1.0)) *
		    std::exp(1.0 / (std::pow(y - yloc,2) - 1.0)) );
      }
    }
  }

  double energy_IC = get_energy(U);

  // ----------------------------------------------------
  // Time stepping
  double t = 0.0;
  torch::Tensor K1 = torch::zeros({Nx,Ny}, options);
  torch::Tensor K2 = torch::zeros({Nx,Ny}, options);
  torch::Tensor K3 = torch::zeros({Nx,Ny}, options);
  torch::Tensor K4 = torch::zeros({Nx,Ny}, options);
  
  for (int n=0; n<Nsteps; n++) {

    if (n%50==0) {std::cout << n << '\t'
			    << get_energy(U) / energy_IC
			    << std::endl;}

    // RK4
    RHS( U, K1, x_xi, y_xi, x_eta, y_eta, inv_Jac, d_xi, d_eta );
    RHS( U + 0.5*dt*K1, K2, x_xi, y_xi, x_eta, y_eta, inv_Jac, d_xi, d_eta );
    RHS( U + 0.5*dt*K2, K3, x_xi, y_xi, x_eta, y_eta, inv_Jac, d_xi, d_eta );
    RHS( U + dt*K3, K4, x_xi, y_xi, x_eta, y_eta, inv_Jac, d_xi, d_eta );

    U = U + dt*(K1 + 2.0*(K2 + K3) + K4)/6.0;

    t += dt;
    
  }

}
