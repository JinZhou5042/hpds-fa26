# NA61 ROOT Analysis

- Domain: high-energy physics analysis for the NA61 experiment at CERN and
  neutrino-flux estimation for the NuMI beam at Fermilab.
- Contacts: Michael Quintieri (`mquintie@nd.edu`) and Laura Fields
  (`lfields2@nd.edu`).
- Technical profile: a C++ program built against ROOT reads a large data file,
  selects events, and produces spectra used downstream.
- Course fit: an intentionally inefficient, portable analysis stage offers a
  tractable target for profiling, data-access analysis, and parallelization.

## Project packet

Collect the repository and revision, a legally and technically shareable
representative ROOT dataset, data-access instructions, ROOT environment,
typical command or shell script, expected output, baseline runtime, and the
owner's view of the principal bottleneck.
