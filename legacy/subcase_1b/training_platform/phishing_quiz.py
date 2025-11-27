from flask import request, jsonify
import time

from open_edx_client import OpenEdXClient
from results_service import append_result, aggregate_results

# Sample phishing quiz questions
quiz_questions = [
    {
        'id': 'q1',
        'question': 'What is the safest response to an unexpected password reset email?',
        'options': [
            'Click the link and change your password',
            'Ignore the email',
            'Verify the request through an official channel'
        ],
        'answer': 2
    },
    {
        'id': 'q2',
        'question': 'Which URL is likely malicious?',
        'options': [
            'https://accounts.example.com',
            'http://login.example.com.security-update.co',
            'https://intranet.example.com/profile'
        ],
        'answer': 1
    },
    {
        'id': 'q3',
        'question': 'Why should you hover over links before clicking?',
        'options': [
            'To check the true destination',
            'To download the attachment',
            'To enable pop-up blockers'
        ],
        'answer': 0
    },
    {
        'id': 'q4',
        'question': 'You receive an email from your bank asking you to update your details via an attached form. What should you do?',
        'options': [
            'Open the form and fill in your details',
            'Contact the bank using an official phone number',
            'Reply to the email with your information'
        ],
        'answer': 1
    },
    {
        'id': 'q5',
        'question': 'Which attachment file type is most likely to contain malware?',
        'options': [
            'invoice.pdf',
            'update.exe',
            'report.txt'
        ],
        'answer': 1
    },
    {
        'id': 'q6',
        'question': 'Which is a sign of a spear phishing attempt?',
        'options': [
            'A mass email advertising a new product',
            'An email referencing a project you are working on',
            'A system notification from your antivirus software'
        ],
        'answer': 1
    },
    {
        'id': 'q7',
        'question': 'You notice a login page uses http instead of https. What should you do?',
        'options': [
            'Proceed with entering your credentials',
            'Close the page and report it to IT',
            'Ignore the difference and continue'
        ],
        'answer': 1
    },
    {
        'id': 'q8',
        'question': 'An email threatens account suspension unless you act immediately. What tactic is the attacker using?',
        'options': [
            'Urgency and fear',
            'Routine company policy',
            'Technical jargon'
        ],
        'answer': 0
    },
    {
        'id': 'q9',
        'question': 'What is the best way to verify a suspicious email from a coworker?',
        'options': [
            'Reply to the email asking if it\'s legitimate',
            'Call the coworker using a known number',
            'Forward it to others to ask their opinion'
        ],
        'answer': 1
    },
    {
        'id': 'q10',
        'question': 'After clicking on a suspicious link, what should you do first?',
        'options': [
            'Delete your browsing history',
            'Disconnect from the network and inform IT',
            'Continue working to avoid suspicion'
        ],
        'answer': 1
    }
]


def init_app(
    app,
    authenticate,
    tokens,
    quiz_results,
    open_edx: OpenEdXClient | None = None,
    edx_failures: list | None = None,
):
    """Register quiz endpoints on the given Flask app."""

    @app.route('/quiz/start', methods=['GET'])
    def quiz_start():
        token = request.args.get('token')
        user = authenticate(token)
        if not user:
            return jsonify({'error': 'unauthorized'}), 403
        course_id = request.args.get('course_id')
        questions = [{k: v for k, v in q.items() if k != 'answer'} for q in quiz_questions]
        return jsonify({'course_id': course_id, 'questions': questions})

    @app.route('/quiz/submit', methods=['POST'])
    def quiz_submit():
        data = request.get_json(force=True)
        token = data.get('token')
        user = authenticate(token)
        if not user:
            return jsonify({'error': 'unauthorized'}), 403
        course_id = data.get('course_id')
        answers = data.get('answers', {})
        score = 0
        for q in quiz_questions:
            qid = q['id']
            if str(answers.get(qid)) == str(q['answer']):
                score += 1
        username = tokens.get(token)
        quiz_results[(course_id, username)] = {'answers': answers, 'score': score}

        result = {
            'course_id': course_id,
            'username': username,
            'score': score,
            'details': {'answers': answers},
            'timestamp': time.time(),
        }
        append_result(result)
        metrics = aggregate_results(course_id, username)
        if open_edx:
            open_edx.push_grade(username, course_id, score)
            ok, message = open_edx.push_grade_lms(username, course_id, score)
            if not ok and edx_failures is not None:
                edx_failures.append(
                    {
                        "course_id": course_id,
                        "username": username,
                        "error": message,
                        "timestamp": time.time(),
                    }
                )
        return jsonify({'score': score, 'metrics': metrics})

    @app.route('/quiz/score', methods=['GET'])
    def quiz_score():
        token = request.args.get('token')
        user = authenticate(token)
        if not user:
            return jsonify({'error': 'unauthorized'}), 403
        course_id = request.args.get('course_id')
        username = tokens.get(token)
        result = quiz_results.get((course_id, username))
        return jsonify({'score': result['score'] if result else 0})
