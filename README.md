# Classrooms

With repl.it's Classrooms feature being disabled on the 31st Jan 2021, schools are now required to pay $1000 dollars a year for something which they used to use for free!

This is a replacement for repl.it's classrooms feature now that it has been shut down. It uses replauth and embed repls for the assignments, so is still based heavily around repl.it.


## Creating a Classroom

First you will need to be a teacher on repl.it. You can do this by going to the [account page](https://repl.it/account) and scrolling down to the roles section and selecting the teacher role - if you do this after making an account it may take a while to update in this database, so is recommended that you make sure you have this role prior to your first login.

Next on the [landing page](https://classrooms.codingcactus.repl.co) click the `Create` button towards the top of the page. This will allow you to then input the name, language, description, and icon for the classroom.


## Editing a Classroom

When viewing the classroom's tecaher page (at `/classroom/<classroom_id>/teachers`) click the `Edit` button. This will present you with the form to edit your classroom name, description, and icon.


## Cloning a Classroom

When viewing the classroom's tecaher page (at `/classroom/<classroom_id>/teachers`) click the `Clone` button. This will present you with the form to clone your classroom. You can change the classroom name, description, and icon. Cloning a classroom will copy all the assignments over into a new classroom (with modal answers). Students (and their submissions) and teachers will not be transfered to the new classroom.

## Deleting a Classrrom

When viewing the classroom's tecaher page (at `/classroom/<classroom_id>/teachers`) click the `Delete` button. Only the classroom owner can perform this action.


## Inviting people to your classroom

Once a classrooms is created, you will be taken to the teachers page for it. The teachers page is at `/classroom/<classroom_id>/teachers`. Here you have the buttons to edit the classroom info (name, description, etc.), add students, and add teachers. It also shows the overview of students and their progress throughout each assignment.

When you click the `Invite More` button for either students or teachers, it will present you with three options:

1. Invite a user by their repl.it username
2. Copy an invite link to send to people that you wish to have in your classroom
3. Copy an invite code to be entered on the [landing page](https://classrooms.codingcactus.repl.co) by people you wish to have in your classroom


## Joining a classroom

The only way to join a classroom is through being invited. There are different actions to be taken depending on what type of invite you received:

1. Invited by username: An invite will appear on the landing page for you to either accept or deny
2. Invite link: Simply follow the link
3. Invite code: Enter the  code on the landing page in the `Enter code` box


## Removing people from your classroom

Go to the teachers page and click the `X` next to the student or teacher that you wish to remove. Only the owner of the classroom can remove other teachers.


## Creating assignments

Go to your classroom page (by either clicking on it from the landing page or just going to `/classroom/<classroom_id>`). Click the `Create` button and then enter the name and instructions. This will then show you the page where you can see the general overview of students progress in that assignment.


## Editing Assignments

When viewing the assignment (at `/classroom/<classroom_id>/<assignment_id>`) click the `Edit` button. This will present you with the form to edit your assignment name and instructions.

## Deleting Assignments

When viewing the assignmentr page (at `/classroom/<classroom_id>/<assignment_id>`) click the `Delete` button.


## Completing assignments

Go to your classroom page (by either clicking on it from the landing page or just going to `/classroom/<classroom_id>`). You will see a list of assignments. Click on one that you wish to work on. You will need to then create a repl, and then enter it's url into the box asking for it (only once). This will then embed that repl into that page for you to work on. The Instructions will be on the right side.


## Submitting assignments

Once you have completed the task, you can click the `Submit` in the top right corner of the page. This will allow your teacher to give feedback on your submission. If you feel as though you have missed something, you can unsubmit the assignment using the `Unsubmit` button which will appear.

After your teacher has returned your submission, you can view their feedback, and make any changes that are necessary. If you make some changes, you can click the `Resubmit` button which will send it back to your teacher for remarking.


## Viewing a student's submission

When viewing the assignment overview, you can click on a student, and it will take you to the page which shows their repl.


## Giving feedback on assignments

Once a student has submitted their assignment (shown as the `awaiting feedback` status), you will be able to give feedback on it by clicking the student in the assignment overview page, and writing your feedback in the bottom right box and then click the `Send feedback` button. You can edit this feedback by simply editing what you have written in the box and clicking the `Send feedback` button again.



# Hosting yourself
If you really want to host a clone of this rather than using https://classrooms.codingcactus.repl.co you will need 4 things.

1. [Repl.it](https://repl.it) account
2. [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account
3. [Cloudinary](https://cloudinary.com) account
4. [Uptime Robot](https://uptimerobot.com) account (or any pinging service)

This will cover everything assuming that you have never used any of the services. So if you have already got accounts etc. then you will be able to skip a few steps.

#### Repl.it
- Sign up at https://repl.it/signup
- Click this: [![Run on Repl.it](https://repl.it/badge/github/Coding-Cactus/classrooms)](https://repl.it/github/Coding-Cactus/classrooms)
- Put `python main.py` in the empty box in the top right
- Press the Done button in the box that appears on the top right quarter of the screen
- Create a file clalled exactly `.env`

#### MongoDB Atlas
- Sign up at https://account.mongodb.com/account/register
- Create a new project
- Create a cluster
  - Choose a plan that you want (free plan will work fine)
  - Leave the settings as they are
  - Click create cluster
- Click the Database Access button in the sidebar
- Add a new database user
  - Give it a name
  - Give it a password
  - Copy the password
  - Give it the Atlas Admin role
  - Add User
- Go back to the clusters page
- Click connect
- Click Allow access from anywhere
- CLick Add IP Address
- Add the database user that you just created
- Click Choose Connection Method
- Click the bottom option
- Copy the url from part 2
- Add `mongouri=yoururl` to the `.env` file in your repl, but replace `yoururl` with the url from the previous step. Replace the `<password>` with the password of the database user (from earlier)



### Cloudinary
- Sign up at https://cloudinary.com/users/register/free
- Look at the account details section at the top of the dahsboard page
- Add `CLOUDINARY_CLOUD_NAME=abcdef` to the `.env` file in your repl, but replace `abcdef` with your cloudinary cloud name
- Add `CLOUDINARY_API_KEY=1234546` to the `.env` file in your repl, but replace `123456` with your cloudinary api key
- Add `CLOUDINARY_API_SECRET=asdf` to the `.env` file in your repl, but replace `asdf` with your cloudinary api secret


### Uptime Robot
- Sign up at https://uptimerobot.com/signUp
- Add a http moniter pointing at the repl.co url for your repl (`https://replname.username.repl.co`)


Press the run button on your repl


## More to come!

You can view what else is planned in [roadmap.md](https://github.com/Coding-Cactus/classrooms/blob/master/roadmap.md)
