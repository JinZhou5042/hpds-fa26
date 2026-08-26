---
layout: default
title: A0 - Computing Resources Warmup
---

# A0: Computing Resources Warmup

In this assignment, you will set up accounts at the Notre Dame CRC and Purdue Anvil, then submit one small batch job at each site. The jobs themselves are deliberately simple. The point is to get account and scheduler problems out of the way before we begin larger assignments.

Complete the [first-time setup](../../setup) and read the [general instructions](../../general) before starting. Start both account requests early because provisioning may take a few days.

## Part A: Notre Dame CRC

### 1. Request a CRC account

Follow [Request a CRC account](../../setup#request-a-crc-account) and wait for CRC to confirm that your account is ready.

### 2. Log in to the HTCondor front end

Review the network and VPN requirements in [Using the Notre Dame CRC](../../general#using-the-notre-dame-crc). Then replace `NETID` with your Notre Dame NetID and log in to the HTCondor front end:

```console
ssh NETID@condorfe.crc.nd.edu
```

The "front end" machine is a normal Linux machine, capable of running ordinary applications.
(Experiment with the `w` and `ps` and `top` commands to view the large number of people and processes running.)

It's ok to execute **short-running** programs here (seconds to minutes), but it should not
be used to run programs that are long-running, memory intensive, or highly multi-threaded.
Doing so will disrupt the many other people logged in.

The purpose of the front-end machines is to **submit** jobs to the cluster,
where they will be dispatched to available machines, and then can perform intensive
tasks without interference.

### 3. Submit an HTCondor job

So, let's submit a simple job to run on a different machine in the cluster.

Get in the habit of creating a fresh directory for each assignment/task/activity:

```console
mkdir -p warmup
cd warmup
```

Here, create a file called `crc-hello.submit` that contains this HTCondor submit file:

```
universe = vanilla
executable = /bin/hostname
output = crc-hello.out
error = crc-hello.err
log = crc-hello.log

request_cpus = 1
request_memory = 128MB
request_disk = 10MB

should_transfer_files = yes
when_to_transfer_output = on_exit

queue 1
```

This is a set of instructions to run one application (`/bin/hostname`) on the cluster,
instead of on the front end machine.  Submit the job like this:

```console
condor_submit crc-hello.submit
```

Remember the job ID printed by `condor_submit`, such as `12345.0`. To see whether it is still in the queue, replace `NETID` with your NetID:

```console
condor_q NETID
```

This job may finish before you see it in `condor_q`. Once it is gone from the queue, examine the three files it produced:

```console
cat crc-hello.out
cat crc-hello.err
tail -n 12 crc-hello.log
```

The job succeeded if `crc-hello.out` contains the name of an execute machine, `crc-hello.err` is empty, and the end of `crc-hello.log` reports that the job terminated with exit code 0.

### Explore Further

Try these commands and explore various options to view the state of the cluster and its users.
- `condor_q`
- `condor_status`
- `condor_userprio`
- [condor_matrix](http://condor.cse.nd.edu/condor_matrix.cgi)

## Part B: ACCESS and Purdue Anvil

### 1. Log in to Anvil

Follow [Use Purdue Anvil](../../general#use-purdue-anvil) to open an Anvil shell. Confirm that `mybalance` lists the course CPU account `cis261613` before continuing.

### 2. Submit a Slurm job

Use Slurm to run the test job on a compute node.

Again, get in the habit of creating a directory for each new activity:

```console
mkdir -p warmup
cd warmup
```

Create a file called `anvil-hello.slurm` containing instructions to run a job on the cluster:
```
#!/bin/bash
#SBATCH --account=cis261613
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128M
#SBATCH --time=00:01:00
#SBATCH --job-name=hpds-warmup
#SBATCH --output=anvil-%j.out

echo "system=anvil"
echo "job_id=${SLURM_JOB_ID}"
echo "user=$(whoami)"
echo "compute_host=$(hostname)"
date -u '+utc_time=%Y-%m-%dT%H:%M:%SZ'
```

Submit the job like this:

```console
sbatch anvil-hello.slurm
```

`sbatch` will print a numerical job ID. Remember it. You can check the job while it is waiting or running with:

```console
squeue --me
```

After the job leaves the queue, replace `JOBID` below with your job ID:

```console
cat anvil-JOBID.out
seff JOBID
```

The job succeeded if `anvil-JOBID.out` names a compute host and `seff` reports `State: COMPLETED` with exit code `0`.

## Turning In

Create your repository as described in the [first time setup](../../setup).

In that repository, create a `warmup` directory, and include the following:
- `crc-hello.submit`, `crc-hello.out`, `crc-hello.err`, and `crc-hello.log` from the CRC job.
- `anvil-hello.slurm` and `anvil-JOBID.out` from the Anvil job.
- A `README.md` that records both job IDs, describes the outcomes, and explains what you learned from Explore Further.

Make sure you have committed and pushed all your work.

Submit your work in Canvas by pasting the repository URL into the assignment submission page.
