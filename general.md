---
layout: default
---

# Assignments - General Guidance

This page contains account and cluster information that applies to all assignments. Read the individual assignment page for the work you must complete and the files you must submit.

## Using Notre Dame CRC

### Request a CRC account

Sign in to your Notre Dame email account, open the [CRC account instructions](https://docs.crc.nd.edu/new_user/obtain_account.html), and complete the linked new-user form.

You only need your own CRC account. There is no special CRC project or course account to join. Wait for the CRC account confirmation email and follow the first-login instructions in that message, including the Okta synchronization step if it is requested.

### Connect to a CRC front end

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

## Using NSF ACCESS

ACCESS provides accounts for national computing facilities, including Purdue Anvil.

### Create an ACCESS account

Go to the [ACCESS Account page](https://account.access-ci.org/) and select **Register**. Register with your Notre Dame email address and complete the profile, email verification, and authentication steps.

If you already have an ACCESS or former XSEDE account, use that account. Do not create a second one.

After registration, open your ACCESS profile and copy the **ACCESS ID** exactly as shown. Your ACCESS ID is not necessarily the same as your Notre Dame NetID.

### Join the course allocation

The class uses the following ACCESS project:

```text
Project: CIS261613
Title: Graduate Course in High Performance Distributed Systems
PI: Douglas Thain
```

You do not need to request your own ACCESS project or exchange ACCESS Credits. Email your name, Notre Dame NetID, and ACCESS ID to the TA at `jzhou24@nd.edu` with the subject `[CSE 60772] ACCESS ID - NETID`, replacing `NETID` with your own NetID.

This email is only a request to be added to the course allocation; it is not an assignment submission. Send it once, before beginning the warmup assignment. The assignment itself will be submitted in a second email after the work is complete.

The TA must add your ACCESS ID to the course project and enable the appropriate computing resource. You can check your access in the [ACCESS Allocations portal](https://allocations.access-ci.org/) under **My Projects**. A resource is ready when it appears under CIS261613 and shows a resource username. Provisioning may not be immediate.

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

## Turning in Assignments

Follow the submission instructions on each assignment page. Unless an assignment says otherwise, copy terminal output as text rather than submitting screenshots.

### Getting help

You are welcome to email the TA at `jzhou24@nd.edu` whenever you need help. Clearly describe which system you are using, what you tried, and what happened. Include your source code and the complete command output or error message, and attach screenshots if possible. The TA will be happy to help.
