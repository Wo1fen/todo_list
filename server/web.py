import bcrypt

import config
from db import Database

from datetime import datetime, timedelta
from aiohttp import web
from sqlalchemy.exc import IntegrityError
import jwt


database = Database()
router = web.RouteTableDef()


def login_required(func):
    async def wrapper(request):
        if not request.user:
            return web.json_response({'message': 'Auth required'}, status=401)
        return func(request)
    return wrapper


async def auth_middleware(app, handler):
    async def middleware(request):
        request.user = None
        jwt_token = request.headers.get('authorization', None)
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, config.JWT_SECRET,
                                     algorithms=[config.JWT_ALGORITHM])
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                return web.json_response({'message': 'Token is invalid'}, status=400)

            request.user = await database.fetch_user(user_id=payload['user_id'])
        return await handler(request)
    return middleware


@router.get("/")
async def root(request: web.Request) -> web.Response:
    return web.json_response({
        "message": "ok",
    },
        status=200)


@router.post("/api/register")
async def register(request: web.Request):
    register_info = await request.json()
    username = register_info["username"]
    email = register_info["email"]
    password = bcrypt.hashpw(register_info["password"].encode(), bcrypt.gensalt()).decode()
    try:
        await database.add_new_user(username, email, password)
    except IntegrityError:
        return web.json_response({'message': 'A user with the same name or email already exists'}, status=400)

    return web.json_response({'message': 'User successfully registered!'}, status=200)


@router.post("/api/login")
async def login(request: web.Request):
    login_info = await request.json()

    user = await database.fetch_user(email=login_info["email"])
    if not bcrypt.checkpw(login_info['password'].encode(), user.password.encode()):
        return web.json_response({'message': 'Wrong credentials'}, status=400)

    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=config.JWT_EXP_DELTA_SECONDS)
    }
    jwt_token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return web.json_response({
        'message': 'You are Successfully logged in!',
        'token': jwt_token
    },
        status=200)


@login_required
@router.get("/api/tasks")
async def api_tasks(request: web.Request) -> web.Response:
    user_id = request.user.id
    tasks = await database.fetch_tasks_list(user_id)
    return web.json_response({
        "message": "success",
        "data": tasks
    }, status=200)


@login_required
@router.post("/api/tasks")
async def api_new_task(request: web.Request) -> web.Response:
    task = await request.json()

    user_id = request.user.id
    task_name = task["name"]
    task_desc = task["description"]
    deadline = task["deadline"]

    await database.add_new_task(user_id, task_name=task_name, desc=task_desc, deadline=deadline)

    return web.json_response({
        "message": "Task was successfully added!",
    },
        status=200)


@login_required
@router.delete("/api/tasks/{task_id}")
async def api_delete_task(request: web.Request) -> web.Response:
    user_id = request.user.id
    task_id = int(request.match_info["task_id"])

    await database.delete_task(user_id, task_id)

    return web.json_response({
        "status": "success",
    }, status=200)


@login_required
@router.patch("/api/tasks/{task_id}")
async def api_new_task(request: web.Request) -> web.Response:
    user_id = request.user.id
    task_id = request.match_info["task_id"]
    task = await request.json()

    await database.update_task(user_id, task_id,
                               new_task_name=task['name'],
                               new_desc=task['description'],
                               new_deadline=task['deadline'])
    return web.json_response({"message": "Task successfully updated!"},
                             status=200)


async def init_app() -> web.Application:
    app = web.Application(middlewares=[auth_middleware])
    app.add_routes(router)
    return app


web.run_app(init_app())
