import os
import uuid
import time
import threading
import subprocess
import tempfile
from flask import Flask, request, jsonify

import phishing_quiz
from open_edx_client import OpenEdXClient
from results_service import append_result, aggregate_results

app = Flask(__name__)

# In-memory stores
users = {}  # username -> {password, role}
tokens = {}  # token -> username
courses = {}  # course_id -> {title, content, instructor}
invites = {}  # invite_code -> {course_id, email}
progress = {}  # (course_id, username) -> progress
quiz_results = {}  # (course_id, username) -> {answers, score}
edx_failures = []  # list of Open edX reporting failures
jobs = {}  # job_id -> {status, tool, output}

open_edx = OpenEdXClient()

# Default subnet for KYPO exercises; can be overridden with environment variable
KYPO_SUBNET = os.getenv('KYPO_SUBNET', '10.10.0.0/24')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CALDERA_PROFILE = os.path.join(BASE_DIR, '..', 'caldera_profiles', 'discovery.json')
ZAP_CONFIG = os.path.join(BASE_DIR, '..', 'zap_baseline.conf')
OPENVAS_TEMPLATE = os.path.join(BASE_DIR, '..', 'openvas_task_template.xml')


def _prepare_template(path):
    """Return path to a temporary file with KYPO_SUBNET substituted."""

    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read().replace('KYPO_SUBNET', KYPO_SUBNET)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(content.encode('utf-8'))
    tmp.close()
    return tmp.name


ZAP_CONF = _prepare_template(ZAP_CONFIG)
CALDERA_PROFILE_PATH = _prepare_template(CALDERA_PROFILE)
with open(OPENVAS_TEMPLATE, 'r', encoding='utf-8') as fh:
    OPENVAS_XML = fh.read().replace('KYPO_SUBNET', KYPO_SUBNET)


COMMANDS = {
    'nmap': ['nmap', '-sV', KYPO_SUBNET],
    'zap': ['zap-baseline.py', '-t', f'http://{KYPO_SUBNET}', '-c', ZAP_CONF],
    'caldera': ['caldera', 'run', '--profile', CALDERA_PROFILE_PATH],
    'openvas': ['gvm-cli', 'socket', '--xml', OPENVAS_XML],
}


def _run_tool(job_id, command):
    """Execute a security tool and capture its output.

    Results are stored in-memory for quick access and additionally written to
    ``/var/log/trainee`` for later inspection.  The file extension is chosen
    based on the tool invoked to better reflect the typical output format.
    """

    jobs[job_id]['status'] = 'running'
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:  # tool missing
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['output'] = str(exc)
        return
    except subprocess.CalledProcessError as exc:  # execution error
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['output'] = exc.stderr
        return

    jobs[job_id]['status'] = 'completed'
    jobs[job_id]['output'] = result.stdout

    # Persist full output to disk for instructor review
    log_dir = '/var/log/trainee'
    os.makedirs(log_dir, exist_ok=True)
    tool = jobs[job_id]['tool']
    ext = 'html' if tool in {'zap', 'openvas'} else 'txt'
    file_path = os.path.join(log_dir, f'{tool}_{job_id}.{ext}')
    try:
        with open(file_path, 'w', encoding='utf-8') as fh:
            fh.write(result.stdout)
        jobs[job_id]['output_file'] = file_path
    except OSError:
        # Failure to persist the file should not mark the job as failed
        pass


def authenticate(token):
    username = tokens.get(token)
    if not username:
        return None
    return users.get(username)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'trainee')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    if username in users:
        return jsonify({'error': 'user exists'}), 400
    users[username] = {'password': password, 'role': role}
    return jsonify({'status': 'registered'})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')
    user = users.get(username)
    if not user or user['password'] != password:
        return jsonify({'error': 'invalid credentials'}), 403
    token = str(uuid.uuid4())
    tokens[token] = username
    return jsonify({'token': token})


@app.route('/courses', methods=['POST'])
def create_course():
    data = request.get_json(force=True)
    token = data.get('token')
    user = authenticate(token)
    if not user or user['role'] != 'instructor':
        return jsonify({'error': 'unauthorized'}), 403
    title = data.get('title')
    content = data.get('content', '')
    course_id = str(uuid.uuid4())
    courses[course_id] = {
        'title': title,
        'content': content,
        'instructor': tokens[token]
    }
    return jsonify({'course_id': course_id})


@app.route('/courses', methods=['GET'])
def list_courses():
    token = request.args.get('token')
    user = authenticate(token)
    if not user:
        return jsonify({'error': 'unauthorized'}), 403
    return jsonify(courses)


@app.route('/invites', methods=['POST'])
def create_invite():
    data = request.get_json(force=True)
    token = data.get('token')
    user = authenticate(token)
    if not user or user['role'] != 'instructor':
        return jsonify({'error': 'unauthorized'}), 403
    course_id = data.get('course_id')
    email = data.get('email')
    code = str(uuid.uuid4())
    invites[code] = {'course_id': course_id, 'email': email}
    return jsonify({'invite_code': code})


@app.route('/progress', methods=['POST'])
def update_progress():
    data = request.get_json(force=True)
    token = data.get('token')
    user = authenticate(token)
    if not user:
        return jsonify({'error': 'unauthorized'}), 403
    course_id = data.get('course_id')
    username = data.get('username') or tokens[token]
    value = data.get('progress')
    progress[(course_id, username)] = value
    return jsonify({'status': 'updated'})


@app.route('/progress', methods=['GET'])
def get_progress():
    token = request.args.get('token')
    user = authenticate(token)
    if not user:
        return jsonify({'error': 'unauthorized'}), 403
    course_id = request.args.get('course_id')
    username = request.args.get('username') or tokens[token]
    value = progress.get((course_id, username), 0)
    return jsonify({'progress': value})


@app.route('/results', methods=['POST'])
def post_results():
    data = request.get_json(force=True)
    token = data.get('token')
    user = authenticate(token)
    if not user:
        return jsonify({'error': 'unauthorized'}), 403
    course_id = data.get('course_id')
    username = data.get('username') or tokens[token]
    start = data.get('start_time')
    end = data.get('end_time')
    score = data.get('score', 0)
    duration = None
    if start is not None and end is not None:
        try:
            duration = float(end) - float(start)
        except (TypeError, ValueError):
            duration = None
    result = {
        'course_id': course_id,
        'username': username,
        'score': score,
        'duration': duration,
        'details': data.get('details', {}),
        'timestamp': time.time(),
    }
    append_result(result)
    metrics = aggregate_results(course_id, username)
    quiz = quiz_results.get((course_id, username))
    if quiz:
        metrics['quiz_score'] = quiz.get('score', 0)
    progress[(course_id, username)] = metrics.get('score', score)
    ok_progress, message_progress = open_edx.update_progress(username, course_id, metrics)
    ok_grade, message_grade = open_edx.push_grade_lms(
        username, course_id, metrics.get('score', score)
    )
    if not ok_progress:
        edx_failures.append(
            {
                'course_id': course_id,
                'username': username,
                'error': message_progress,
                'timestamp': time.time(),
            }
        )
    if not ok_grade:
        edx_failures.append(
            {
                'course_id': course_id,
                'username': username,
                'error': message_grade,
                'timestamp': time.time(),
            }
        )
    return jsonify(
        {
            'status': 'recorded',
            'metrics': metrics,
            'edx_sync': ok_progress and ok_grade,
        }
    )


@app.route('/edx_failures', methods=['GET'])
def get_edx_failures():
    token = request.args.get('token')
    user = authenticate(token)
    if not user or user.get('role') != 'instructor':
        return jsonify({'error': 'unauthorized'}), 403
    return jsonify({'failures': edx_failures})


@app.route('/launch_tool', methods=['POST'])
def launch_tool():
    data = request.get_json(force=True)
    token = data.get('token')
    user = authenticate(token)
    if not user:
        return jsonify({'error': 'unauthorized'}), 403

    tool = data.get('tool', '').lower()
    command = COMMANDS.get(tool)
    if not command:
        return jsonify({'error': 'invalid tool'}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'pending', 'tool': tool}
    thread = threading.Thread(target=_run_tool, args=(job_id, command), daemon=True)
    thread.start()

    return jsonify({'job_id': job_id, 'status': jobs[job_id]['status']})


@app.route('/launch_tool/<job_id>', methods=['GET'])
def launch_tool_status(job_id):
    token = request.args.get('token')
    user = authenticate(token)
    if not user:
        return jsonify({'error': 'unauthorized'}), 403

    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'not found'}), 404

    return jsonify(job)


@app.route('/kypo/launch', methods=['POST'])
def kypo_launch():
    """Generate an LTI launch URL for a KYPO lab.

    The endpoint expects a JSON body with a valid authentication token
    and ``lab_id`` identifying the KYPO exercise. The response contains
    a pre-signed LTI launch URL that the caller can redirect the user to
    in order to start the session.
    """

    data = request.get_json(force=True)
    token = data.get('token')
    lab_id = data.get('lab_id')

    user = authenticate(token)
    if not user or not lab_id:
        return jsonify({'error': 'unauthorized'}), 403

    username = tokens[token]
    try:
        launch_url = open_edx.generate_launch_url(username, lab_id)
    except Exception as exc:  # pragma: no cover - configuration errors
        return jsonify({'error': str(exc)}), 500

    return jsonify({'launch_url': launch_url})


phishing_quiz.init_app(app, authenticate, tokens, quiz_results, open_edx, edx_failures)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
