# GitHub Workflow Guide for Final Submission

The final rubric gives points for task branches, Pull Requests, meaningful commits, and CI/CD. Use this guide after unzipping the project.

## 1. Create GitHub Repository

Repository name:

```text
medical-telegram-warehouse
```

## 2. Initialize Main Branch

```bash
git init
git add .
git commit -m "Initial project structure for medical Telegram warehouse"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## 3. Create Task Branches and Pull Requests

Create each branch, make a small confirming commit, push it, then open a Pull Request on GitHub and merge it into `main`.

### Task 1 Branch

```bash
git checkout -b task-1-scraping
git add src/scraper.py data/raw logs README.md
git commit -m "Implement Telethon scraping and raw data lake structure"
git push -u origin task-1-scraping
```

Open PR: `task-1-scraping` → `main`, then merge.

### Task 2 Branch

```bash
git checkout main
git pull
git checkout -b task-2-dbt
git add src/load_raw_to_postgres.py medical_warehouse README.md
git commit -m "Add PostgreSQL raw loader and dbt star schema models"
git push -u origin task-2-dbt
```

Open PR: `task-2-dbt` → `main`, then merge.

### Task 3 Branch

```bash
git checkout main
git pull
git checkout -b task-3-yolo
git add src/yolo_detect.py src/load_yolo_to_postgres.py data/processed/yolo_detections.csv medical_warehouse/models/marts/fct_image_detections.sql README.md
git commit -m "Add YOLOv8 image enrichment and warehouse integration"
git push -u origin task-3-yolo
```

Open PR: `task-3-yolo` → `main`, then merge.

### Task 4 Branch

```bash
git checkout main
git pull
git checkout -b task-4-api
git add api tests README.md
git commit -m "Implement FastAPI analytical endpoints"
git push -u origin task-4-api
```

Open PR: `task-4-api` → `main`, then merge.

### Task 5 Branch

```bash
git checkout main
git pull
git checkout -b task-5-dagster
git add pipeline.py README.md
git commit -m "Add Dagster orchestration job and daily schedule"
git push -u origin task-5-dagster
```

Open PR: `task-5-dagster` → `main`, then merge.

### CI/CD Branch

```bash
git checkout main
git pull
git checkout -b ci-tests
git add .github/workflows/unittests.yml tests requirements.txt
git commit -m "Configure GitHub Actions unit tests"
git push -u origin ci-tests
```

Open PR: `ci-tests` → `main`, then merge.

## 4. Final Submission

Submit the GitHub repository link after all PRs are merged into `main`.

Recommended submission note:

```text
B9W8 Final Submission – Shipping a Data Product: From Raw Telegram Data to an Analytical API

GitHub Repository:
PASTE_REPO_LINK_HERE

Completed Tasks:
- Task 1: Telethon scraping and raw data lake
- Task 2: PostgreSQL raw loader and dbt star schema
- Task 3: YOLOv8 image enrichment and fct_image_detections
- Task 4: FastAPI analytical API endpoints
- Task 5: Dagster orchestration with daily schedule
- CI/CD: GitHub Actions unit test workflow
- Git workflow: task branches and Pull Requests merged into main
```
