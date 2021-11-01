import datetime


class User:
    def __init__(self, nickname, email):
        self._nickname = nickname
        self._email = email

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, value):
        self._nickname = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value

    def to_json(self):
        return {
            'nickname': self.nickname,
            'email': self.email
        }


class Task:
    def __init__(self, name, deadline):
        self._name = name
        self._deadline = deadline
        self._is_finished = False

    def change_state(self):
        self._is_finished = not self._is_finished

    @property
    def deadline(self):
        return self._deadline

    @deadline.setter
    def deadline(self, value):
        self._deadline = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def to_json(self):
        return {
            'name': self.name,
            'deadline': self.deadline,
            'is_finished': self._is_finished,
            'status': 'Просрочено' if datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') > self._deadline
            else 'В процессе'
        }


class ToDoList:
    def __init__(self, user):
        self._user = user
        self._tasks = []

    def add_task(self, task):
        self._tasks.append(task)

    def to_json(self):
        return {
            'user': self._user.to_json(),
            'tasks': list(map(lambda task: task.to_json(), self._tasks))
        }


user = User('s1carr', 's1carr@gmail.com')
print(user.to_json())
task = Task('asd', '2020-11-01 18:00:00')
print(task.to_json())

tdl1 = ToDoList(user)
tdl1.add_task(task)
print(tdl1.to_json())

