# Phishing Awareness Questionnaire

Use this questionnaire to assess how well trainees can identify phishing threats. Questions can be served by the training platform and scored automatically.

## Questionnaire

1. **What is the safest response to an unexpected password reset email?**
   - A. Click the link and change your password
   - B. Ignore the email
   - C. Verify the request through an official channel
2. **Which URL is likely malicious?**
   - A. https://accounts.example.com
   - B. http://login.example.com.security-update.co
   - C. https://intranet.example.com/profile
3. **Why should you hover over links before clicking?**
   - A. To check the true destination
   - B. To download the attachment
   - C. To enable pop-up blockers
4. **You receive an email from your bank asking you to update your details via an attached form. What should you do?**
   - A. Open the form and fill in your details
   - B. Contact the bank using an official phone number
   - C. Reply to the email with your information
5. **Which attachment file type is most likely to contain malware?**
   - A. invoice.pdf
   - B. update.exe
   - C. report.txt
6. **Which is a sign of a spear phishing attempt?**
   - A. A mass email advertising a new product
   - B. An email referencing a project you are working on
   - C. A system notification from your antivirus software
7. **You notice a login page uses http instead of https. What should you do?**
   - A. Proceed with entering your credentials
   - B. Close the page and report it to IT
   - C. Ignore the difference and continue
8. **An email threatens account suspension unless you act immediately. What tactic is the attacker using?**
   - A. Urgency and fear
   - B. Routine company policy
   - C. Technical jargon
9. **What is the best way to verify a suspicious email from a coworker?**
   - A. Reply to the email asking if it's legitimate
   - B. Call the coworker using a known number
   - C. Forward it to others to ask their opinion
10. **After clicking on a suspicious link, what should you do first?**
    - A. Delete your browsing history
    - B. Disconnect from the network and inform IT
    - C. Continue working to avoid suspicion

## Scoring via Training Platform

The training platform exposes endpoints that handle quiz distribution and scoring:

```bash
# Obtain questions
curl http://localhost:5000/quiz/start

# Submit answers for grading
curl -X POST http://localhost:5000/quiz/submit \
  -H 'Content-Type: application/json' \
  -d '{"user":"alice","answers":{"q1":"C","q2":"B","q3":"A","q4":"B","q5":"B","q6":"B","q7":"B","q8":"A","q9":"B","q10":"B"}}'

# Retrieve the stored score
curl http://localhost:5000/quiz/score?user=alice
```

These endpoints allow instructors to integrate phishing assessments into automated training workflows and track learner performance over time.
