---
layout: default
---

# Assignments - General Guidance

This page contains account and cluster information that applies to all assignments. Read the individual assignment page for the work you must complete and the files you must submit.

Before doing anything else, follow the [setup instructions](setup) to create your various accounts.

## Code Repository

Anything to be turned in should be checked into your repository for this course,
which will grow and evolve as the semester develops.  Please put each assignment
in a separate directory named according to the unit: `warmup`, `simd`, `openmd`, `cuda` and so forth.

In that directory, you should include all the technical materials
that describe the experiments you ran, along with the results.
Make sure to include:

- Source code for anything you ran.  (even if examples from the textbook)
- All scripts needed to build or run the code.  (e.g. shell script, makefile...)
- Raw data resulting from your experiments. (e.g. runtimes for each configuration)
- Code to generate the necessary plots. (e.g. matplotlib code or gnuplot file)
- A `README.md` file that addresses the questions and other objectives of the assignment.

We strongly recommend that you add materials to the repository incrementally as you work,
rather than trying to assemble things at the last minute.  Commit as you go.

In all things, take time to organize your materials, give them constructive names,
and make everything clear and consistent.

## Turning In

Once you have committed and pushed any necessary changes to your repository,
simply go to Canvas and submit the assignment online by pasting the URL
of your repository.  Once an assignment is submitted, you are welcome to work on the next assignments
by making commits in other directories.

## Resources

### Using the Notre Dame CRC

If you are off campus, connect to the Notre Dame VPN before using SSH. Follow the [Notre Dame VPN installation and connection instructions](https://nd.service-now.com/nd_portal?id=product_page&sys_id=9d5919c7db22a34099dcf25bbf9619e2&table=cmdb_ci_business_app/). If you are on campus, connect through the campus network.

CRC has two equivalent general front ends, `crcfe01.crc.nd.edu` and `crcfe02.crc.nd.edu`. You may use either one and switch to the other if your first choice is unavailable or busy. Replace `NETID` with your Notre Dame NetID and run one of these commands:

```console
ssh NETID@crcfe01.crc.nd.edu
ssh NETID@crcfe02.crc.nd.edu
```

CRC also has `condorfe.crc.nd.edu`, a front end dedicated to HTCondor submissions. The general front ends are sufficient for small jobs unless an assignment specifically asks you to use `condorfe`.

All CRC front ends are shared by many users. A long-running or multicore program on a front end consumes CPU and memory needed by everyone else and can make logins, editors, compilers, and scheduler commands slow. Use front ends only for short, lightweight work. Submit long-running, CPU-intensive, memory-intensive, or multicore programs through Grid Engine or HTCondor.

### CRC references

- [CRC account request](https://docs.crc.nd.edu/new_user/obtain_account.html)
- [CRC quick start](https://docs.crc.nd.edu/new_user/quick_start.html)
- [HTCondor at Notre Dame](https://docs.crc.nd.edu/resources/condor.html)

### Use Purdue Anvil

Open [Anvil Open OnDemand](https://ondemand.anvil.rcac.purdue.edu/), log in with your ACCESS identity, and select **Clusters -> Anvil Shell Access**. Anvil access will not work until the course has an active Anvil allocation and the TA has assigned you to it.

Run these commands after opening the Anvil shell:

```console
whoami
hostname
mybalance
showpartitions
```

Your Anvil username will normally begin with `x-` and is different from your ACCESS ID. `mybalance` shows the Slurm account used to submit jobs; do not assume that this account name is the same as the ACCESS project ID.

The Anvil shell runs on a shared login node. Use it for short tasks such as editing files, compiling small programs, and submitting or checking jobs. Run long, CPU-intensive, memory-intensive, or multicore programs through Slurm so that they execute on compute nodes with reserved resources.

### ACCESS and Anvil references

- [ACCESS account help](https://support.access-ci.org/documentation/your-access-account)
- [ACCESS project user management](https://allocations.access-ci.org/how-to)
- [Anvil access and usernames](https://docs.rcac.purdue.edu/userguides/anvil/access/)
- [Anvil getting started](https://docs.rcac.purdue.edu/userguides/anvil/getting-started/)
- [Anvil job submission](https://docs.rcac.purdue.edu/userguides/anvil/jobs/)

