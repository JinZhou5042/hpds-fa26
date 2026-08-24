---
layout: default
title: A0 - Computing Resources Warmup
---

# A0: Computing Resources Warmup

In this assignment, you will set up accounts at the Notre Dame CRC and Purdue Anvil, then submit one small batch job at each site. The jobs themselves are deliberately simple. The point is to get account and scheduler problems out of the way before we begin larger assignments.

Start both account requests as soon as possible. Account creation and resource access may take a few days.

Read the course [General Assignment Guidance](../../general) before starting. It explains how to create the accounts, connect to both clusters, use shared front ends responsibly, and ask for help.

Before beginning the tasks below, [create or recover your ACCESS account](../../general#create-an-access-account) and [email your ACCESS ID to the TA](../../general#join-the-course-allocation). This is the first of two emails: it is needed to request Anvil access and is not your assignment submission. If you have already sent this email, do not send it again.

## Part A: Notre Dame CRC

### 1. Request a CRC account

Follow [Request a CRC account](../../general#request-a-crc-account) and wait for CRC to confirm that your account is ready.

### 2. Log in to a CRC front end

Follow [Connect to a CRC front end](../../general#connect-to-a-crc-front-end), choose either `crcfe01.crc.nd.edu` or `crcfe02.crc.nd.edu`, and record your choice in `warmup.txt`.

### 3. Submit an HTCondor job

Create a working directory and download [crc-hello.submit](crc-hello.submit):

```console
mkdir -p ~/hpds-warmup
cd ~/hpds-warmup
curl -LO https://dthain.github.io/hpds-fa26/assignments/warmup/crc-hello.submit
```

Submit one job from the general front end you selected:

```console
condor_submit crc-hello.submit
```

Save the job ID printed by `condor_submit`, such as `12345.0`. To see whether it is still in the queue, replace `NETID` with your NetID:

```console
condor_q NETID
```

This job may finish before you see it in `condor_q`. Once it is gone from the queue, examine the three files it produced:

```console
cat crc-hello.out
cat crc-hello.err
tail -n 12 crc-hello.log
```

The job succeeded if `crc-hello.out` contains the name of an execute machine, `crc-hello.err` is empty, and the end of `crc-hello.log` reports normal termination with return value 0.

## Part B: ACCESS and Purdue Anvil

### 1. Wait to be added to Anvil

Our ACCESS project CIS261613 has been approved, but the exchange for Anvil computing resources is still under review. Wait for the class announcement before trying to log in to Anvil.

After the Anvil exchange is approved, the TA will add your ACCESS ID to CIS261613 and enable the Anvil resource for you. This is not something students can do themselves.

Check **My Projects** as described in the general guidance. Continue when CIS261613 lists Anvil and shows your Anvil username.

### 2. Log in to Anvil

Follow [Use Purdue Anvil](../../general#use-purdue-anvil) to open an Anvil shell and identify your Slurm account with `mybalance`.

### 3. Submit a Slurm job

Use Slurm to run the test job on a compute node.

Create a working directory and download [anvil-hello.slurm](anvil-hello.slurm):

```console
mkdir -p ~/hpds-warmup
cd ~/hpds-warmup
curl -LO https://dthain.github.io/hpds-fa26/assignments/warmup/anvil-hello.slurm
nano anvil-hello.slurm
```

In `anvil-hello.slurm`, replace `SLURM_ACCOUNT_FROM_MYBALANCE` with the account printed by `mybalance`, then save the file.

Submit the job:

```console
sbatch anvil-hello.slurm
```

`sbatch` will print a numerical job ID. Save it. You can check the job while it is waiting or running with:

```console
squeue --me
```

After the job leaves the queue, replace `JOBID` below with your job ID:

```console
cat anvil-JOBID.out
seff JOBID
```

The job succeeded if `anvil-JOBID.out` names a compute host and `seff` reports `State: COMPLETED` with exit code `0`.

## What to submit

After completing both parts, download [warmup-template.txt](warmup-template.txt), rename it `warmup.txt`, and fill in each field. Send a second email to `jzhou24@nd.edu` with the subject `[CSE 60772] A0 - NETID`, replacing `NETID` with your own NetID, and attach `warmup.txt`. This second email is your assignment submission; do not include your ACCESS ID again. Copy the requested output as text; screenshots are not necessary. Do not include passwords, Duo codes, recovery codes, or private keys.

If ACCESS, Anvil, or CRC is still processing your request at the deadline, write `PENDING`, the date you made the request, and the current status in that section. Finish the remaining job after access is enabled.
