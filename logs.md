Exception in ASGI application

Traceback (most recent call last):
  File "/var/task/_vendor/uvicorn/protocols/http/httptools_impl.py", line 419, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/vc__handler__python.py", line 340, in __call__
    await self.app(new_scope, receive, send)
  File "/var/task/_vendor/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/var/task/_vendor/starlette/applications.py", line 123, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/var/task/_vendor/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/var/task/_vendor/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/var/task/_vendor/starlette/middleware/cors.py", line 83, in __call__
    await self.app(scope, receive, send)
  File "/var/task/_vendor/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/var/task/_vendor/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/var/task/_vendor/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/var/task/_vendor/starlette/routing.py", line 762, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/var/task/_vendor/starlette/routing.py", line 782, in app
    await route.handle(scope, receive, send)
  File "/var/task/_vendor/starlette/routing.py", line 297, in handle
    await self.app(scope, receive, send)
  File "/var/task/_vendor/starlette/routing.py", line 77, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/var/task/_vendor/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/var/task/_vendor/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/var/task/_vendor/starlette/routing.py", line 72, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/fastapi/routing.py", line 299, in app
    raise e
  File "/var/task/_vendor/fastapi/routing.py", line 294, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/_vendor/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/backend/app/api/v1/progress.py", line 86, in get_progress_stats
    stats = await progress_service.get_stats(current_user.id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/var/task/backend/app/services/progress_service.py", line 172, in get_stats
    from ..models.skill import SkillMaster
ModuleNotFoundError: No module named 'app'