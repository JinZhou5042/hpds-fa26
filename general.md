---
layout: default
---

# Assignments - General Guidance

## Setup a Python 3 Environment

The five programming assignments must be written in Python 3 and run
correctly on the CSE student machines.  (student10-13.cse.nd.edu)
If you prefer to do your development work on your laptop or another
machine, that's ok, but then you are responsible for setting up the appropriate
environment, and then ensuring that your work functions on the student machines.

The student machines have Python 3.6.8 installed by default,
which is a rather on the old side.
For this class, you will need to set up
your own environment with the correct version.
(Other classes may require different versions.)

First, log into one of the student machines:

```
ssh <netID>@student10.cse.nd.edu
```

Where `<netID>` is your Notre Dame netID. Use your account password as student machine login password.

Then, download and install [Miniforge](https://docs.conda.io/en/latest/miniconda.html) for Linux, if you haven't done so for another class:

```
curl https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh > miniforge.sh
chmod 755 miniforge.sh
./miniforge.sh
```

Note: please enter `yes` for the last step of installation (initialize), which adds `conda` to `PATH`.

Once Conda is installed, you should log out and log back in.
Notice that your prompt should now have the prefix `(base)`,
which indicates you are in the `base` Conda environment.

Now, create an environment `distsys` just for this class:

```
conda create --name distsys python=3.12
```

Then, whenever you are working on this class, activate the `distsys`
environment, and you will have the right version of Python:

```
(base) dthain@student10$ conda activate distsys
(distsys) dthain@student10:~$ python -V
Python 3.12.0
```

To switch back to the default environment for another class,
 use `conda deactivate` one or more times, until your prompt is clean:

```
(distsys) dthain@student10$ conda deactivate
(base) dthain@student10$ conda deactivate
dthain@student02:~$ python -V
Python 3.6.8
```

When your prompt is clean, you are out of any Conda environment, using the original version of Python on the student machine.
Now you may use `conda activate` or `conda activate base` to go back to `base` Conda environment.
Similarly, as long as you have created `distsys`, you may use `conda activate distsys` to go to `distsys` Conda environment directly, which skips `base`.

## Focus on Standard Libraries

The general approach for solving the programming assignments in this class is to
learn how to use the basic Python language and standard libraries to build up
complex systems.  This will help you to understand these capabilities in detail
and develop the skills for building new libraries of your own.

To that end, you should become intimately familiar with the [standard library documentation](https://docs.python.org/3.12/library/index.html).  These modules in particular will be helpful:

- [File and Directory Access](https://docs.python.org/3.12/library/filesys.html)
- [subprocess](https://docs.python.org/3.12/library/subprocess.html)
- [time](https://docs.python.org/3.12/library/time.html)
- [json](https://docs.python.org/3.12/library/json.html)
- [http.client](https://docs.python.org/3.12/library/http.client.html)
- [socket](https://docs.python.org/3.12/library/socket.html)
 
Now, there do exist various additional packages and libraries that provide
implementations of some of the techniques that we discuss: remote procedure call,
consensus, persistence, and so forth.  However, we won't be using those, because
simply "installing package X" doesn't lead to any new understanding or experience.
If you find yourself trying to solve a technical problem by installing new 
Conda packages, then you are probably taking the wrong approach to the assignment.  Talk to the instructors to see if there is a better way.

On a related note, exercise care when searching for solutions online.
Stack Overflow and AI tools can be helpful when trying to understand
obscure error messages, or find the right standard library to use.
However, don't just uncritically copy a bit of code that you find:
it may be solving a different problem, it may be an "advertisement" for someone's
favorite package, or it may not work at all.  Use that solution as a "clue"
to read the documentation for that particularly function or library, so that
you can understand how to use it yourself.

## Getting Started with Git
Git is a version control tool that allows you to save and collaborate on programming projects. In Git, your code is saved in two different locations–the local copy and the remote copy.

Make a Remote Copy

1) First make sure you are logged into Github. Go to your repositories, and click the button to make a new one. 

2) Use your netid followed by whatever you’d like as the repository name. For example: YOURNETID-distsys-sp26

3) Make sure your repository is PRIVATE not public, then finish creating the repository.

4) Fill out [this form](https://forms.gle/CUKj4cQjrzSzt3hV7) so we can associate your email, netID, and github account. 

5) Go into your repository settings on the right side of the screen then click on “Collaborators”. Add `colinthomas-z80`, `Leoreoreo` and `dthain` as contributors, so that we can see and grade your submissions.

7) Go back to the repository main page and click the green “code” button then copy the URL under the “SSH” tab. The URL should look something like this: git@github.com:YOURNAME/YOURNETID-distsys-sp26.git. If you see a yellow box asking you to create public ssh keys, follow the instructions to do so.

Programming assignments have names with sequential numbers like `a1`, `a2`, `a3` ... For each of these assignments make a new directory with the name such as `a2` and complete the assignment in this directory. It is okay if the empty directories for future assignments do not show up on GitHub. 

When you build upon work from one assignment to the next, such as `a3` and `a4`, copy all of the files into `a4`. Do not modify or reference files from previous assignment directories. 

## Turning in Assignments

Writing assignments and some other where specified will be turned in through Canvas. All other assignments will be pushed to your GitHub repository.

Programming assignments have names with sequential numbers like `a1`, `a2`, `a3` ... For each of these assignments make a new directory with the name such as `a2` and complete the assignment in this directory. It is okay if the empty directories for future assignments do not show up on GitHub. 

When you build upon work from one assignment to the next, such as `a3` and `a4`, copy all of the files into `a4`. Do not modify or reference files from previous assignment directories. 

## Turning in Code to GitHub

1) Make sure that all files that you have changed are added with git add, committed with git commit, and pushed with git push.

2) Go back to your github repository. Make sure you refresh your page. If everything went well you should see all of your changes.

3) On the right hand side under “Releases”, click “Create new release”

3) Click “Choose a new tag”, type "a2" (or “a3”, “a4”, ... for later assignments) then click “Create new tag”

4) Click “Publish release” at the bottom and you’re done!



