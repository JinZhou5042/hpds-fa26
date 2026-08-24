---
layout: default
title: A0 - Computing Resources Warmup
---

# A0: Computing Resources Warmup

In this assignment, you will set up accounts at Purdue Anvil and the Notre Dame CRC, then submit one small batch job at each site. The jobs themselves are deliberately simple. The point is to get account and scheduler problems out of the way before we begin larger assignments.

Start both account requests as soon as possible. Account creation and resource access may take a few days.

## Anvil status

Our ACCESS project CIS261613 has been approved, but the exchange for Anvil computing resources is still under review. You can create your ACCESS account and email the TA your ACCESS ID now, but you must wait for the class announcement before trying to log in to Anvil.

The TA will add students to the allocation after the exchange is active. This is not something students can do themselves.

## Part A: ACCESS and Purdue Anvil

### 1. Create an ACCESS account

Go to the [ACCESS Account page](https://account.access-ci.org/) and select **Register**. Register with your Notre Dame email address and complete the profile, email verification, and authentication steps.

If you already have an ACCESS or former XSEDE account, use that account. Do not create a second one.

After registration, open your ACCESS profile and copy the **ACCESS ID** exactly as shown. Email your name, Notre Dame NetID, and ACCESS ID to the TA at `jzhou24@nd.edu` with the subject `[CSE 60772] A0 - NETID`, replacing `NETID` with your own NetID. Your ACCESS ID is not your Notre Dame NetID.

You do not need to request your own ACCESS project or allocation. The class will use:

```text
Project: CIS261613
Title: Graduate Course in High Performance Distributed Systems
PI: Douglas Thain
```

### 2. Wait to be added to Anvil

After the Anvil exchange is approved, the TA will add your ACCESS ID to CIS261613 and enable the Anvil resource for you.

You can check this in the [ACCESS Allocations portal](https://allocations.access-ci.org/) under **My Projects**. You are ready when CIS261613 lists Anvil and shows an Anvil username. The Anvil username will normally begin with `x-` and is different from your ACCESS ID.

Provisioning is not always immediate. Allow 12 to 48 hours after the TA confirms that you were added.

### 3. Log in to Anvil

Open [Anvil Open OnDemand](https://ondemand.anvil.rcac.purdue.edu/), log in with your ACCESS identity, and select **Clusters -> Anvil Shell Access**.

Run these commands in the Anvil shell:

```console
whoami
hostname
mybalance
showpartitions
```

`mybalance` prints the Slurm account that you will use for the job. Copy that account name exactly; do not assume it is the same as `CIS261613`.

### 4. Submit a Slurm job

The shell opened above is on a shared login node. Use Slurm to run the test job on a compute node.

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

## Part B: Notre Dame CRC

### 1. Request a CRC account

Sign in to your Notre Dame email account, open the [CRC account instructions](https://docs.crc.nd.edu/new_user/obtain_account.html), and complete the linked new-user form.

You only need your own CRC account. There is no special CRC project or course account to join.

CRC will notify you by email when the account is ready. Follow the first-login instructions in that message, including the Okta synchronization step if it is requested.

### 2. Log in to a CRC front end

CRC has two general front ends: `crcfe01.crc.nd.edu` and `crcfe02.crc.nd.edu`. They provide the same software and serve the same purpose; they are simply two separate shared machines. You may use either one for this assignment. If one is unavailable or busy, try the other.

CRC also has `condorfe.crc.nd.edu`, a front end dedicated to HTCondor submissions. We will use it later when submitting larger collections of HTCondor jobs, but either general front end is sufficient for this one-job warmup.

All front ends are shared by many CRC users. A long-running or multicore program on a front end can consume the CPU and memory needed by everyone else, making logins, editors, compilers, and scheduler commands slow or unresponsive. Use a front end only for short, lightweight work. Submit long-running, CPU-intensive, memory-intensive, or multicore programs through Grid Engine or HTCondor so that they run on compute nodes with resources reserved for the job.

If you are off campus, connect to the Notre Dame VPN before trying to log in. Follow the [Notre Dame VPN installation and connection instructions](https://nd.service-now.com/nd_portal?id=product_page&sys_id=9d5919c7db22a34099dcf25bbf9619e2&table=cmdb_ci_business_app/). If you are on campus, connect through the campus network.

Wait until CRC confirms that your account has been created, then choose either command below and replace `NETID` with your Notre Dame NetID:

```console
ssh NETID@crcfe01.crc.nd.edu
ssh NETID@crcfe02.crc.nd.edu
```

Run only one of these commands. Record which front end you chose.

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

## What to submit

Download [warmup-template.txt](warmup-template.txt), rename it `warmup.txt`, and fill in each field. Reply to the same email thread that you used to send your ACCESS ID and attach the completed `warmup.txt`. Copy the requested output as text; screenshots are not necessary. Do not include passwords, Duo codes, recovery codes, or private keys.

If ACCESS, Anvil, or CRC is still processing your request at the deadline, write `PENDING`, the date you made the request, and the current status in that section. Finish the remaining job after access is enabled.

## If something goes wrong

You are welcome to email the TA at `jzhou24@nd.edu` whenever you need help. Describe clearly which system you are using, what you tried, and what happened. Include your source code and the complete command output or error message, and attach screenshots if possible. The TA will be happy to help.

## References

- [ACCESS account help](https://support.access-ci.org/documentation/your-access-account)
- [ACCESS project user management](https://allocations.access-ci.org/how-to)
- [Anvil access and usernames](https://docs.rcac.purdue.edu/userguides/anvil/access/)
- [Anvil getting started](https://docs.rcac.purdue.edu/userguides/anvil/getting-started/)
- [Anvil job submission](https://docs.rcac.purdue.edu/userguides/anvil/jobs/)
- [CRC account request](https://docs.crc.nd.edu/new_user/obtain_account.html)
- [CRC quick start](https://docs.crc.nd.edu/new_user/quick_start.html)
- [HTCondo