![icon](sara_1_icon.ico)
# SARA 1 

## Goal and context
This is a project that was made from November 26 2020 and was finished during May/July 2021.

It is functionnal, but is not reallyoptimized. It's a proof of concept.

Yes, but what is it really ?

It is a NLP UI based on a tree selection process.
Sara1 is not able to detect word position, and hence, the tree did the intent detection through a word distance function that was to be minimized.
This word distance is NOT based on embeddings, but rather on a dictionary lookup table where words have a certain 
semantic distance based on a maze solving algorithm and a synonym dictionary being parsed(pre-processed, of course).

To handle orthographic mistakes as well as Out Of Vocabulary tokens, a Levensteinian distance was also computed, before being transformed so as to 
minimise the impact of small mistakes on long words

The tree then looks at all of the nodes, and uses once more a maze-solving algorithm to minimize distance until the action Node. It is to be noted 
that every branch has a priority, that is increased by a number depending on the node each layer, and that the maze-solving algorithm is trying to 
increase as much as possible. Not a perfect solution, but for a kid who hasen't done any ML, it works (and anyway, the thing about ML is if you can
avoid it, do so.)

The action Node contains code stored in string form (which, yes, is dangerous, but no one but me was ever supposed to gain access to the prototype), 
which is then pllayed. It is given a context dictionary which contains(among other things) the request. This allowed for arguments to be extracted
dynamically from the request, such as the calendar modifications routine.

The whole application comes with a GUI that could theoretically be taken out, and replaced quite easily with a pipe file reader that would then be 
connected to any desired input method (why not voice analysis).

## Reflexion on finished product

So, in conclusion.

A good first proof of concept, especially for one done on my free time while in CPGE ("classe prépas"), which is satisfying. However, the prototype 
is far from deployable, due to poor performances, lack of any kind of security, poor algorithmic choices, and rather simplistic GUI design. 
It is also quite hard to scale up in both functionnality (Tree modification can be done in GUI, but is a chore) and in tree complexity (Not having
any embeddings, and not having gone for a kd-tree then makes the whole thing harder than needs be).

Is it good at intent detection ?

Somewhat... If you know the action node you are trying to trigger, then yes.

What is that sleep Mode.

Sleep Mode is an attempt at getting the system to cycle through all interactions it has recorded, and try to optimize it's various parameters so 
as to get the right answer.
