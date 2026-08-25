---
layout: default
title: A0 - Computing Resources Warmup
---

# A0: Computing Resources Warmup

In this assignment, you will set up accounts at the Notre Dame CRC and Purdue Anvil, then submit one small batch job at each site. The jobs themselves are deliberately simple. The point is to get account and scheduler problems out of the way before we begin larger assignments.

First review the [general instructions](../../general) and do the [first time setup](../../setup) instructions.
Start both account requests as soon as possible. Account creation and resource access may take a few days.

Before beginning the tasks below, [create or recover your ACCESS account](../../setup#create-an-nsf-access-account) and [email your ACCESS ID to the TA](../../setup#join-the-course-allocation). This is the first of two emails: it is needed to request Anvil access and is not your assignment submission. If you have already sent this email, do not send it again.

## Part A: Notre Dame CRC

### 1. Request a CRC account

Follow [Request a CRC account](../../setup#request-a-crc-account) and wait for CRC to confirm that your account is ready.

### 2. Log in to a CRC front end

Follow [Connect to a CRC front end](../../general#using-the-notre-dame-crc), choose either `crcfe01.crc.nd.edu` or `crcfe02.crc.nd.edu`, and make a note of your choice.

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

Summarize 

## Part B: ACCESS and Purdue Anvil

### 1. Wait to be added to Anvil

Our ACCESS project CIS261613 has been approved, but the exchange for Anvil computing resources is still under review. Wait for the class announcement before trying to log in to Anvil.

After the Anvil exchange is approved, the TA will add your ACCESS ID to CIS261613 and enable the Anvil resource for you. This is not something students can do themselves.

Check **My Projects** as described in the general guidance. Continue when CIS261613 lists Anvil and shows your Anvil username.

### 2. Log in to Anvil

Follow [Use Purdue Anvil](../../general#use-purdue-anvil) to open an Anvil shell and identify your Slurm account with `mybalance`.

### 3. Submit a Slurm job

Use Slurm to run the test job on a compute node.

Again, get in the habit of creating a directory for each new activity:

```console
mkdir -p warmup
cd warmup
```

Create a file called `anvil-hello.slurm` containing instructions to run a job on the cluster:
```
#!/bin/bash
#SBATCH --account=SLURM_ACCOUNT_FROM_MYBALANCE
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:01:00
#SBATCH --job-name=hpds-warmup
#SBATCH --output=anvil-%j.out

echo "system=anvil"
echo "job_id=${SLURM_JOB_ID}"
echo "user=$(whoami)"
echo "compute_host=$(hostname)"
date -u '+utc_time=%Y-%m-%dT%H:%M:%SZ'
```

In `anvil-hello.slurm`, replace `SLURM_ACCOUNT_FROM_MYBALANCE` with the account printed by `mybalance`, then save the file.

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
- All the files submitted/created to run a job on the ND CRC.
- All the files submitted/created to run a job on Purdue Anvil.
- A README.md file that describes what you did, what the outcomes were,
and what you learned from the "Explore Further" prompts.

Make sure you have committed and pushed all your work.

Submit your work in Canvas by pasting the repository URL into the assignment submission page.
