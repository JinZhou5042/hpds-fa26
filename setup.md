---
layout: default
---

# Setup Instructions

## Create a Repository

[Create a GitHub repository](https://github.com/new) named `NETID-hpds` for your coursework:
- Make sure the repository is marked **private** and not public.
- Add `dthain` and `JinZhou5042` as collaborators.
- When turning in assignments, just paste the repository URL into the Canvas assignment submission.

## Request a CRC account

Sign in to your Notre Dame email account, open the [CRC account instructions](https://docs.crc.nd.edu/new_user/obtain_account.html), and complete the linked new-user form.

You only need your own CRC account. There is no special CRC project or course account to join. Wait for the CRC account confirmation email and follow the first-login instructions in that message, including the Okta synchronization step if it is requested.

## Create an NSF ACCESS Account

Go to the [ACCESS Account page](https://account.access-ci.org/) and select **Register**. Register with your Notre Dame email address and complete the profile, email verification, and authentication steps.

If you already have an ACCESS or former XSEDE account, use that account. Do not create a second one.

After registration, open your ACCESS profile and copy the **ACCESS ID** exactly as shown. Your ACCESS ID is not necessarily the same as your Notre Dame NetID.

### Join the course allocation

The course has an active allocation on Purdue Anvil through this ACCESS project:

```text
Project: CIS261613
Title: Graduate Course in High Performance Distributed Systems
PI: Douglas Thain
```

The course will provide Anvil resources for all students. Email your name, Notre Dame NetID, and ACCESS ID to the TA at `jzhou24@nd.edu`.

The TA will add your ACCESS ID to the course project. Check **My Projects** in the [ACCESS Allocations portal](https://allocations.access-ci.org/). You can use Anvil after it appears under CIS261613 with a resource username. Provisioning may take some time after you are added.

### Set up SSH access to Anvil

Anvil uses SSH keys for terminal access. Start on your laptop and create a key for Anvil:

```console
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_anvil
```

Press three Enters until you see the output. The command creates a private key named `id_ed25519_anvil` and a public key named `id_ed25519_anvil.pub`.

Display the public key on macOS or Linux:

```console
cat ~/.ssh/id_ed25519_anvil.pub
```

On Windows PowerShell, use:

```console
Get-Content ~/.ssh/id_ed25519_anvil.pub
```

Copy the complete line beginning with `ssh-ed25519`. Open [Anvil Open OnDemand](https://ondemand.anvil.rcac.purdue.edu/), log in with your ACCESS identity, and select **Clusters -> Anvil Shell Access**. In the Anvil shell, run:

```console
mkdir -p ~/.ssh
chmod 700 ~/.ssh
vim ~/.ssh/authorized_keys
```

Paste the public key into `authorized_keys` and save the file. Then return to your laptop and replace `ANVIL_USERNAME` with the resource username shown in **My Projects**:

```console
ssh ANVIL_USERNAME@anvil.rcac.purdue.edu
```

The first connection may ask you to confirm the host key. A successful login opens a shell on an Anvil login node.

