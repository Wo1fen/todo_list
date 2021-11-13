from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_DELTA_SECONDS
from db import Database

from datetime import datetime, timedelta
from aiohttp import web
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
                payload = jwt.decode(jwt_token, JWT_SECRET,
                                     algorithms=[JWT_ALGORITHM])
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                return web.json_response({'message': 'Token is invalid'}, status=400)

            request.user = await database.fetch_user(user_id=payload['user_id'])
        return await handler(request)
    return middleware


@router.post("/api/register")
async def register(request: web.Request):
    register_info = await request.json()
    username = register_info['username']
    email = register_info['email']
    password = register_info['password']

    await database.add_user(username, email, password)   # медот еще не реализован

    return web.json_response({})


@router.post("/api/login")
async def login(request: web.Request):
    login_info = await request.json()

    user = await database.fetch_user(email=login_info["email"])
    # User auth login here

    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return web.json_response({'token': jwt_token})


@router.get("/")
async def root(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
    })


@login_required
@router.get("/api/tasks")
async def api_tasks(request: web.Request) -> web.Response:
    user_id = request.user.id
    tasks = await database.fetch_tasks(user_id)
    return web.json_response({
        "status": "ok",
        "data": tasks
    })


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


# @router.patch("/api/tasks/{task_id}")
# async def api_new_task(request: web.Request) -> web.Response:
#     task_id = request.match_info["task_id"]
#     task = await request.json()
#
#     fields = {}
#     if "name" in task:
#         fields["name"] = task["name"]
#     if "description" in task:
#         fields["description"] = task["description"]
#     if "deadline" in task:
#         fields["deadline"] = task["deadline"]
#     user_id = 1
#
#     # await database.add_new_task(task_name, task_desc, deadline, user_id)
#
#     return web.json_response({
#         "status": "ok",
#     })


@router.delete("/api/tasks/{task_id}")
async def api_delete_task(request: web.Request) -> web.Response:
    task_id = request.match_info["task_id"]

    return web.json_response({
        "status": "ok",
    })


async def init_app() -> web.Application:
    app = web.Application(middlewares=[auth_middleware])
    app.add_routes(router)
    return app


web.run_app(init_app())
