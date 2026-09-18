"""
.. autoclass:: Thermochemistry
"""


import numpy as np
import torch


class Thermochemistry:
    """
    .. attribute:: model_name
    .. attribute:: num_elements
    .. attribute:: num_species
    .. attribute:: num_reactions
    .. attribute:: num_falloff
    .. attribute:: one_atm

        Returns 1 atm in SI units of pressure (Pa).

    .. attribute:: gas_constant
    .. attribute:: species_names
    .. attribute:: species_indices

    .. automethod:: get_specific_gas_constant
    .. automethod:: get_density
    .. automethod:: get_pressure
    .. automethod:: get_mix_molecular_weight
    .. automethod:: get_concentrations
    .. automethod:: get_mixture_specific_heat_cp_mass
    .. automethod:: get_mixture_specific_heat_cv_mass
    .. automethod:: get_mixture_enthalpy_mass
    .. automethod:: get_mixture_internal_energy_mass
    .. automethod:: get_species_specific_heats_r
    .. automethod:: get_species_enthalpies_rt
    .. automethod:: get_species_entropies_r
    .. automethod:: get_species_gibbs_rt
    .. automethod:: get_equilibrium_constants
    .. automethod:: get_temperature
    .. automethod:: __init__
    """

    def __init__(self, usr_np=np):
        """Initialize thermochemistry object for a mechanism.

        Parameters
        ----------
        usr_np
            :mod:`numpy`-like namespace providing at least the following functions,
            for any array ``X`` of the bulk array type:

            - ``usr_np.log(X)`` (like :data:`numpy.log`)
            - ``usr_np.log10(X)`` (like :data:`numpy.log10`)
            - ``usr_np.exp(X)`` (like :data:`numpy.exp`)
            - ``usr_np.where(X > 0, X_yes, X_no)`` (like :func:`numpy.where`)
            - ``usr_np.linalg.norm(X, np.inf)`` (like :func:`numpy.linalg.norm`)

            where the "bulk array type" is a type that offers arithmetic analogous
            to :class:`numpy.ndarray` and is used to hold all types of (potentialy
            volumetric) "bulk data", such as temperature, pressure, mass fractions,
            etc. This parameter defaults to *actual numpy*, so it can be ignored
            unless it is needed by the user (e.g. for purposes of
            GPU processing or automatic differentiation).

        """

        self.usr_np = usr_np
        self.model_name = 'sanDiego.xml'
        self.num_elements = 3
        self.num_species = 9
        self.num_reactions = 24
        self.num_falloff = 2

        self.one_atm = 101325.0
        self.gas_constant = 8314.46261815324
        self.big_number = 1.0e300

        self.species_names = ['H2', 'O2', 'H', 'H2O', 'HO2', 'H2O2', 'O', 'OH', 'N2']
        self.species_indices = {'H2': 0, 'O2': 1, 'H': 2, 'H2O': 3, 'HO2': 4, 'H2O2': 5, 'O': 6, 'OH': 7, 'N2': 8}

        #self.wts = np.array([2.016, 31.998, 1.008, 18.015, 33.006, 34.014, 15.999, 17.007, 28.014])

        self.wts = self._pyro_make_tensor([2.016, 31.998, 1.008, 18.015, 33.006, 34.014, 15.999, 17.007, 28.014])
        self.iwts = 1/self.wts

    def _pyro_zeros_like(self, argument):
        # FIXME: This is imperfect, as a NaN will stay a NaN.
        return 0 * argument

    def _pyro_make_tensor(self, res_list):
        if self.usr_np is torch:
            if torch.is_tensor(res_list[0]):
                for i,val in enumerate(res_list):
                    res_list[i] = val#.squeeze()
                return torch.stack(res_list, 0)
            else:
                return self.usr_np.tensor(res_list, dtype=torch.float64)
        else:
            return self.usr_np.array(res_list)

    def _pyro_make_array(self, res_list):
        """This works around (e.g.) numpy.exp not working with object
        arrays of numpy scalars. It defaults to making object arrays, however
        if an array consists of all scalars, it makes a "plain old"
        :class:`numpy.ndarray`.

        See ``this numpy bug <https://github.com/numpy/numpy/issues/18004>`__
        for more context.
        """

        from numbers import Number
        all_numbers = all(isinstance(e, Number) for e in res_list)

        dtype = np.float64 if all_numbers else object
        result = np.empty((len(res_list),), dtype=dtype)

        # 'result[:] = res_list' may look tempting, however:
        # https://github.com/numpy/numpy/issues/16564
        for idx in range(len(res_list)):
            result[idx] = res_list[idx]

        return result

    def _pyro_norm(self, argument, normord):
        """This works around numpy.linalg norm not working with scalars.

        If the argument is a regular ole number, it uses :func:`numpy.abs`,
        otherwise it uses ``usr_np.linalg.norm``.
        """
        # Wrap norm for scalars

        from numbers import Number

        if isinstance(argument, Number):
            return np.abs(argument)
        return self.usr_np.linalg.norm(argument.squeeze(), normord) # JFM moved .squeeze here from _pyro_make_tensor

    def species_name(self, species_index):
        return self.species_name[species_index]

    def species_index(self, species_name):
        return self.species_indices[species_name]

    def get_specific_gas_constant(self, mass_fractions):
        return self.gas_constant * (
                    + self.iwts[0]*mass_fractions[0]
                    + self.iwts[1]*mass_fractions[1]
                    + self.iwts[2]*mass_fractions[2]
                    + self.iwts[3]*mass_fractions[3]
                    + self.iwts[4]*mass_fractions[4]
                    + self.iwts[5]*mass_fractions[5]
                    + self.iwts[6]*mass_fractions[6]
                    + self.iwts[7]*mass_fractions[7]
                    + self.iwts[8]*mass_fractions[8]
                )

    def get_density(self, p, temperature, mass_fractions):
        mmw = self.get_mix_molecular_weight(mass_fractions)
        rt = self.gas_constant * temperature
        return p * mmw / rt

    def get_pressure(self, rho, temperature, mass_fractions):
        mmw = self.get_mix_molecular_weight(mass_fractions)
        rt = self.gas_constant * temperature
        return rho * rt / mmw

    def get_mix_molecular_weight(self, mass_fractions):
        return 1/(
                    + self.iwts[0]*mass_fractions[0]
                    + self.iwts[1]*mass_fractions[1]
                    + self.iwts[2]*mass_fractions[2]
                    + self.iwts[3]*mass_fractions[3]
                    + self.iwts[4]*mass_fractions[4]
                    + self.iwts[5]*mass_fractions[5]
                    + self.iwts[6]*mass_fractions[6]
                    + self.iwts[7]*mass_fractions[7]
                    + self.iwts[8]*mass_fractions[8]
                )

    def get_concentrations(self, rho, mass_fractions):
        #return self.iwts * rho * mass_fractions
        return self._pyro_make_tensor([
                    self.iwts[0]*mass_fractions[0]*rho,
                    self.iwts[1]*mass_fractions[1]*rho,
                    self.iwts[2]*mass_fractions[2]*rho,
                    self.iwts[3]*mass_fractions[3]*rho,
                    self.iwts[4]*mass_fractions[4]*rho,
                    self.iwts[5]*mass_fractions[5]*rho,
                    self.iwts[6]*mass_fractions[6]*rho,
                    self.iwts[7]*mass_fractions[7]*rho,
                    self.iwts[8]*mass_fractions[8]*rho,
                ])

    def get_mass_average_property(self, mass_fractions, spec_property):
        return sum([mass_fractions[i] * spec_property[i] * self.iwts[i]
                    for i in range(self.num_species)])

    def get_mixture_specific_heat_cp_mass(self, temperature, mass_fractions):
        cp0_r = self.get_species_specific_heats_r(temperature)
        cpmix = self.get_mass_average_property(mass_fractions, cp0_r)
        return self.gas_constant * cpmix

    def get_mixture_specific_heat_cv_mass(self, temperature, mass_fractions):
        cp0_r = self.get_species_specific_heats_r(temperature) - 1.0
        cpmix = self.get_mass_average_property(mass_fractions, cp0_r)
        return self.gas_constant * cpmix

    def get_mixture_enthalpy_mass(self, temperature, mass_fractions):
        h0_rt = self.get_species_enthalpies_rt(temperature)
        hmix = self.get_mass_average_property(mass_fractions, h0_rt)
        return self.gas_constant * temperature * hmix

    def get_mixture_internal_energy_mass(self, temperature, mass_fractions):
        e0_rt = self.get_species_enthalpies_rt(temperature) - 1.0
        emix = self.get_mass_average_property(mass_fractions, e0_rt)
        return self.gas_constant * temperature * emix

    def get_species_specific_heats_r(self, temperature):
        return self._pyro_make_tensor([
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.867760513712 + 0.0009294189291*temperature + -1.920924856e-07*temperature**2 + 2.397521038e-11*temperature**3 + -1.269507592e-15*temperature**4, 2.34433112 + 0.00798052075*temperature + -1.9478151e-05*temperature**2 + 2.01572094e-08*temperature**3 + -7.37611761e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 3.735968259520498 + 0.0005252429024*temperature + -6.820135211e-08*temperature**2 + 2.112706159e-12*temperature**3 + 3.349740305e-16*temperature**4, 3.78245636 + -0.00299673416*temperature + 9.84730201e-06*temperature**2 + -9.68129509e-09*temperature**3 + 3.24372837e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.500000000082495 + 2.41879982e-18*temperature + -6.163990319e-22*temperature**2 + 9.904620798e-27*temperature**3 + 5.494102931e-30*temperature**4, 2.5 + 7.05332819e-13*temperature + -1.99591964e-15*temperature**2 + 2.30081632e-18*temperature**3 + -9.27732332e-22*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.758944166939999 + 0.002888397014*temperature + -7.728263523e-07*temperature**2 + 9.661400569e-11*temperature**3 + -4.51271433e-15*temperature**4, 4.19864056 + -0.0020364341*temperature + 6.52040211e-06*temperature**2 + -5.48797062e-09*temperature**3 + 1.77197817e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 4.117224508773001 + 0.002044628613*temperature + -4.834400118e-07*temperature**2 + 5.039817467e-11*temperature**3 + -1.982844643e-15*temperature**4, 4.30179801 + -0.00474912051*temperature + 2.11582891e-05*temperature**2 + -2.42763894e-08*temperature**3 + 9.29225124e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 4.16500285 + 0.00490831694*temperature + -1.90139225e-06*temperature**2 + 3.71185986e-10*temperature**3 + -2.87908305e-14*temperature**4, 4.27611269 + -0.000542822417*temperature + 1.67335701e-05*temperature**2 + -2.15770813e-08*temperature**3 + 8.62454363e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.5664423701285 + -6.776623334e-05*temperature + 1.785202407e-08*temperature**2 + 2.069683358e-13*temperature**3 + -1.294391943e-16*temperature**4, 3.1682671 + -0.00327931884*temperature + 6.64306396e-06*temperature**2 + -6.12806624e-09*temperature**3 + 2.11265971e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.823004358414999 + 0.001120771631*temperature + -2.859676704e-07*temperature**2 + 3.514630128e-11*temperature**3 + -1.614130295e-15*temperature**4, 4.12530561 + -0.00322544939*temperature + 6.52764691e-06*temperature**2 + -5.79853643e-09*temperature**3 + 2.06237379e-12*temperature**4),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 3.161755501687001 + 0.001063279969*temperature + -3.280799873e-07*temperature**2 + 4.572775106e-11*temperature**3 + -2.326834447e-15*temperature**4, 3.298677 + 0.0014082404*temperature + -3.963222e-06*temperature**2 + 5.641515e-09*temperature**3 + -2.444854e-12*temperature**4),
                ])

    def get_species_enthalpies_rt(self, temperature):
        return self._pyro_make_tensor([
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.867760513712 + 0.00046470946455*temperature + -6.403082853333334e-08*temperature**2 + 5.993802595e-12*temperature**3 + -2.5390151840000003e-16*temperature**4 + -786.160900805267 / temperature, 2.34433112 + 0.003990260375*temperature + -6.4927169999999995e-06*temperature**2 + 5.03930235e-09*temperature**3 + -1.4752235220000002e-12*temperature**4 + -917.935173 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 3.735968259520498 + 0.0002626214512*temperature + -2.2733784036666664e-08*temperature**2 + 5.2817653975e-13*temperature**3 + 6.69948061e-17*temperature**4 + -1245.449473196348 / temperature, 3.78245636 + -0.00149836708*temperature + 3.282434003333333e-06*temperature**2 + -2.4203237725e-09*temperature**3 + 6.48745674e-13*temperature**4 + -1063.94356 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.500000000082495 + 1.20939991e-18*temperature + -2.0546634396666666e-22*temperature**2 + 2.4761551995e-27*temperature**3 + 1.0988205862000001e-30*temperature**4 + 25473.65989999452 / temperature, 2.5 + 3.526664095e-13*temperature + -6.653065466666667e-16*temperature**2 + 5.7520408e-19*temperature**3 + -1.855464664e-22*temperature**4 + 25473.6599 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.758944166939999 + 0.001444198507*temperature + -2.576087841e-07*temperature**2 + 2.41535014225e-11*temperature**3 + -9.02542866e-16*temperature**4 + -29926.2176893965 / temperature, 4.19864056 + -0.00101821705*temperature + 2.17346737e-06*temperature**2 + -1.371992655e-09*temperature**3 + 3.54395634e-13*temperature**4 + -30293.7267 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 4.117224508773001 + 0.0010223143065*temperature + -1.6114667060000002e-07*temperature**2 + 1.25995436675e-11*temperature**3 + -3.9656892859999997e-16*temperature**4 + 73.56660692143204 / temperature, 4.30179801 + -0.002374560255*temperature + 7.0527630333333326e-06*temperature**2 + -6.06909735e-09*temperature**3 + 1.8584502480000002e-12*temperature**4 + 294.80804 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 4.16500285 + 0.00245415847*temperature + -6.337974166666666e-07*temperature**2 + 9.27964965e-11*temperature**3 + -5.7581661e-15*temperature**4 + -17861.7877 / temperature, 4.27611269 + -0.0002714112085*temperature + 5.5778567000000005e-06*temperature**2 + -5.394270325e-09*temperature**3 + 1.724908726e-12*temperature**4 + -17702.5821 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.5664423701285 + -3.388311667e-05*temperature + 5.9506746900000005e-09*temperature**2 + 5.174208395e-14*temperature**3 + -2.5887838859999998e-17*temperature**4 + 29217.20113293974 / temperature, 3.1682671 + -0.00163965942*temperature + 2.2143546533333334e-06*temperature**2 + -1.53201656e-09*temperature**3 + 4.22531942e-13*temperature**4 + 29122.2592 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.823004358414999 + 0.0005603858155*temperature + -9.53225568e-08*temperature**2 + 8.78657532e-12*temperature**3 + -3.22826059e-16*temperature**4 + 3736.310622457334 / temperature, 4.12530561 + -0.001612724695*temperature + 2.1758823033333334e-06*temperature**2 + -1.4496341075e-09*temperature**3 + 4.1247475799999997e-13*temperature**4 + 3381.53812 / temperature),
            self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 3.161755501687001 + 0.0005316399845*temperature + -1.0935999576666666e-07*temperature**2 + 1.1431937765e-11*temperature**3 + -4.653668894e-16*temperature**4 + -1012.770811295934 / temperature, 3.298677 + 0.0007041202*temperature + -1.3210739999999999e-06*temperature**2 + 1.41037875e-09*temperature**3 + -4.889707999999999e-13*temperature**4 + -1020.8999 / temperature),
                ])

    def get_species_entropies_r(self, temperature):
        return self._pyro_make_tensor([
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.867760513712*self.usr_np.log(temperature) + 0.0009294189291*temperature + -9.60462428e-08*temperature**2 + 7.991736793333334e-12*temperature**3 + -3.17376898e-16*temperature**4 + -0.6572733182838171, 2.34433112*self.usr_np.log(temperature) + 0.00798052075*temperature + -9.7390755e-06*temperature**2 + 6.7190698e-09*temperature**3 + -1.8440294025e-12*temperature**4 + 0.683010238),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 3.735968259520498*self.usr_np.log(temperature) + 0.0005252429024*temperature + -3.4100676055e-08*temperature**2 + 7.042353863333333e-13*temperature**3 + 8.3743507625e-17*temperature**4 + 2.997624520424838, 3.78245636*self.usr_np.log(temperature) + -0.00299673416*temperature + 4.923651005e-06*temperature**2 + -3.2270983633333334e-09*temperature**3 + 8.109320925e-13*temperature**4 + 3.65767573),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.500000000082495*self.usr_np.log(temperature) + 2.41879982e-18*temperature + -3.0819951595e-22*temperature**2 + 3.301540266e-27*temperature**3 + 1.37352573275e-30*temperature**4 + -0.4466828533274811, 2.5*self.usr_np.log(temperature) + 7.05332819e-13*temperature + -9.9795982e-16*temperature**2 + 7.669387733333333e-19*temperature**3 + -2.31933083e-22*temperature**4 + -0.446682853),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.758944166939999*self.usr_np.log(temperature) + 0.002888397014*temperature + -3.8641317615e-07*temperature**2 + 3.2204668563333335e-11*temperature**3 + -1.1281785825e-15*temperature**4 + 6.40041578096093, 4.19864056*self.usr_np.log(temperature) + -0.0020364341*temperature + 3.260201055e-06*temperature**2 + -1.82932354e-09*temperature**3 + 4.429945425e-13*temperature**4 + -0.849032208),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 4.117224508773001*self.usr_np.log(temperature) + 0.002044628613*temperature + -2.417200059e-07*temperature**2 + 1.6799391556666667e-11*temperature**3 + -4.9571116075e-16*temperature**4 + 3.233395789965101, 4.30179801*self.usr_np.log(temperature) + -0.00474912051*temperature + 1.057914455e-05*temperature**2 + -8.0921298e-09*temperature**3 + 2.32306281e-12*temperature**4 + 3.71666245),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 4.16500285*self.usr_np.log(temperature) + 0.00490831694*temperature + -9.50696125e-07*temperature**2 + 1.2372866199999999e-10*temperature**3 + -7.197707625e-15*temperature**4 + 2.91615662, 4.27611269*self.usr_np.log(temperature) + -0.000542822417*temperature + 8.36678505e-06*temperature**2 + -7.192360433333333e-09*temperature**3 + 2.1561359075e-12*temperature**4 + 3.43505074),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.5664423701285*self.usr_np.log(temperature) + -6.776623334e-05*temperature + 8.926012035e-09*temperature**2 + 6.898944526666666e-14*temperature**3 + -3.2359798575e-17*temperature**4 + 4.795684327283496, 3.1682671*self.usr_np.log(temperature) + -0.00327931884*temperature + 3.32153198e-06*temperature**2 + -2.0426887466666666e-09*temperature**3 + 5.281649275e-13*temperature**4 + 2.05193346),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 2.823004358414999*self.usr_np.log(temperature) + 0.001120771631*temperature + -1.429838352e-07*temperature**2 + 1.171543376e-11*temperature**3 + -4.0353257375e-16*temperature**4 + 5.937567724308418, 4.12530561*self.usr_np.log(temperature) + -0.00322544939*temperature + 3.263823455e-06*temperature**2 + -1.9328454766666666e-09*temperature**3 + 5.155934475e-13*temperature**4 + -0.69043296),
                self.usr_np.where(self.usr_np.greater(temperature, 1000.0), 3.161755501687001*self.usr_np.log(temperature) + 0.001063279969*temperature + -1.6403999365e-07*temperature**2 + 1.5242583686666665e-11*temperature**3 + -5.8170861175e-16*temperature**4 + 4.678212252352846, 3.298677*self.usr_np.log(temperature) + 0.0014082404*temperature + -1.981611e-06*temperature**2 + 1.8805050000000002e-09*temperature**3 + -6.112135e-13*temperature**4 + 3.950372),
                ])

    def get_species_gibbs_rt(self, temperature):
        h0_rt = self.get_species_enthalpies_rt(temperature)
        s0_r = self.get_species_entropies_r(temperature)
        return h0_rt - s0_r

    def get_equilibrium_constants(self, temperature):
        rt = self.gas_constant * temperature
        c0 = self.usr_np.log(self.one_atm / rt)

        g0_rt = self.get_species_gibbs_rt(temperature)
        return self._pyro_make_tensor([
                    g0_rt[6] + g0_rt[7] + -1*(g0_rt[2] + g0_rt[1]),
                    g0_rt[2] + g0_rt[7] + -1*(g0_rt[0] + g0_rt[6]),
                    g0_rt[2] + g0_rt[3] + -1*(g0_rt[0] + g0_rt[7]),
                    2.0*g0_rt[7] + -1*(g0_rt[3] + g0_rt[6]),
                    g0_rt[0] + -1*2.0*g0_rt[2] + -1*-1.0*c0,
                    g0_rt[3] + -1*(g0_rt[2] + g0_rt[7]) + -1*-1.0*c0,
                    g0_rt[1] + -1*2.0*g0_rt[6] + -1*-1.0*c0,
                    g0_rt[7] + -1*(g0_rt[2] + g0_rt[6]) + -1*-1.0*c0,
                    g0_rt[4] + -1*(g0_rt[6] + g0_rt[7]) + -1*-1.0*c0,
                    g0_rt[4] + -1*(g0_rt[2] + g0_rt[1]) + -1*-1.0*c0,
                    2.0*g0_rt[7] + -1*(g0_rt[2] + g0_rt[4]),
                    g0_rt[0] + g0_rt[1] + -1*(g0_rt[2] + g0_rt[4]),
                    g0_rt[3] + g0_rt[6] + -1*(g0_rt[2] + g0_rt[4]),
                    g0_rt[1] + g0_rt[7] + -1*(g0_rt[4] + g0_rt[6]),
                    g0_rt[3] + g0_rt[1] + -1*(g0_rt[4] + g0_rt[7]),
                    g0_rt[3] + g0_rt[1] + -1*(g0_rt[4] + g0_rt[7]),
                    g0_rt[5] + -1*2.0*g0_rt[7] + -1*-1.0*c0,
                    g0_rt[5] + g0_rt[1] + -1*2.0*g0_rt[4],
                    g0_rt[5] + g0_rt[1] + -1*2.0*g0_rt[4],
                    g0_rt[0] + g0_rt[4] + -1*(g0_rt[2] + g0_rt[5]),
                    g0_rt[3] + g0_rt[7] + -1*(g0_rt[2] + g0_rt[5]),
                    g0_rt[3] + g0_rt[4] + -1*(g0_rt[5] + g0_rt[7]),
                    g0_rt[3] + g0_rt[4] + -1*(g0_rt[5] + g0_rt[7]),
                    g0_rt[4] + g0_rt[7] + -1*(g0_rt[5] + g0_rt[6]),
                ])

    def get_temperature(self, enthalpy_or_energy, t_guess, y, do_energy=False):
        if do_energy is False:
            pv_fun = self.get_mixture_specific_heat_cp_mass
            he_fun = self.get_mixture_enthalpy_mass
        else:
            pv_fun = self.get_mixture_specific_heat_cv_mass
            he_fun = self.get_mixture_internal_energy_mass

        num_iter = 500
        tol = 1.0e-6
        ones = self._pyro_zeros_like(enthalpy_or_energy) + 1.0
        t_i = t_guess * ones

        for _ in range(num_iter):
            f = enthalpy_or_energy - he_fun(t_i, y)
            j = -pv_fun(t_i, y)
            dt = -f / j
            t_i += dt
            if self._pyro_norm(dt, np.inf) < tol:
                return t_i

        raise RuntimeError("Temperature iteration failed to converge")

    def get_falloff_rates(self, temperature, concentrations, k_fwd):
        ones = self._pyro_zeros_like(temperature) + 1.0
        k_high = self._pyro_make_tensor([
            4650000000.0*temperature**0.44,
            95500000000.0*temperature**-0.27,
                ])

        k_low = self._pyro_make_tensor([
            57500000000000.0*temperature**-1.4,
            2.76e+19*temperature**-3.2,
                ])

        reduced_pressure = self._pyro_make_tensor([
            (2.5*concentrations[0] + 16.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])*k_low[0]/k_high[0],
            (2.5*concentrations[0] + 6.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])*k_low[1]/k_high[1],
                            ])

        falloff_center = self._pyro_make_tensor([
            self.usr_np.log10(0.5*self.usr_np.exp((-1*temperature) / 1e-30) + 0.5*self.usr_np.exp((-1*temperature) / 1.0000000000000002e+30) + self.usr_np.exp(-1e+90 / temperature)),
            self.usr_np.log10(0.43000000000000005*self.usr_np.exp((-1*temperature) / 1.0000000000000002e+30) + 0.57*self.usr_np.exp((-1*temperature) / 1e-30) + self.usr_np.exp(-1e+90 / temperature)),
                        ])

        falloff_function = self._pyro_make_tensor([
            10**(falloff_center[0] / (1 + ((self.usr_np.log10(reduced_pressure[0]) + -0.4 + -1*0.67*falloff_center[0]) / (0.75 + -1*1.27*falloff_center[0] + -1*0.14*(self.usr_np.log10(reduced_pressure[0]) + -0.4 + -1*0.67*falloff_center[0])))**2)),
            10**(falloff_center[1] / (1 + ((self.usr_np.log10(reduced_pressure[1]) + -0.4 + -1*0.67*falloff_center[1]) / (0.75 + -1*1.27*falloff_center[1] + -1*0.14*(self.usr_np.log10(reduced_pressure[1]) + -0.4 + -1*0.67*falloff_center[1])))**2)),
                            ])*reduced_pressure/(1+reduced_pressure)

        k_fwd[9] = k_high[0]*falloff_function[0]*ones
        k_fwd[16] = k_high[1]*falloff_function[1]*ones
        return

    def get_fwd_rate_coefficients(self, temperature, concentrations):
        ones = self._pyro_zeros_like(temperature) + 1.0
        k_fwd = self._pyro_make_tensor([
            self.usr_np.exp(31.192067198532598 + -0.7*self.usr_np.log(temperature) + -1*(8589.851597151493 / temperature)) * ones,
            self.usr_np.exp(3.92395157629342 + 2.67*self.usr_np.log(temperature) + -1*(3165.568384724549 / temperature)) * ones,
            self.usr_np.exp(13.972514306773938 + 1.3*self.usr_np.log(temperature) + -1*(1829.342520199863 / temperature)) * ones,
            self.usr_np.exp(6.551080335043404 + 2.33*self.usr_np.log(temperature) + -1*(7320.978251450734 / temperature)) * ones,
            1300000000000.0*temperature**-1.0 * ones,
            4e+16*temperature**-2.0 * ones,
            6170000000.0*temperature**-0.5 * ones,
            4710000000000.0*temperature**-1.0 * ones,
            8000000000.0 * ones,
            0*temperature,
            self.usr_np.exp(24.983124837646084 + -1*(148.41608612272393 / temperature)) * ones,
            self.usr_np.exp(23.532668532308907 + -1*(414.09771841210573 / temperature)) * ones,
            self.usr_np.exp(24.157253041431556 + -1*(865.9609563076275 / temperature)) * ones,
            20000000000.0 * ones,
            self.usr_np.exp(26.832513419710775 + -1*(5500.054796103862 / temperature)) * ones,
            self.usr_np.exp(24.087107432064798 + -1*(-249.66135459769072 / temperature)) * ones,
            0*temperature,
            self.usr_np.exp(19.083368717027604 + -1*(-709.00553297687 / temperature)) * ones,
            self.usr_np.exp(25.357994825176046 + -1*(5556.582802973943 / temperature)) * ones,
            self.usr_np.exp(23.85876005287556 + -1*(4000.619345786196 / temperature)) * ones,
            self.usr_np.exp(23.025850929940457 + -1*(1804.0853256408905 / temperature)) * ones,
            self.usr_np.exp(25.052682521347997 + -1*(3659.8877639501534 / temperature)) * ones,
            self.usr_np.exp(21.27715095017285 + -1*(159.96223220682563 / temperature)) * ones,
            self.usr_np.exp(9.172638504792172 + 2.0*self.usr_np.log(temperature) + -1*(2008.5483292135248 / temperature)) * ones,
                ])
        self.get_falloff_rates(temperature, concentrations, k_fwd)

        k_fwd[4] *= (2.5*concentrations[0] + 12.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])
        k_fwd[5] *= (2.5*concentrations[0] + 12.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])
        k_fwd[6] *= (2.5*concentrations[0] + 12.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])
        k_fwd[7] *= (2.5*concentrations[0] + 12.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])
        k_fwd[8] *= (2.5*concentrations[0] + 12.0*concentrations[3] + concentrations[1] + concentrations[2] + concentrations[4] + concentrations[5] + concentrations[6] + concentrations[7] + concentrations[8])
        return k_fwd

    def get_net_rates_of_progress(self, temperature, concentrations):
        k_fwd = self.get_fwd_rate_coefficients(temperature, concentrations)
        log_k_eq = self.get_equilibrium_constants(temperature)
        return self._pyro_make_tensor([
                    k_fwd[0]*(concentrations[2]*concentrations[1] + -1*self.usr_np.exp(log_k_eq[0])*concentrations[6]*concentrations[7]),
                    k_fwd[1]*(concentrations[0]*concentrations[6] + -1*self.usr_np.exp(log_k_eq[1])*concentrations[2]*concentrations[7]),
                    k_fwd[2]*(concentrations[0]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[2])*concentrations[2]*concentrations[3]),
                    k_fwd[3]*(concentrations[3]*concentrations[6] + -1*self.usr_np.exp(log_k_eq[3])*concentrations[7]**2.0),
                    k_fwd[4]*(concentrations[2]**2.0 + -1*self.usr_np.exp(log_k_eq[4])*concentrations[0]),
                    k_fwd[5]*(concentrations[2]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[5])*concentrations[3]),
                    k_fwd[6]*(concentrations[6]**2.0 + -1*self.usr_np.exp(log_k_eq[6])*concentrations[1]),
                    k_fwd[7]*(concentrations[2]*concentrations[6] + -1*self.usr_np.exp(log_k_eq[7])*concentrations[7]),
                    k_fwd[8]*(concentrations[6]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[8])*concentrations[4]),
                    k_fwd[9]*(concentrations[2]*concentrations[1] + -1*self.usr_np.exp(log_k_eq[9])*concentrations[4]),
                    k_fwd[10]*(concentrations[2]*concentrations[4] + -1*self.usr_np.exp(log_k_eq[10])*concentrations[7]**2.0),
                    k_fwd[11]*(concentrations[2]*concentrations[4] + -1*self.usr_np.exp(log_k_eq[11])*concentrations[0]*concentrations[1]),
                    k_fwd[12]*(concentrations[2]*concentrations[4] + -1*self.usr_np.exp(log_k_eq[12])*concentrations[3]*concentrations[6]),
                    k_fwd[13]*(concentrations[4]*concentrations[6] + -1*self.usr_np.exp(log_k_eq[13])*concentrations[1]*concentrations[7]),
                    k_fwd[14]*(concentrations[4]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[14])*concentrations[3]*concentrations[1]),
                    k_fwd[15]*(concentrations[4]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[15])*concentrations[3]*concentrations[1]),
                    k_fwd[16]*(concentrations[7]**2.0 + -1*self.usr_np.exp(log_k_eq[16])*concentrations[5]),
                    k_fwd[17]*(concentrations[4]**2.0 + -1*self.usr_np.exp(log_k_eq[17])*concentrations[5]*concentrations[1]),
                    k_fwd[18]*(concentrations[4]**2.0 + -1*self.usr_np.exp(log_k_eq[18])*concentrations[5]*concentrations[1]),
                    k_fwd[19]*(concentrations[2]*concentrations[5] + -1*self.usr_np.exp(log_k_eq[19])*concentrations[0]*concentrations[4]),
                    k_fwd[20]*(concentrations[2]*concentrations[5] + -1*self.usr_np.exp(log_k_eq[20])*concentrations[3]*concentrations[7]),
                    k_fwd[21]*(concentrations[5]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[21])*concentrations[3]*concentrations[4]),
                    k_fwd[22]*(concentrations[5]*concentrations[7] + -1*self.usr_np.exp(log_k_eq[22])*concentrations[3]*concentrations[4]),
                    k_fwd[23]*(concentrations[5]*concentrations[6] + -1*self.usr_np.exp(log_k_eq[23])*concentrations[4]*concentrations[7]),
               ])

    def get_net_production_rates(self, rho, temperature, mass_fractions):
        c = self.get_concentrations(rho, mass_fractions)
        r_net = self.get_net_rates_of_progress(temperature, c)
        ones = self._pyro_zeros_like(r_net[0]) + 1.0
        return self._pyro_make_tensor([
                r_net[4] + r_net[11] + r_net[19] + -1*(r_net[1] + r_net[2]) * ones,
                r_net[6] + r_net[11] + r_net[13] + r_net[14] + r_net[15] + r_net[17] + r_net[18] + -1*(r_net[0] + r_net[9]) * ones,
                r_net[1] + r_net[2] + -1*(r_net[0] + 2.0*r_net[4] + r_net[5] + r_net[7] + r_net[9] + r_net[10] + r_net[11] + r_net[12] + r_net[19] + r_net[20]) * ones,
                r_net[2] + r_net[5] + r_net[12] + r_net[14] + r_net[15] + r_net[20] + r_net[21] + r_net[22] + -1*r_net[3] * ones,
                r_net[8] + r_net[9] + r_net[19] + r_net[21] + r_net[22] + r_net[23] + -1*(r_net[10] + r_net[11] + r_net[12] + r_net[13] + r_net[14] + r_net[15] + 2.0*r_net[17] + 2.0*r_net[18]) * ones,
                r_net[16] + r_net[17] + r_net[18] + -1*(r_net[19] + r_net[20] + r_net[21] + r_net[22] + r_net[23]) * ones,
                r_net[0] + r_net[12] + -1*(r_net[1] + r_net[3] + 2.0*r_net[6] + r_net[7] + r_net[8] + r_net[13] + r_net[23]) * ones,
                r_net[0] + r_net[1] + 2.0*r_net[3] + r_net[7] + 2.0*r_net[10] + r_net[13] + r_net[20] + r_net[23] + -1*(r_net[2] + r_net[5] + r_net[8] + r_net[14] + r_net[15] + 2.0*r_net[16] + r_net[21] + r_net[22]) * ones,
                0.0 * ones,
               ])
