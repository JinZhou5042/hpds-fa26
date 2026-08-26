---
layout: default
title: Syllabus
---
# Syllabus 

## Instructors:

- Prof. Douglas Thain (`dthain@nd.edu`)
- TA: Jin Zhou (`jzhou24@nd.edu`)

## Course Web Page

[https://dthain.github.io/hpds-fa26](https://dthain.github.io/hpds-fa26)

## Overview

This course will introduce students to the theory and practice of high performance distributed systems, in which scientific applications are scaled up to run effectively on hundreds to thousands nodes in clusters.

We begin with an overview of the fundamentals of parallel computing at local scale:
vector (SIMD) architectures for data-parallel computing,
multicore architectures for coarse task-parallel computing,
and GPU architectures for fine-grained parallelization.
For each of these techniques, we will explore the performance of a variety of comptuational kernels
across different scales and devices.

Once a code is reasonably optimized on a local scale, then we are ready to distribute it across
the entire cluster.  We will explore the overall architecture of HPC clusters, and focus on the software
systems used to organize computations across nodes with local parallelism.  We will consider a variety
of distributed programming models, such as bag-of-tasks, graph workflows, distributed futures,
and functions as a service.  Across these, we will consider the intrinsic tradeoffs between execution
time, resource consumption, and fairness.

In the second half of the semester, students will undertake a course project that explores application
performance from bottom to top.  Students will be matched with example scientific applications drawn
from across the university.  The application must be evaluated and optimized at local scale,
adapted to a distributed programming model, and then evaluated and optimized at cluster scale.
A progress report, class presentation, and written technical paper will summarize the overall work.

## Prerequisites

- CSE 30341 (Operating Systems) or equivalent course.
- Programming experience in C and Python
- Strong fluency with the Unix command line.

## Communications

All of the course details (slides, assignments, manuals, links) will be posted on the course website.
Feedback on assignments will be returned via Canvas.  The Slack channel will be used for general Q&amp;A for the class.
If you have a technical question that could be of interest to others, please post it to the channel, so that others can benefit from the answers. You are welcome to post (or answer) questions anytime, and we will generally monitor and answer questions on weekday afternoons. (Keep in mind that we do go home at night, and so late-night questions will get answered the next day.)  For questions about feedback or anything else that just applies specifically to you, just email the instructor or TA directly.

## How to Get the Most Out of this Course

First, our scheduled class time is for the purpose of **talking to each other** and developing community.
Most classes, I will plan to lecture for about half of the time, and then transition to discussion.
You should commit to attending every class, but please send me a note if your are absent for an important
reason such as doctor appointment, conference travel, etc.

To that end, **class will not be recorded** and also **you may not record class** on your own device.
This is to ensure that we can have a free-flowing discussion with each other,
without concern for our words (unpracticed, accidental, or erroneous) being shared around the world.
If you are concerned about missing a key detail, then please consult the written materials (website, slides, manuals, etc)
as the definitive resource for the class.

Second, this class is built on the idea that you are a **motivated and independent student** who is ready to figure out some details on your own.  Each major unit in the class will be developed over 2-3 weeks like this:

- **Key Principles** - In class, I will give a high level overview of the hardware and software concepts that form the organizing principles of a particular topic, such as multicore programming, cluster architecture, distributed functions, etc.
- **Tech Intro** - There may be multiple technologies that exhibit these principles.  I will pick *one* widely used technology in each area (e.g. OpenMP, CUDA, HTCondor), and give you a practical introduction showing how to get started, run some example codes, perform some common transformations, and measure performance.
- **Deep Dive** - Out of class, you will dig deeply into the technology and learn more than was shown in class by reading manuals, looking up tutorials, writing code, and trying out new features.  You will certainly have to solve some unexpected problems by puzzling over error messages and trying different approaches.  Be curious, creative, and persistent!
- **Report Back** - The assignments will be somewhat open-ended, so that you can show us what you have learned.
Demonstrate that you have understood the principles, and then also show that you have found or created new ideas and approaches.
Each student will sign up for one "demo days" in which you make a short presentation to the class of a technique
or example that you have worked out yourself.

## Assignments and Deadlines

**Important:** Do not expect to complete assignments in a single sitting on the due date.  Expect that every assignment will involve unexpected errors, queueing delays, troubleshooting, and rumination.  Start early, so that these matters can be spread over several days.

Assignments are generally due at 5PM on the date indicated.  In general, **late assignments will not be graded**, so if you come up short on time, then submit whatever work you have accomplished by the deadline, and move on to the next assignment.

You are permitted **one free late pass** to account for the ordinary circumstances of
life, such as a minor illness, schedule conflict, etc.  To do so, just email/slack the TA before the deadline, saying briefly "I would like to take a late pass on assignment X".
And the due date for that item will be extended by seven calendar days.
(Naturally, you can't use a late pass on the exams, the final presentation, or the final project.)

Beyond that, exceptions will only be made for serious circumstances
such as a hospitalization, death in the family,
mandatory participation in a university sponsored event,
or the other items outlined in section 3.1 of the Undergraduate Academic Code.
In those cases, please confer with the instructor at the earliest possibility.

## Facilities Available

Each assignment will require that you evaluate your work in multiple locations,
so as to consider the effects of different hardware.  We assume that you have
access to a laptop or workstation in the CSE department as a starting point.
In addition, you must request accounts at these two facilities **during the first week of class** so as to be able to use them throughout the semester.

- [Notre Dame Center for Research Computing (CRC)](https://docs.crc.nd.edu) - Our local campus facility which provess a shared cluster accessible of CPUs and GPUs through SLURM or HTCondor along with parallel storage capability.  This is easy to get started with, and generally has plenty of capacity available early in the semester.  **Beware:** The cluster tends to become highly utilized with long wait times during the last few weeks of the semester.
- [NSF ACCESS Cyberinfrastructure](https://access-ci.org): A national federation of computing facilities accessible through a common interface. Follow the [setup instructions](setup#join-the-course-allocation) to join the course allocation on Purdue Anvil. Do not request your own ACCESS allocation. Shifting to other facilities during the semester to explore what is available is encouraged.

## Grading

As graduate students, you are training to be research scholars, and the quality of research isn't measured in percentage points.  Research feedback comes in prose form.  Strong work is accepted for publication, while work that needs improvement is declined so that it can be revised.  Great work is read and cited, but never graded. I want you to focus on doing quality work, and not on counting percentage points.

To that end, **I will not be awarding numeric or letter grades on each assignment**.  Instead, for each assignment, you will receive back a paragraph of qualitative comments indicating where your work is strong,
where improvement is needed, and suggestions for learning and going deeper.  We will consider
your work on the following axes:

- **Insight** - Does your work demonstrate a clear understanding of the principles at work?
Explain things assuming that your reader is encountering your work for the first time.
Your quantitative results should be understandable and well supported by appropriate descriptions.
Surprising results should be highlighted and described to the best of your ability.
- **Curiosity** - Does your work demonstrate a genuine curiosity that goes well beyond
the starting points given in class?  Expect to dig deeply into reference materials,
troubleshoot unexpected problems, and make use of the all the computing resources available to you.
- **Craftsmanship** - Does your work show care and consistency in execution?
Prose should be clearly written; code should be well designed; diagrams should be clear and consistent; fonts should be appropriate sizes; etc.

Summary letter grades will be given at the midterm break, before the final exam,
and then at the end of the course.  `A` will be given to an overall body of work
that consistently demonstrates insight, curiosity, and craftsmanship.
`B` will be given to work that is generally good but has room for improvement in one area.
`C` will be given to work that is acceptable but has multiple significant weaknesses.

## Academic Code of Honor

As a student at Notre Dame, you are bound by the [Academic Code of Honor](http://honorcode.nd.edu), which states:

> As a member of the Notre Dame community, I acknowledge that it is my responsibility to learn and abide by principles of intellectual honesty and academic integrity, and therefore I will not participate in or tolerate academic dishonesty.

In this class, that means that any work that bears your name is the result of your own efforts.
(Or where group work is permitted, the members of that group.)  You must construct your own code, run your own
experiments, plot your own graphs, and write your own text.  If your work incorporates small elements (text, code, data)
that came from somewhere else, then they must be clearly identified as such, and the source cited by an appropriate method.

Artifical Intelligence (AI) technologies are of course everywhere and rapidly changing.
This includes tools such as ChatGPT, Gemini, Copilot, and anything else that functions similarly.  We will discuss these tools at various points and consider their impact on the profession.  In general:

- You are **permitted** to use AI tools to **discover information**.  These tools can be very helpful to survey technologies, suggest specific features, troubleshoot problems, and understand error messages.  If the outcome is an increase in your own understanding, then you are using these tools **correctly**.
- You are **prohibited** from AI tools to **generate products**.  You should be writing your own code,
drawing your own conclusions, and writing your own words.  If the outcome is a copy-paste of material from AI into your assignments, then you are using these tools **incorrectly.**

This is the key test: **You should be able to readily explain any aspect of your submitted work: how you wrote it, how it works, and what it means.**  If you cannot do that, then the only logical conclusion is that it is not your own work.

## Some Campus Resources

- If you require an accommodation for a disability, please first contact the
Sara Bea Center [http://sarabeadisabilityservices.nd.edu](sarabeadisabilityservices.nd.edu) for a consultation, and we will be happy to work together on a solution.
-  If you encounter a difficult life situation and don't know what to do,
the University Counseling Center [http://ucc.nd.edu](http://ucc.nd.edu) or the Care and Wellness Consultants [http://care.nd.edu](care.nd.edu) can help and also connect you with other campus resources.
