---
layout: default
title: Course Project
---

# Course Project for Distributed Systems

## Requirements

The final project in this course will be open ended.  You will propose, carry out, and report upon a project in groups of **two** students.
Projects must have the following elements:

- **Build a System** - Your project must involve constructing a system of some complexity
that deals with some of the challenging problems of distributed systems, such as reliability, consistency,
replication, and so forth. If you make use of existing software or packages, then you must build something
substantially new on top, and not just plug a few things together. Python is a recommended implementation language, but you are welcome to use another language (perhaps Rust, Go, or Ruby) if it is more suitable for your purpose.

- **Evaluate its Performance** - The performance of your system must be evaluated carefully, in
a manner appropriate to the nature of the system.  For example, if your system is designed to be
scalable, then you should evaluate throughput and latency as the number of nodes increases.
Or, if it is designed to be reliable, then you should evaluate its performance when nodes fail.
Or, if it is designed to be consistent, then you should evaluate the latency of update propagation
under various conditions.  Think carefully about the appropriate evaluation for your system.

- **Present it Clearly** - Present your work cogently by writing a paper and making an oral presentation.
The paper should describe the motivation, design, evaluation methods, and quantitative results of your project.
The oral presentation should summarize the most important aspects of the paper and give a demo of how it works,
during the last week of class.

## Project Ideas

Following are some ideas to get you thinking.  You are welcome to modify one of these ideas,
or to pick a different problem, but talk to Prof. Thain first if you have something radically different in mind.
**One rule:** please no cryptocurrency mining!
These end up consuming a lot of resources to no productive end.

**Peer to Peer Communication Network** - Build a system that allows for social interaction
(live chat, or news updates, or social networking)
between many users, without requiring any centralized server.  Each participant
in the system should have their own independent node that passes appropriate messages
back and forth.  Decide how to discover other nodes, pass messages to the rest
of the system, put messages in a suitable order, and how to deal with disconnections
and outages.  Measure the latency and throughput of message dissemination as
the system grows in size.

**Distributed Model Inference**
Select a machine learning model and a set of inference tasks that are (individually)
easy to run on a single machine using a standard framework like PyTorch.
(e.g. classifying images of animals)   Design a distributed system to take those 
tasks and distribute them across multiple machines in order to achieve much increased
throughput.  Be careful to consider how you will ensure that each machine is busy,
but not overloaded, and deal with failing machines.

**Distributed Operating System**
Design a distributed system that overlays a number of existing computers
and makes it easy for a single user to transparently run arbitrary programs
across the cluster without knowing or seeing exactly what machine they are on.
That is, the end user should be able to do (something like) `fork()`, `exec()` and `ps`
from one place and have the impression that they are using one big machine.

**Scalable Filesystem** - Design a file storage system that can scale up to a large
number of nodes.  One approach to this is to create a single "name" node and multiple "storage" nodes.
The name node can keep track of the filesystem tree, file names, and the location of the files on the storage nodes.
To access a file, a client must interact with the name node to locate it, and then the storage node to access it.
Consider how to choose where to put files, where to replicate files, and how to deal with node outages.
Measure both the latency and performance of the system as the number of clients and servers increases.

**Log Oriented Replication** - Use the idea of chain replication to build a reliable distributed
data structure like a hash table.  Make good use of a transaction log at each node: as entries are
appended at one node, arrange for those
log entries to be passed on to the next system in a row.  Careful: When is it safe for one node to compress
its own log?  Consider how a new node joins the system, and what happens when a node crashes.
Evaluate the throughput and latency of the system as the number of clients and servers increases.

**Distributed Board Game Engine** - Pick a common board game  -- Chess, Othello, Go, etc -- that
has many configurations and is thus computationally difficult for a computer to play effectively.
Take an existing solver for this game that works on a single node, and build a distributed system
that can run it on multiple nodes at the same time, playing against a human user.
In this way, the difficulty of the "computer" player can be expanded to as many nodes as desired.
Measure the time to reach a solution of a given quality, and the amount of the configuration space
that can be explored in a fixed amount of time.

**Distributed Interactive Game** - Create a simple multi-player interactive game, where a centralized
server manages the game and players must interact from client nodes.  The game could be an old-school text
adventure (explore rooms, collect items, etc) or something more graphical if you are so inclined.
Design into the game some actions that are mutually exclusive, requiring the server to perform a total
ordering on the actions and return the results to the client. For example, if user A roasts a marshmallow on a fire,
while user B *concurrently* puts the fire out with water, what's the outcome?

## Computing Resources

You have several choices where to deploy your project:
- The student machines are a good choice if your project involves long-running servers that have persistent state: a filesystem, data structure, distributed OS, etc.
- Your own laptops are a good choice if you are implementing an interactive service between people: chat system, interactive game.
- The [Center for Research Computing](http://crc.nd.edu) is a good choice if you are scaling up an intensive computation: distributed inference, board game, etc.  This can give you access to hundreds or thousands of machines, but you will need to sign up and experiment a bit early on in order to use it correctly.
- Cloud services (Amazon, Azure, etc) are a good choice if you need to set up complex software environments or require root access to configure things.

## Milestones

**Project Proposal - Friday, March 6th** -
Turn in a document that describes the overall shape of your project.
This should include the project partners, a high level description
of the goals and structure of the system, identification of the key
*distributed systems* problem in the system, 
what languages and resources will be necessary to carry it out,
and your plan for evaluating the system.  Be sure to think about
what *metrics* you will use to evaluate the system -- throughput, latency,
scalability, runtime -- and sketch a notional graph of how you think
that metric will change as the system size or load increases.
(Of course, I don't expect you to know the actual results, but I want
you to think about **what** you will measure and what orders of magnitude to expect.)
The proposal should be about two full pages of text.  The instructor will follow up with
you to make sure that the project is of appropriate size and difficulty.
**Submit this via the Assignments tab in Canvas.**

**Progess Report - Friday, April 10th** -
Turn in a detailed report describing the overall design of your
system and your progress towards building it.  This will be a substantial
report of some length that will require you to  think carefully about the
details of the system design **before**
writing every bit of code.  Your report should have the following sections:
- **Purpose**. Describe the purpose of your system.  What is it designed to
accomplish, and how will you know if it is working correctly?
What are the essential challenges that must be overcome to deliver service to the user?
If your project is similar to something that already exists (e.g. Hadoop or Chord or DNS) then explain carefully
how your work differs from the original.
- **Architecture**.  Describe in detail how the internals of the system will work.
Draw a detailed diagram of the system showing how the processes in the system relate,
and examples of how they communicate in order to carry out the essential functions of
the system.  Detail how the system handles names or identifiers: what do they mean,
how are they generated, how they are made unique, and how items in the system are discovered or located.
Detail how the system is made reliable in the presence of failures: what happens
if the network goes down or individual processes crash, and how the system responds.
- **Progress**.  Describe your progress so far.  At this point, you should have
the technology installed and working, and be able to demonstrate some basic functionality,
even if not all of the features or capabilities are ready yet.  Include one or more
screenshots to show that something is working.  Indicate your progress
toward completion and any challenges or problems discovered along the way.
**Submit this via the Assignments tab in Canvas.**

**Class Presentation**

- During the final two weeks of class, you
will give a **fifteen** minute presentation to the whole class.
The talk should include an overview of the goal or problem, the structure of your
system, an example of how your system operates, and your results from evaluating
the system so far.  Each member of the group should speak for part of the time.
Your talk should be accompanied by 10-15 carefully designed
and edited slides, containing detailed diagrams of your system.

- While this is a short talk, it will require careful preparation
in order to be detailed, informative, and on time.  Practice multiple times
together so that you can consistently finish between 14m30s and 14m59s.
Following each talk, there will be **two** minutes for questions from the audience.
In the meantime, the next group should come up to the podium and load the next
slide deck.  

- **Attendance will be taken** during project talks, and will count for a portion
of your grade. Please show courtesy to your classmates by arriving on time and
giving them your attention.

- To ensure a minimum of technical difficulties, please prepare your slides using
**Google Slides**, make sure it is readable by anyone with the link, and email Prof. Thain
with the link no later than 5PM the day before the presentation.  (It's fine if you
continue to update the presentation after that point, but I need the link to assemble
the schedule.)

**Final Submission - Wednesday, April 29th at 5PM** - Turn in your code and the final paper.
The code should be structured such that the instructor can build and
execute it independently.  The paper should give an overview of the
goal or the problem, a detailed description of the structure of your
system, including a good diagram where appropriate, and an evaluation
of the correctness and performance of the system.  You can and should include
material from your progress report regarding the architecture of the system,
but of course the material should be updated and extended substantially.
There is no specific length requirement; the paper should be long enough to explain all
of the necessary details.  The said, anything less than five pages
is probably too short; anything longer than fifteen pages is probably too long.

**Submit your final report as a PDF via the Assignments tab in Canvas.
The code for your final project should be checked into a (private) github
repository that is shared with `dthain` and `colinthomas-z80`.  Clearly indicate
the URL of your repository on the first page of your report.**

