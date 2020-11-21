# perchat

*Chatroom for users*
> This is a chatroom for multiple users. There are two modes in the chatroom including the persuasion ignorance mode and persuasion awareness mode. In the persuasion awareness mode, the website will detect the persuasion of messages from users and show an alert to them. They could either directly send their messages to others or revise their messages. While in the other mode, users won't have such alerts and chat smoothly. Our goal is to test whether users have different behaviours in such two environments.

> Example application for *[Python Web Development with Flask](https://perchat.herokuapp.com/)*.

Demo: https://perchat.herokuapp.com/

![Screenshot]()

## Installation

clone
create & activate virtual env then install dependency:

with venv/virtualenv + pip:
```
$ python -m venv env  # use `virtualenv env` for Python2, use `python3 ...` for Python3 on Linux & macOS
$ source env/bin/activate  # use `env\Scripts\activate` on Windows
$ pip install -r requirements.txt
```
or with Pipenv:
```
$ pipenv install --dev
$ pipenv shell
```
generate fake data then run:
```
$ flask forge
$ flask run
* Running on http://127.0.0.1:5000/
```
Test account:
feel free to create an account!

## License

This project is licensed under the MIT License (see the
[LICENSE](LICENSE) file for details).
