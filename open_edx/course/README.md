# Open edX Course Guide

This folder contains content for an Open edX course. Use it to add lessons or quizzes and to package the course for import into Open edX Studio.

## Directory structure

```
course/
├── lessons/   # Markdown or HTML content units
└── quizzes/   # XML quiz definitions
```

## Adding markdown or HTML units

1. Place new lesson files under the `lessons/` directory.
2. Use the `.md` extension for Markdown content or `.html` for raw HTML.
3. Reference existing examples such as `phishing_overview.md` or `phishing_examples.html` for formatting guidance.

## Updating quizzes

1. Quiz definitions are stored in the `quizzes/` directory as XML files.
2. Edit the existing quiz (for example, `phishing_quiz.xml`) or add a new `<name>_quiz.xml` file.
3. Follow standard Open edX problem XML structure when editing or adding questions.

## Re‑zipping for Studio import

1. From the repository root, change into the `open_edx` directory:
   ```bash
   cd open_edx
   ```
2. Zip the `course` folder so that it is the root of the archive. This ensures Studio recognizes the course layout:
   ```bash
   zip -r course.zip course
   ```
3. In Open edX Studio, go to *Tools > Import* and upload the generated `course.zip`.

The resulting ZIP must contain a top-level `course/` directory with the `lessons/` and `quizzes/` subfolders, along with any additional course configuration files required by Open edX.

