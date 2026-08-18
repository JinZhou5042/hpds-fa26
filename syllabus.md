---
layout: default
title: Syllabus
---
# Syllabus - CSE 60772 - High Performance Distributed Systems - Fall 2026

## Instructors:

- Prof. Douglas Thain `dthain@nd.edu`
- TA: Jin Zhou `jzhou24@nd.edu`

## Course Web Page

[https://dthain.github.io/hpdc-fa26](https://dthain.github.io/hpdc-fa26)

## Overview

This course will introduce students to the theory and practice of high performance distributed computing, in which applications are scaled up to run effectively on hundreds to thousands of cluster nodes.

We begin with an overview of the fundamentals of cluster architecture and the software systems used to manage cluster resources. Building on that foundation, students will explore a range of programming models used to structure large scale applications, such as bag-of-tasks, graph workflows, functional programming, and data parallel programming.
Scheduling and performance metrics relevant to distributed applications will be introduced, and students will explore the unavoidable tradeoffs between execution time, resource consumption, and fairness.

The semester-long course project will entail students matching with owners of existing scientific applications drawn from across the University in fields such as physics, astronomy, molecular dynamics, etc. These connections will be facilitated by Prof. Thain and the staff of the Center for Research Computing.

Students will characterize the performance of the existing (local) applications, select and develop a distributed programming model, deploy the applications at large scale, evaluate the end-to-end system performance, and then develop a new contribution that improves some aspect of performance, reliability, or efficiency of the distributed application. A final presentation and written technical paper are required.

## Audience

- PhD students beginning research in distributed computing.
- MS and PhD students wishing to employ distributed computing for their own research.
- Advanced undergraduates who have completed CSE 40771. (limited number, with permission only)

## Prerequisites

- CSE 30341 (Operating Systems) or equivalent course.
- Programming experience in C or Python
- Strong fluency with the Unix command line.

## Facilities Available

Students must request accounts at these two facilities <b>during the first week of class</b> so as to be able to use them throughout the semester.

- <a href=https://docs.crc.nd.edu>Notre Dame Center for Research Computing (CRC)</a> - Our local campus facility which provess a shared cluster accessible of CPUs and GPUs through SLURM or HTCondor along with parallel storage capability.  This is easy to get started with, and generally has plenty of capacity available early in the semester.  <b>Beware: The cluster tends to become highly utilized with long wait times during the last few weeks of the semester.</b>
- <a href=https://access-ci.org>NSF ACCESS CI</a> - A national federation of computing facilities accessible through a common interface.  Students should request an EXPLORE allocation and initially request access to the Purdue Anvil facility as a common starting point.  Shifting to other facilities during the semester to explore what is available is encouraged. 



## Course Outcomes

Students successfully completing this course will be able to: 
- Describe the architecture and operation of a variety of common distributed systems.
- Compare the architecture and operation of various distributed systems.
- Describe how distributed systems are fundamentally different from standalone systems in matters such as naming, invocation, synchronization, and fault tolerance.
- Construct, test, and evaluate programs in a distributed environment.
- Communicate technical results orally and in writing.

## Assignments

- Warmup - Get access to the CRC and ACCESS and verify that you can compile and submit simple jobs.
- Multicore - Gain experience with OpenMP, use it tow write simple multicore kernels, and evaluate performance and scaling.
- GPU - Gain experience with CUDA, use it to write simple parallel kernels, and evaluate performance and scaling.
- Workflows - Gain experience with workflow systems, and use them to organize and scale out applications to the entire cluster.
- Filesystems - Evaluate the performance, scalability, and limitations of both local and parallel storage systems, and use them to divide work units appropriately. 
- Course Project - Select a scientific application, 
-- Project Proposal
-- Annotated Bibliography
-- Progress Report
-- Class Presentation
-- Final Paper

Final Chalk Talk

## How we Learn Together

(me) Introduction 
(you) Reading and Exploration
(us) Questions and Discussion
(you) Complete Assignment
(me) Evaluate 


## Important References

Vector Instructions
SIMD Parallelism - Chapter 10.1-10.6 of Algorithmica HPC by Sergey SLotin
https://en.algorithmica.org/hpc/simd/

Threading - OpenMP

OpenMP
The Art of HPC, Volume 2, Chapter 17-27, by Victor Eijkhout
https://theartofhpc.com/pcse/index.html

A "Hands-On" Introduction to OpenMP, Tim Mattson and Larry Meadows
https://www.openmp.org/wp-content/uploads/omp-hands-on-SC08.pdf


GPU/CUDA
CUDA Programming Guide
https://docs.nvidia.com/cuda/cuda-programming-guide/

HTCondor

TaskVine

Ray

The principles of distributed systems will be studied via the course textbook:

[Marten van Steen and Andrew Tanenbaum, Distributed Systems 4th edition, 2023](https://www.distributed-systems.net/index.php/books/ds4)

You can order a physical copy of this book, or register online to download a PDF, as you prefer, but do one or the other right away!

The textbook provides the foundation of the course, and it will be important for you
to absorb it in preparation for class.  You should read the assigned chapters and take notes each weekend.  Summary notes on the assigned readings will be due in Canvas (usually) **Mondays** by 11AM.

The most effective way to read and retain information is to take notes the old-fashioned way, by hand with pen and paper. If you are out of the habit of writing by hand, now is a great time to start, so as to build up your muscles and practice for the exams.  Once written out, just snap a few photos and upload to Canvas.

Your notes can be organized in whatever way is appropriate to that chapter and is useful for you. Good things to include may be an outline of the chapter, definition of key terms, or a sketch of the systems or data structures being discussed.  Finally, answer the reflection
question posed in the assignment.

Grading on notes will be very simple: either one, one-half, or zero points.
There are ten opportunities to earn 11 points, so you can miss one without penalty.
The act of taking notes is entirely for your benefit, so we are just looking for a constructive effort on your part.

## Final Project

In the final project, students will propose, build, and measure a distributed system of their own design, which must make use of multiple techniques discussed in class to achieve a system that is robust and performant. Examples might include a distributed filesystem, a parallel programming model, or a peer-to-peer data routing system. The final submission will include a project report describing the design of the system.

## About the AZS

## How to Get the Most Out of Class

To succeed in the class, you should attend all class meetings, take notes, and participate in class discussions. During most class sessions, I'll give a prepared lecture for about 30 minutes, and then we will shift into Q&amp;A or working on an example.

The textbook is dense in places; sometimes a key algorithm may only occupy two pages in the book, but requires 30 minutes of class discussion to work out all the details. So, it works best if you read the textbook for a broad understanding before class, and then go back and review details and work some examples afterward.

Because much of the class material involves working with system diagrams and examples, I will mostly work on the blackboard instead of presenting slide decks. I recommend that you take notes by sketching along with pen and paper: the simple act of note-taking exercises your mental muscles in a way that passive observation does not. If you prefer to take notes on your laptop or tablet, then that's fine too.

However, I do ask that you refrain from using your laptops or phones for non-class related tasks during class time. I know it is tempting during a brief lull to respond to messages, check the news, etc, but even one laptop open can be an unavoidable distraction for other people in the class.   Please reserve this time for working together.

Note that **classes will not be recorded**, so plan accordingly.
Our class meetings are primarily for discussion and practice using the
available written materials, so if you miss class for whatever reason,
then catch up by reviewing the written materials and talking with a peer.

## Communications

Assignments and the course schedule are available on the course website, and assignment grades will be posted in Canvas.  We will be using Slack to handle general Q&amp;A for the class. If you have a technical question that could be of interest to others, please post it there, so that others can benefit from the answers. You are welcome to post (or answer) questions anytime, and we will generally monitor and answer questions on weekday afternoons. (Keep in mind that we do go home at night, and so late-night questions will get answered the next day.)  For questions about grades or anything else that just applies specifically to you, just email the instructor or TA directly.

Office hours are a great time to get focused help on a tricky bit of code. We are happy to help you during that time -- just knock, come in, and introduce yourself. If you can't make any of the office hours, then send email to see if we can work out another time.

## Assignments and Grading

Programming assignments are generally due at 5:00PM on Fridays.
Because the programming assignments are cumulative, working up to
a larger goal, it's important to stay on top of things and make progress
every week -- don't leave the assignment until the last minute.

Programming assignments will be submitted by copying files to a "dropbox"
directory on the student machines. Writing assignments (project proposal, etc)
will be submitted via the Canvas assignments feature.

**Late assignments will receive no credit.**  Everything in this class builds
up piece by piece, and it's important to stay on track.  If some assignment isn't
working out perfectly, it's usally best to submit what you have on time, and keep moving.

You are permitted **one free late pass** to account for the ordinary circumstances of
life, such as a minor illness, schedule conflict, etc.  To do so, just send an email to the TA **before the deadline**, saying briefly "I would like to take a late pass on assignment X".
And the due date for that item will be extended by seven calendar days.
(Naturally, you can't use a late pass on the exams or the final project.)

Beyond that, exceptions will only be made for serious circumstances
such as a hospitalization, death in the family,
mandatory participation in a university sponsored event,
or the other items outlined in section 3.1 of the Undergraduate Academic Code.
In those cases, please confer with the instructor at the earliest possibility.

For each assignment, a numeric grade will be awarded.
Throughout the semester, grades and class averages will be posted through Sakai.
At the end of the semester, I'll convert number grades to letter grades on
a scale of A/B/C/D = 90/80/70/65, and exercise some prudential judgement
for pluses and minuses and borderline grades.

Overall grades will be weighted as follows: Reading Notes (10%),Programming Assignments (30%), Course Project (30%), Midterm (15%), Final (15%).

## Academic Code of Honor

As a student at Notre Dame, you are bound by the [Academic Code of Honor](http://honorcode.nd.edu), which states:

*As a member of the Notre Dame community, I acknowledge that it is my responsibility to learn and abide by principles of intellectual honesty and academic integrity, and therefore I will not participate in or tolerate academic dishonesty.*

The purpose of the homeworks and assignments in this course is for you
to gain the discipline and skills in analysis, design, and programming so that
you will be able to work independently in a professional setting.
To that end, all work in this class must be the result of your own ideas and effort.

You are permitted to consult with other students, search engines,
and AI assistants in order to find documentation, troubleshoot technical
problems, and generally get "unstuck" after making your own efforts.
However, the outcome of such consultation must
be that you understand *what it means* and *how to do it yourself*.
You remain responsible for all work that bears your name.

## Some Campus Resources

- If you require an accommodation for a disability, please first contact the
Sara Bea Center [http://sarabeadisabilityservices.nd.edu](sarabeadisabilityservices.nd.edu) for a consultation, and we will be happy to work together on a solution.
-  If you encounter a difficult life situation and don't know what to do,
the University Counseling Center [http://ucc.nd.edu](http://ucc.nd.edu) or the Care and Wellness Consultants [http://care.nd.edu](care.nd.edu) can help and also connect you with other campus resources.
