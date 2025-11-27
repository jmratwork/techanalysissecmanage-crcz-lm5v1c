import argparse
import json
import os
import sys
from urllib import request, parse

# Base URL for the training platform API. Can be overridden with the
# TRAINING_PLATFORM_URL environment variable to point the CLI at a remote
# service when running inside KYPO.
BASE_URL = os.environ.get('TRAINING_PLATFORM_URL', 'http://localhost:5000')


def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(BASE_URL + path, data=data, headers={'Content-Type': 'application/json'})
    with request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get(path, params):
    query = parse.urlencode(params)
    with request.urlopen(BASE_URL + path + '?' + query) as resp:
        return json.loads(resp.read().decode('utf-8'))


def cmd_register(args):
    post('/register', {'username': args.username, 'password': args.password, 'role': args.role})


def cmd_login(args):
    resp = post('/login', {'username': args.username, 'password': args.password})
    print(resp.get('token', ''))


def cmd_create_course(args):
    post('/courses', {'token': args.token, 'title': args.title, 'content': args.content})


def cmd_list_courses(args):
    resp = get('/courses', {'token': args.token})
    print(json.dumps(resp))


def cmd_invite(args):
    resp = post('/invites', {'token': args.token, 'course_id': args.course_id, 'email': args.email})
    print(resp.get('invite_code', ''))


def cmd_update_progress(args):
    post('/progress', {'token': args.token, 'course_id': args.course_id, 'username': args.username, 'progress': args.progress})


def cmd_get_progress(args):
    resp = get('/progress', {'token': args.token, 'course_id': args.course_id, 'username': args.username})
    print(resp.get('progress', 0))


def cmd_submit_results(args):
    payload = {
        'token': args.token,
        'course_id': args.course_id,
        'score': args.score,
        'start_time': args.start_time,
        'end_time': args.end_time,
    }
    if args.progress is not None:
        payload['progress'] = args.progress
    if args.details:
        payload['details'] = json.loads(args.details)
    post('/results', payload)


def main():
    parser = argparse.ArgumentParser(description='Training platform CLI')
    sub = parser.add_subparsers(dest='cmd')

    p = sub.add_parser('register')
    p.add_argument('--username', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--role', choices=['instructor', 'trainee'], default='trainee')
    p.set_defaults(func=cmd_register)

    p = sub.add_parser('login')
    p.add_argument('--username', required=True)
    p.add_argument('--password', required=True)
    p.set_defaults(func=cmd_login)

    p = sub.add_parser('create-course')
    p.add_argument('--token', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--content', default='')
    p.set_defaults(func=cmd_create_course)

    p = sub.add_parser('list-courses')
    p.add_argument('--token', required=True)
    p.set_defaults(func=cmd_list_courses)

    p = sub.add_parser('invite')
    p.add_argument('--token', required=True)
    p.add_argument('--course-id', required=True)
    p.add_argument('--email', required=True)
    p.set_defaults(func=cmd_invite)

    p = sub.add_parser('update-progress')
    p.add_argument('--token', required=True)
    p.add_argument('--course-id', required=True)
    p.add_argument('--username', required=True)
    p.add_argument('--progress', type=int, required=True)
    p.set_defaults(func=cmd_update_progress)

    p = sub.add_parser('get-progress')
    p.add_argument('--token', required=True)
    p.add_argument('--course-id', required=True)
    p.add_argument('--username', required=True)
    p.set_defaults(func=cmd_get_progress)

    p = sub.add_parser('submit-results')
    p.add_argument('--token', required=True)
    p.add_argument('--course-id', required=True)
    p.add_argument('--score', type=int, default=0)
    p.add_argument('--start-time', type=float, required=True)
    p.add_argument('--end-time', type=float, required=True)
    p.add_argument('--progress', type=int)
    p.add_argument('--details', help='JSON string with extra details')
    p.set_defaults(func=cmd_submit_results)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    try:
        args.func(args)
    except Exception as exc:  # pragma: no cover - network errors
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
