# AutoQuiz
Master of Science Project code, using [Flask](http://flask.pocoo.org/).

[Thesis](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2018/EECS-2018-54.html) available online.

If you want to use our code (and data perhaps), please cite it as the format listed here:
```
@mastersthesis{Xiao:EECS-2018-54,
    Author = {Xiao, Zhiping},
    Editor = {Garcia, Dan},
    Title = {AutoQuiz: an online, adaptive, test practice system},
    School = {EECS Department, University of California, Berkeley},
    Year = {2018},
    Month = {May},
    URL = {http://www2.eecs.berkeley.edu/Pubs/TechRpts/2018/EECS-2018-54.html},
    Number = {UCB/EECS-2018-54},
    Abstract = {    Students often have trouble knowing how to prepare for high-stakes exams. Even in the best case where legacy problems and solutions are available, there are usually no indications of the difficulty of a particular question or relevance to the material with which the student needs the most help. The problem is exacerbated by traditionally large introductory courses, where there’s no way a teacher could suggest a custom plan of study for every student, as they could in a small, face-to-face setting.
    In this report, we present AutoQuiz, an online, adaptive, test practice system. At its heart is a model of user content knowledge, which we call an “adapted DKT model”. We test it on two datasets, ASSISTments and PKUMOOC, to verify its effectiveness. We build a knowledge graph and encode assessment items from UC Berkeley’s non-majors introduction to computing course, CS10: The Beauty and Joy of Computing (BJC), and have volunteer students from the Spring 2018 version of the course use the system and provide qualitative feedback. We also measure the system quantitatively based on how well it improved their exam performance. The high-level user interaction is as follows:
    1. If a student prefers choosing a specific question on her own or iterating through all the questions in the system, we’ll give her adequate freedom to select questions under specified topics.
    2. If a student chooses “challenge” mode to test herself, we’ll pull a fixed-sized group of multiple-choice questions from an archive based on our estimation of the student’s performance on the skills she is expected to master. The student will receive automated and dynamic feedback after each submission.}
}
```

## Dependencies

* Based on [Flask](http://flask.pocoo.org/) framework
* Front-end using [JQuery](https://jquery.com/) and [Bootstrap](https://getbootstrap.com/)
* Login system handled by [Flask-Login](https://flask-login.readthedocs.io/en/latest/)

## Simplified maintnance:

**0.** Initialize database by running ***sh init_db.sh*** on mac, or ***sqlite3 auto_quiz.db < schema.sql*** followed by ***python init_db.py*** in any other environment. 

Note: this initialization will clear the user data you already have. In fact, you might want to update using only ***python init_db.py***.

**1.** When adding a question to the system:
- create a new xml file under ***./static/dataset/*** with the given format of other existing .xml files;
- if involve new skill, log it by adding new key-value pairs in variable ***skill_map*** in ***init_db.py***;
- run script ***update_db_skill_question.py***

**2.** About the environment:

I used Python 2.7 back then.

Run by ```python auto_quiz.py```.
