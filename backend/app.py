import json
import logging
import os
import random
from uuid import uuid4
from collections import defaultdict

import joblib
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from schemas import (
    SkillsInput, TestSubmission, RecommendResponse, EvaluateResponse,
    UserSignup, UserLogin, AuthResponse, JourneyDashboardResponse,
    CompanyPracticeSubmission, CompanyPracticeEvaluateResponse,
    GitHubProjectCreate, GitHubProjectResponse,
)
from database import init_db, get_db, UserSession, TestResult, User, CompanyPracticeResult, GitHubProject
from utils import (
    SKILLS_LIST, DOMAIN_DATA, DOMAIN_SKILLS,
    normalize_skills, compute_skill_gap, compute_readiness_score,
    get_resources_for_skills, get_xai_explanation, hash_password, verify_password,
    build_learning_roadmap, build_fit_reasoning, skills_to_feature_vector,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Career Intelligence API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

logger = logging.getLogger("career_intelligence")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# ── Question bank ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_QB_PATH = os.path.join(BASE_DIR, "questions.json")

with open(_QB_PATH, "r", encoding="utf-8") as _f:
    QUESTION_BANK: dict[str, list[dict]] = json.load(_f)

LEVEL_COUNTS = {
    "easy": {"easy": 10, "medium": 0, "hard": 0},
    "medium": {"easy": 2, "medium": 4, "hard": 0},
    "hard": {"easy": 1, "medium": 2, "hard": 3},
    "mixed": {"easy": 5, "medium": 3, "hard": 2},
}

LEVEL_CODING_COUNTS = {
    "easy": {"medium": 0, "hard": 0},
    "medium": {"medium": 2, "hard": 0},
    "hard": {"medium": 1, "hard": 2},
    "mixed": {"medium": 1, "hard": 1},
}

COMPANY_PRACTICE_BANK = {
    "TCS": [
        ("easy", "Aptitude", "If a train travels 120 km in 2 hours, what is its average speed?", ["40 km/h", "50 km/h", "60 km/h", "80 km/h"], 2),
        ("easy", "Verbal", "Choose the synonym of 'Brief'.", ["Long", "Short", "Complex", "Late"], 1),
        ("medium", "Coding Logic", "Which approach efficiently checks if two strings are anagrams?", ["Sort/count characters and compare", "Compare only lengths", "Check first letters", "Reverse one string"], 0),
        ("medium", "SQL", "Which SQL clause filters groups after aggregation?", ["WHERE", "HAVING", "ORDER BY", "LIMIT"], 1),
        ("hard", "Coding", "For a coding round, which solution best detects a cycle in a linked list?", ["Nested loops only", "Floyd slow-fast pointers", "Sort node values", "Use binary search"], 1),
        ("hard", "Problem Solving", "A function must handle very large input. What matters most?", ["Time/space complexity", "Variable name length", "Only comments", "Using more print statements"], 0),
    ],
    "Infosys": [
        ("easy", "Aptitude", "What is 15% of 240?", ["24", "30", "36", "48"], 2),
        ("easy", "Verbal", "Choose the correctly spelled word.", ["Recieve", "Receive", "Receeve", "Receve"], 1),
        ("medium", "Pseudo Code", "What does a stack primarily follow?", ["FIFO", "LIFO", "Random access", "Round robin"], 1),
        ("medium", "DBMS", "Which key uniquely identifies a row in a table?", ["Foreign key", "Candidate key only", "Primary key", "Composite index only"], 2),
        ("hard", "Coding", "Which technique is best for finding shortest path in an unweighted graph?", ["DFS", "BFS", "Merge sort", "Hashing"], 1),
        ("hard", "OOP", "Which principle hides internal implementation details?", ["Inheritance", "Encapsulation", "Polymorphism", "Compilation"], 1),
    ],
    "Wipro": [
        ("easy", "Aptitude", "If x + 5 = 12, what is x?", ["5", "6", "7", "8"], 2),
        ("easy", "Verbal", "Choose the antonym of 'Expand'.", ["Grow", "Extend", "Contract", "Increase"], 2),
        ("medium", "Programming", "What is the output of a loop that increments i from 0 to 4?", ["4 iterations", "5 iterations", "6 iterations", "Infinite"], 1),
        ("medium", "OS", "Which concept allows multiple processes to appear to run simultaneously?", ["Indexing", "Multitasking", "Normalization", "Serialization"], 1),
        ("hard", "Coding", "Which data structure helps implement LRU cache efficiently?", ["Array only", "Hash map + doubly linked list", "Stack only", "Queue only"], 1),
        ("hard", "Networks", "Which protocol is commonly used for secure web communication?", ["HTTP", "FTP", "HTTPS", "Telnet"], 2),
    ],
    "Accenture": [
        ("easy", "Aptitude", "What is the next number: 2, 4, 8, 16, ?", ["18", "24", "32", "64"], 2),
        ("easy", "Logical", "If all cats are animals, which statement is true?", ["All animals are cats", "Some animals are cats", "No cats are animals", "Cats are not animals"], 1),
        ("medium", "Cloud", "What is autoscaling used for?", ["Changing UI colors", "Adjusting resources based on demand", "Deleting logs", "Encrypting passwords"], 1),
        ("medium", "API", "Which status code usually means unauthorized?", ["200", "201", "401", "500"], 2),
        ("hard", "Scenario", "A service has traffic spikes. Which architecture helps most?", ["Caching, queues, and horizontal scaling", "More CSS", "Single server only", "No monitoring"], 0),
        ("hard", "Coding", "Which approach prevents duplicate payment processing on retry?", ["Idempotency key", "Bigger payload", "More UI buttons", "No database"], 0),
    ],
    "Cognizant": [
        ("easy", "Aptitude", "What is 9 squared?", ["18", "72", "81", "99"], 2),
        ("easy", "Verbal", "Fill in: She is good ___ mathematics.", ["in", "at", "on", "for"], 1),
        ("medium", "Java", "Which keyword is used to inherit a class in Java?", ["implements", "extends", "inherits", "super"], 1),
        ("medium", "Testing", "Unit tests usually test what?", ["Entire system only", "Individual components", "Production deployment", "Database backups"], 1),
        ("hard", "Coding", "Which pattern is appropriate when only one instance should exist?", ["Factory", "Singleton", "Observer", "Adapter"], 1),
        ("hard", "System Design", "What improves reliability during downstream API failure?", ["Retries with backoff and circuit breaker", "No timeout", "Infinite loop", "Ignore errors"], 0),
    ],
    "Capgemini": [
        ("easy", "Aptitude", "If 5 workers finish a task in 10 days, how many worker-days are needed?", ["15", "25", "50", "100"], 2),
        ("easy", "Logical", "Find the odd one out: SQL, Python, Java, Mango.", ["SQL", "Python", "Java", "Mango"], 3),
        ("medium", "Frontend", "Which hook stores state in React?", ["useEffect", "useState", "useRef", "useRoute"], 1),
        ("medium", "Database", "Which operation combines rows from two tables?", ["JOIN", "SORT", "GROUP", "DROP"], 0),
        ("hard", "Coding", "Which algorithmic idea is best for repeated lookup by key?", ["Hashing", "Bubble sort", "Linear scan always", "Recursion only"], 0),
        ("hard", "Architecture", "What helps decouple services for async work?", ["Message queue", "Single shared file", "Manual screenshots", "Inline CSS"], 0),
    ],
}

DOMAIN_SCENARIOS = {
    "Data Scientist": {
        "medium": [
            ("A model scores 95% accuracy but misses most fraud cases. What should you inspect first?", ["Class imbalance and precision/recall", "The CSS bundle size", "Docker image layers", "Only the training speed"], 0, "Model Evaluation"),
            ("You need to compare average order value across customer segments. Which workflow is best?", ["Group data, aggregate metrics, visualise differences", "Train a neural network immediately", "Drop all categorical columns", "Use only raw CSV exports"], 0, "Data Manipulation"),
            ("A feature has extreme outliers before model training. What is a sensible next step?", ["Inspect distribution and consider robust scaling or clipping", "Always delete the column", "Convert it to HTML", "Ignore validation metrics"], 0, "Feature Engineering"),
            ("You are asked to explain a model to business stakeholders. What should you prepare?", ["Feature impact, errors, and business interpretation", "Only source code screenshots", "A Kubernetes manifest", "A colour palette"], 0, "Model Evaluation"),
        ],
        "hard": [
            ("Your training accuracy is high but validation performance drops sharply. Which response is strongest?", ["Reduce overfitting with validation, regularisation, and simpler features", "Increase epochs without checking metrics", "Remove the test set", "Report only training accuracy"], 0, "Machine Learning"),
            ("A production prediction pipeline receives delayed and incomplete data. What design choice matters most?", ["Data validation, fallback handling, and monitoring drift", "Changing the app font", "Adding more dashboard colours", "Skipping preprocessing"], 0, "Model Deployment"),
        ],
    },
    "AI-ML Engineer": {
        "medium": [
            ("A deployed model has slow inference latency. What should you investigate first?", ["Model size, batching, hardware, and serving path", "Navbar spacing", "Excel formulas", "Only the README title"], 0, "Model Deployment"),
            ("A neural network overfits after a few epochs. Which change is most relevant?", ["Add regularisation, dropout, or data augmentation", "Use more CSS", "Remove validation data", "Always increase depth"], 0, "Regularisation"),
            ("You fine-tune a transformer and validation loss rises. What should you tune?", ["Learning rate, epochs, dataset quality, and freezing strategy", "Only database indexes", "Image alt text", "The browser cache"], 0, "NLP"),
            ("A model performs well offline but poorly with real users. What is the likely concern?", ["Data drift or mismatch between train and production data", "Too many React components", "Missing Figma file", "No spreadsheet formulas"], 0, "Model Deployment"),
        ],
        "hard": [
            ("You need reproducible ML experiments across team members. Which setup is strongest?", ["Version data, code, configs, metrics, and model artifacts", "Share screenshots manually", "Use random seeds only", "Delete old experiments"], 0, "MLOps"),
            ("A GPU training job runs out of memory. Which response is most appropriate?", ["Reduce batch size, use mixed precision, or optimise model memory", "Disable validation forever", "Switch to SQL", "Increase UI contrast"], 0, "Deep Learning"),
        ],
    },
    "Data Analyst": {
        "medium": [
            ("A business metric changed suddenly last week. What should you do first?", ["Validate data quality, segment the metric, and compare time periods", "Build a neural network", "Rewrite frontend CSS", "Ignore source changes"], 0, "Business Analysis"),
            ("A dashboard is correct but executives find it confusing. What should improve?", ["Clear KPIs, hierarchy, context, and fewer unnecessary charts", "More table joins only", "A bigger Docker image", "No labels"], 0, "Data Visualisation"),
            ("A SQL query duplicates revenue after joining tables. What is the likely issue?", ["Join grain mismatch or many-to-many join", "Wrong font size", "Missing GPU", "Too much caching"], 0, "SQL"),
            ("A dataset has missing values in an important numeric field. What is the best first step?", ["Profile missingness before choosing imputation or exclusion", "Always replace with zero", "Always delete the dataset", "Convert to JSON only"], 0, "Data Cleaning"),
        ],
        "hard": [
            ("Two teams report different monthly revenue numbers. What is the strongest analytical response?", ["Align definitions, source systems, filters, and aggregation grain", "Average both numbers blindly", "Pick the larger value", "Stop tracking revenue"], 0, "Business Analysis"),
            ("A KPI improved but customer complaints increased. What should your analysis include?", ["Segmented analysis and tradeoff investigation across user groups", "Only the KPI chart", "Only raw exports", "A deployment plan"], 0, "Statistics"),
        ],
    },
    "Full Stack Developer": {
        "medium": [
            ("A React page refetches data on every render. What should you inspect?", ["Effect dependencies and state update loops", "SQL indexes first", "Only image size", "Kubernetes pods"], 0, "Frontend"),
            ("An API endpoint works locally but fails from the browser. What is a likely issue?", ["CORS, auth headers, or environment URL mismatch", "Wrong chart colour", "Missing Excel formula", "Low model accuracy"], 0, "APIs & Architecture"),
            ("A product needs login and saved user data. What should the design include?", ["Auth flow, protected routes, persistence, and validation", "Only static HTML", "No backend", "Random local variables only"], 0, "Backend"),
            ("A database query gets slow as data grows. What should you consider?", ["Indexes, query shape, pagination, and schema design", "More animations", "Changing font family", "Removing API errors"], 0, "Databases"),
        ],
        "hard": [
            ("You must design a scalable full-stack app for many concurrent users. What matters most?", ["Caching, pagination, API boundaries, database indexes, and deployment strategy", "Only more buttons", "All logic in one component", "No monitoring"], 0, "APIs & Architecture"),
            ("A checkout flow creates duplicate orders on retry. Which backend idea helps?", ["Idempotency keys and transaction-safe order creation", "More CSS classes", "Client-only validation", "Skipping database constraints"], 0, "Backend"),
        ],
    },
    "Software Engineer": {
        "medium": [
            ("A function must find duplicates in a large list efficiently. Which structure helps?", ["Hash set", "Nested loops only", "CSS grid", "Manual screenshots"], 0, "Data Structures"),
            ("A service becomes difficult to test because everything is tightly coupled. What improves it?", ["Separation of concerns and dependency injection", "More global state", "No interfaces", "Longer functions"], 0, "Testing"),
            ("You need shortest paths in an unweighted graph. Which algorithm fits?", ["BFS", "Binary search", "QuickSort", "CSS cascade"], 0, "Algorithms"),
            ("A class hierarchy breaks when subclasses replace parent behavior. Which principle is involved?", ["Liskov Substitution Principle", "DRY only", "CAP theorem", "HTTP caching"], 0, "OOP"),
        ],
        "hard": [
            ("Design a rate limiter for an API. Which tradeoff is most relevant?", ["Algorithm choice, storage, distributed consistency, and burst handling", "Only button styling", "Only file names", "No persistence"], 0, "System Design"),
            ("A concurrent program sometimes returns different totals. What bug should you suspect?", ["Race condition around shared mutable state", "Wrong margin", "Missing chart label", "Slow DNS only"], 0, "Concurrency"),
        ],
    },
    "DevOps Engineer": {
        "medium": [
            ("A container runs locally but fails in CI. What should you inspect?", ["Environment variables, build context, image tags, and logs", "Frontend colours", "SQL joins", "Model hyperparameters"], 0, "Containers"),
            ("A deployment should not reach production without tests. What pipeline design helps?", ["Separate build, test, approval, and deploy stages", "One manual shell command only", "No artifacts", "Skipping rollback"], 0, "CI/CD"),
            ("A Kubernetes service cannot reach pods. What should you check?", ["Labels, selectors, ports, and pod readiness", "Excel sheets", "React hooks", "Typography"], 0, "Orchestration"),
            ("Infrastructure changes are risky and undocumented. What improves safety?", ["Terraform plan, code review, state management, and idempotent changes", "Manual console edits only", "No version control", "Screenshots"], 0, "Infrastructure as Code"),
        ],
        "hard": [
            ("A release causes high error rates. What is the strongest operational response?", ["Rollback or mitigate, inspect metrics/logs, and identify root cause", "Keep deploying", "Delete monitoring", "Ignore alerts"], 0, "Monitoring"),
            ("Multiple services need reliable async work processing. What design should you consider?", ["Queue-based architecture with retries, dead-letter handling, and observability", "One cron hidden in UI", "Only local files", "No logging"], 0, "Reliability"),
        ],
    },
    "Cybersecurity Analyst": {
        "medium": [
            ("A login endpoint allows unlimited attempts. What is the security concern?", ["Brute-force attacks and missing rate limiting", "Wrong chart type", "Slow CSS", "Lack of dashboards"], 0, "Threats & Attacks"),
            ("A user reports a suspicious email. What should you inspect?", ["Sender, links, headers, attachments, and phishing indicators", "Only the logo", "Database indexes", "CSS classes"], 0, "Incident Response"),
            ("A web app stores plain text passwords. What should be changed?", ["Use salted password hashing and secure storage practices", "Use larger text", "Store passwords in CSV", "Disable login"], 0, "Authentication & Security"),
            ("A public API exposes sensitive data. What should you review?", ["Authorization checks, data minimization, and logging", "Only frontend spacing", "Only file names", "Model accuracy"], 0, "Compliance & Frameworks"),
        ],
        "hard": [
            ("You discover lateral movement after a compromised account. What should response prioritize?", ["Containment, credential rotation, log review, and scope analysis", "Only UI redesign", "Ignore internal systems", "Delete all logs"], 0, "Incident Response"),
            ("A company needs to reduce risk before an audit. What program is strongest?", ["Asset inventory, controls mapping, vulnerability management, and evidence collection", "One password reset", "More charts", "No policies"], 0, "Compliance & Frameworks"),
        ],
    },
    "UI/UX Designer": {
        "medium": [
            ("Users abandon a form halfway through. What should you investigate?", ["Friction points, field clarity, validation, and user expectations", "Only backend indexes", "GPU memory", "Docker layers"], 0, "UX Research"),
            ("Two CTA buttons compete visually. What design concept helps?", ["Visual hierarchy", "SQL normalization", "Thread safety", "Cache eviction"], 0, "Visual Design"),
            ("A prototype tests poorly with screen-reader users. What should improve?", ["Semantic labels, focus order, contrast, and accessibility patterns", "Only shadows", "More hidden icons", "No labels"], 0, "Accessibility"),
            ("A team needs reusable interface consistency. What should you create?", ["A design system with components, states, and usage guidelines", "A single screenshot", "Only backend API docs", "A spreadsheet"], 0, "Design Systems"),
        ],
        "hard": [
            ("Stakeholders want a flashy UI but research shows users need simplicity. What is the best response?", ["Use evidence from user goals, task success, and usability findings to guide tradeoffs", "Follow only personal taste", "Ignore research", "Remove testing"], 0, "UX Strategy"),
            ("A checkout redesign improves beauty but reduces completion. What should you do?", ["Analyze usability data, identify friction, and iterate toward conversion and clarity", "Keep it unchanged", "Remove analytics", "Only change colours"], 0, "Interaction Design"),
        ],
    },
    "Backend Developer": {
        "medium": [
            ("An API creates duplicate records when clients retry requests. What should you add?", ["Idempotency and transaction-safe writes", "More frontend icons", "No database constraints", "Manual cleanup only"], 0, "API Design"),
            ("A frequently requested endpoint is slow. What should you inspect?", ["Query plan, indexes, caching, pagination, and payload size", "Button shadows", "Figma variants", "Only image format"], 0, "Performance"),
            ("A service needs background email sending. What architecture fits?", ["Message queue or background worker", "Synchronous loop in the request only", "CSS animation", "LocalStorage only"], 0, "Concurrency"),
            ("A password reset system is being designed. What matters most?", ["Token expiry, secure hashing, single-use tokens, and audit logging", "Only UI colours", "Longer labels", "No server validation"], 0, "Authentication & Security"),
        ],
        "hard": [
            ("Design an API that handles traffic spikes without failing. What should be included?", ["Rate limiting, caching, queues, autoscaling, and graceful degradation", "One large controller", "No monitoring", "All data in memory"], 0, "Scalability"),
            ("A distributed transaction sometimes partially completes. What design concern is central?", ["Consistency, retries, idempotency, and compensating actions", "Typography", "CSS specificity", "Dashboard layout"], 0, "System Design"),
        ],
    },
}

DOMAIN_CODING_QUESTIONS = {
    "Data Scientist": {
        "medium": [
            {
                "text": "Write a Python function `clean_scores(scores)` that removes `None` values and returns the average score rounded to 2 decimals.",
                "starter_code": "def clean_scores(scores):\n    # scores example: [80, None, 90, 75]\n    pass",
                "expected_keywords": ["def", "none", "sum", "len", "round"],
                "sub_topic": "Python Data Cleaning",
            },
            {
                "text": "Write a Python snippet using pandas to group a DataFrame `df` by `department` and calculate the mean `salary`.",
                "starter_code": "import pandas as pd\n\n# df has columns: department, salary\nresult = None",
                "expected_keywords": ["groupby", "department", "salary", "mean"],
                "sub_topic": "Data Manipulation",
            },
        ],
        "hard": [
            {
                "text": "Write a function `precision_recall(tp, fp, fn)` that returns precision and recall rounded to 3 decimals. Handle division by zero safely.",
                "starter_code": "def precision_recall(tp, fp, fn):\n    pass",
                "expected_keywords": ["tp", "fp", "fn", "precision", "recall", "round", "if"],
                "sub_topic": "Model Evaluation",
            },
            {
                "text": "Write a pandas pipeline that fills missing numeric values with median values and one-hot encodes a `category` column.",
                "starter_code": "import pandas as pd\n\ndef prepare_features(df):\n    pass",
                "expected_keywords": ["median", "fillna", "get_dummies", "category", "select_dtypes"],
                "sub_topic": "Feature Engineering",
            },
            {
                "text": "Write pseudocode or Python for a train/validation split, model training, prediction, and F1-score evaluation flow.",
                "starter_code": "def train_and_evaluate(X, y, model):\n    pass",
                "expected_keywords": ["train_test_split", "fit", "predict", "f1", "score"],
                "sub_topic": "Machine Learning",
            },
        ],
    },
    "AI-ML Engineer": {
        "medium": [
            {
                "text": "Write a Python function `normalize(values)` that min-max normalizes a list of numbers. Handle equal min/max safely.",
                "starter_code": "def normalize(values):\n    pass",
                "expected_keywords": ["min", "max", "return", "for", "if"],
                "sub_topic": "Preprocessing",
            },
            {
                "text": "Write a small FastAPI prediction endpoint skeleton that accepts JSON input and returns a prediction.",
                "starter_code": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.post('/predict')\ndef predict(payload: dict):\n    pass",
                "expected_keywords": ["fastapi", "post", "predict", "return", "payload"],
                "sub_topic": "Model Deployment",
            },
        ],
        "hard": [
            {
                "text": "Write a PyTorch-style training loop pseudocode with forward pass, loss calculation, backward pass, and optimizer step.",
                "starter_code": "def train_one_epoch(model, loader, optimizer, loss_fn):\n    pass",
                "expected_keywords": ["zero_grad", "loss", "backward", "step", "model"],
                "sub_topic": "Deep Learning",
            },
            {
                "text": "Write code/pseudocode to load a saved model artifact, validate input features, and return an inference response.",
                "starter_code": "def run_inference(model_path, payload):\n    pass",
                "expected_keywords": ["load", "validate", "predict", "return", "model"],
                "sub_topic": "Model Deployment",
            },
            {
                "text": "Write pseudocode for an experiment tracker that records parameters, metrics, and model artifact path after training.",
                "starter_code": "def log_experiment(params, metrics, artifact_path):\n    pass",
                "expected_keywords": ["params", "metrics", "artifact", "log", "timestamp"],
                "sub_topic": "MLOps",
            },
        ],
    },
    "Data Analyst": {
        "medium": [
            {
                "text": "Write a SQL query to return total revenue by `region` from an `orders` table with columns `region`, `quantity`, and `price`.",
                "starter_code": "SELECT\n  -- your columns\nFROM orders\n-- your grouping",
                "expected_keywords": ["select", "sum", "quantity", "price", "group by", "region"],
                "sub_topic": "SQL",
            },
            {
                "text": "Write a pandas snippet to remove duplicate rows and fill missing `sales` values with the median.",
                "starter_code": "def clean_sales(df):\n    pass",
                "expected_keywords": ["drop_duplicates", "fillna", "median", "sales"],
                "sub_topic": "Data Cleaning",
            },
        ],
        "hard": [
            {
                "text": "Write a SQL query to find the top 3 products by monthly revenue using an `orders` table with `order_date`, `product`, and `revenue`.",
                "starter_code": "SELECT\n  -- month, product, revenue\nFROM orders\n-- rank/filter top 3",
                "expected_keywords": ["date", "product", "sum", "group by", "rank", "partition"],
                "sub_topic": "SQL",
            },
            {
                "text": "Write pandas code to calculate month-over-month percentage growth for a DataFrame with `month` and `revenue` columns.",
                "starter_code": "def add_mom_growth(df):\n    pass",
                "expected_keywords": ["sort", "pct_change", "revenue", "month"],
                "sub_topic": "Business Analysis",
            },
            {
                "text": "Write pseudocode for validating a dashboard KPI before sharing it with leadership.",
                "starter_code": "def validate_kpi(source_data, dashboard_value):\n    pass",
                "expected_keywords": ["source", "filter", "aggregate", "compare", "document"],
                "sub_topic": "Data Validation",
            },
        ],
    },
    "Full Stack Developer": {
        "medium": [
            {
                "text": "Write a React component that renders a list of skills and shows `No skills added` when the list is empty.",
                "starter_code": "function SkillList({ skills }) {\n  return null;\n}",
                "expected_keywords": ["map", "skills", "length", "return", "key"],
                "sub_topic": "Frontend",
            },
            {
                "text": "Write an Express-style route handler for `GET /users/:id` that returns a user or a 404 response.",
                "starter_code": "app.get('/users/:id', async (req, res) => {\n  // your code\n});",
                "expected_keywords": ["req.params", "find", "if", "404", "json"],
                "sub_topic": "Backend",
            },
        ],
        "hard": [
            {
                "text": "Write React code/pseudocode to submit a form, show loading state, handle API errors, and clear the form on success.",
                "starter_code": "function SignupForm() {\n  // state + submit handler\n}",
                "expected_keywords": ["useState", "fetch", "try", "catch", "loading", "error"],
                "sub_topic": "Frontend",
            },
            {
                "text": "Write a REST API handler that creates an order safely and prevents duplicate orders when the client retries.",
                "starter_code": "async function createOrder(req, res) {\n  // your code\n}",
                "expected_keywords": ["idempotency", "transaction", "order", "if", "return"],
                "sub_topic": "Backend",
            },
            {
                "text": "Write pseudocode for paginating a database-backed API endpoint with `page` and `limit` query parameters.",
                "starter_code": "async function listItems(req, res) {\n  // your code\n}",
                "expected_keywords": ["page", "limit", "offset", "find", "total"],
                "sub_topic": "APIs & Architecture",
            },
        ],
    },
    "Software Engineer": {
        "medium": [
            {
                "text": "Write a function `has_duplicate(nums)` that returns true if a list contains a duplicate.",
                "starter_code": "def has_duplicate(nums):\n    pass",
                "expected_keywords": ["set", "for", "return", "true"],
                "sub_topic": "Data Structures",
            },
            {
                "text": "Write a function `reverse_words(sentence)` that reverses word order but keeps each word unchanged.",
                "starter_code": "def reverse_words(sentence):\n    pass",
                "expected_keywords": ["split", "reverse", "join", "return"],
                "sub_topic": "Algorithms",
            },
        ],
        "hard": [
            {
                "text": "Write a function `is_valid_parentheses(s)` using a stack for brackets `()[]{}`.",
                "starter_code": "def is_valid_parentheses(s):\n    pass",
                "expected_keywords": ["stack", "append", "pop", "return", "map"],
                "sub_topic": "Data Structures",
            },
            {
                "text": "Write BFS pseudocode to return the shortest distance between two nodes in an unweighted graph.",
                "starter_code": "def shortest_path(graph, start, target):\n    pass",
                "expected_keywords": ["queue", "visited", "while", "distance", "return"],
                "sub_topic": "Algorithms",
            },
            {
                "text": "Write a simple LRU cache design using a dictionary and an order-tracking structure. Pseudocode is fine.",
                "starter_code": "class LRUCache:\n    def get(self, key):\n        pass\n    def put(self, key, value):\n        pass",
                "expected_keywords": ["dict", "capacity", "get", "put", "remove"],
                "sub_topic": "System Design",
            },
        ],
    },
    "DevOps Engineer": {
        "medium": [
            {
                "text": "Write a simple Dockerfile for a Node app that installs dependencies and starts `npm start`.",
                "starter_code": "FROM node:18\n# add steps here",
                "expected_keywords": ["from", "copy", "npm install", "expose", "cmd"],
                "sub_topic": "Containers",
            },
            {
                "text": "Write a GitHub Actions workflow skeleton that installs dependencies and runs tests on push.",
                "starter_code": "name: CI\non: [push]\njobs:\n  test:\n    steps:\n      # your steps",
                "expected_keywords": ["jobs", "checkout", "setup", "install", "test"],
                "sub_topic": "CI/CD",
            },
        ],
        "hard": [
            {
                "text": "Write a Kubernetes Deployment YAML skeleton for 3 replicas of an app container.",
                "starter_code": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app\nspec:\n  # your spec",
                "expected_keywords": ["replicas", "selector", "template", "containers", "image"],
                "sub_topic": "Orchestration",
            },
            {
                "text": "Write Terraform pseudocode/resource blocks to create a cloud VM/security group style resource.",
                "starter_code": "resource \"example\" \"app\" {\n  # your config\n}",
                "expected_keywords": ["resource", "variable", "provider", "tags", "output"],
                "sub_topic": "Infrastructure as Code",
            },
            {
                "text": "Write pseudocode for a deployment rollback strategy when error rate crosses a threshold.",
                "starter_code": "def rollback_if_unhealthy(metrics):\n    pass",
                "expected_keywords": ["error", "threshold", "rollback", "alert", "previous"],
                "sub_topic": "Monitoring",
            },
        ],
    },
    "Cybersecurity Analyst": {
        "medium": [
            {
                "text": "Write pseudocode to validate password strength with checks for length, digit, uppercase, and special character.",
                "starter_code": "def is_strong_password(password):\n    pass",
                "expected_keywords": ["len", "isdigit", "upper", "special", "return"],
                "sub_topic": "Authentication & Security",
            },
            {
                "text": "Write pseudocode to detect suspicious login attempts from a list of events by counting failures per IP.",
                "starter_code": "def suspicious_ips(events):\n    pass",
                "expected_keywords": ["ip", "failed", "count", "threshold", "return"],
                "sub_topic": "Threats & Attacks",
            },
        ],
        "hard": [
            {
                "text": "Write a small log-analysis function that flags users with failed logins followed by a successful login from the same IP.",
                "starter_code": "def flag_bruteforce_success(events):\n    pass",
                "expected_keywords": ["failed", "success", "ip", "user", "flag"],
                "sub_topic": "Incident Response",
            },
            {
                "text": "Write pseudocode for securely storing a password using salt and hashing.",
                "starter_code": "def store_password(password):\n    pass",
                "expected_keywords": ["salt", "hash", "pbkdf2", "bcrypt", "store"],
                "sub_topic": "Authentication & Security",
            },
            {
                "text": "Write pseudocode for checking whether a user has permission to access a resource.",
                "starter_code": "def can_access(user, resource, action):\n    pass",
                "expected_keywords": ["role", "permission", "resource", "action", "return"],
                "sub_topic": "Authorization",
            },
        ],
    },
    "UI/UX Designer": {
        "medium": [
            {
                "text": "Write semantic HTML for an accessible email input with a label and error message region.",
                "starter_code": "<form>\n  <!-- your accessible input -->\n</form>",
                "expected_keywords": ["label", "input", "email", "aria", "error"],
                "sub_topic": "Accessibility",
            },
            {
                "text": "Write CSS for a responsive two-column card layout that becomes one column on small screens.",
                "starter_code": ".cards {\n  /* your CSS */\n}",
                "expected_keywords": ["grid", "media", "columns", "gap", "1fr"],
                "sub_topic": "Visual Design",
            },
        ],
        "hard": [
            {
                "text": "Write HTML/CSS pseudocode for a keyboard-accessible modal with focusable close control and ARIA attributes.",
                "starter_code": "<div class=\"modal\">\n  <!-- your modal -->\n</div>",
                "expected_keywords": ["role", "dialog", "aria-modal", "button", "focus"],
                "sub_topic": "Accessibility",
            },
            {
                "text": "Write pseudocode for handling form validation states: idle, invalid, submitting, success, and error.",
                "starter_code": "function handleFormState(state) {\n  // your logic\n}",
                "expected_keywords": ["invalid", "submitting", "success", "error", "message"],
                "sub_topic": "Interaction Design",
            },
            {
                "text": "Write CSS variables for a small design system containing color, spacing, and radius tokens.",
                "starter_code": ":root {\n  /* tokens */\n}",
                "expected_keywords": ["--", "color", "spacing", "radius", "var"],
                "sub_topic": "Design Systems",
            },
        ],
    },
    "Backend Developer": {
        "medium": [
            {
                "text": "Write a FastAPI route for `GET /health` that returns `{status: 'ok'}`.",
                "starter_code": "from fastapi import FastAPI\napp = FastAPI()\n\n# your route here",
                "expected_keywords": ["@app.get", "health", "return", "status", "ok"],
                "sub_topic": "API Design",
            },
            {
                "text": "Write SQL to create a `users` table with id, email, password_hash, and created_at.",
                "starter_code": "CREATE TABLE users (\n  -- columns\n);",
                "expected_keywords": ["create table", "id", "email", "password_hash", "created_at"],
                "sub_topic": "Databases",
            },
        ],
        "hard": [
            {
                "text": "Write a FastAPI endpoint that creates a user only if the email is not already registered.",
                "starter_code": "@app.post('/users')\ndef create_user(payload: dict):\n    pass",
                "expected_keywords": ["email", "query", "if", "raise", "add"],
                "sub_topic": "API Design",
            },
            {
                "text": "Write pseudocode for caching an expensive database result with a TTL and fallback on cache miss.",
                "starter_code": "def get_with_cache(key):\n    pass",
                "expected_keywords": ["cache", "ttl", "miss", "database", "set"],
                "sub_topic": "Caching",
            },
            {
                "text": "Write pseudocode for a worker that consumes jobs from a queue, retries failures, and marks completion.",
                "starter_code": "def process_jobs(queue):\n    pass",
                "expected_keywords": ["queue", "try", "except", "retry", "complete"],
                "sub_topic": "Concurrency",
            },
        ],
    },
}

# ── ML model ──────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    raise RuntimeError("Model not found. Run: python generate_dataset.py && python model.py")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_expanded_question_bank(domain: str) -> list[dict]:
    base_questions = QUESTION_BANK.get(domain, [])
    expanded = [
        {
            **q,
            "difficulty": q.get("difficulty", "easy"),
            "question_type": q.get("question_type", "mcq"),
        }
        for q in base_questions
    ]

    scenarios = DOMAIN_SCENARIOS.get(domain, {})
    prefix = "".join(part[0].lower() for part in domain.replace("/", " ").replace("-", " ").split())
    for difficulty, entries in scenarios.items():
        for idx, (text, options, correct_index, sub_topic) in enumerate(entries, start=1):
            expanded.append({
                "id": f"{prefix}_{difficulty}_{idx:02d}",
                "text": text,
                "options": options,
                "correct_index": correct_index,
                "sub_topic": sub_topic,
                "difficulty": difficulty,
                "question_type": "scenario" if difficulty == "medium" else "case-study",
            })

    coding_questions = DOMAIN_CODING_QUESTIONS.get(domain, {})
    for difficulty, entries in coding_questions.items():
        for idx, item in enumerate(entries, start=1):
            expanded.append({
                "id": f"{prefix}_{difficulty}_code_{idx:02d}",
                "text": item["text"],
                "options": [],
                "correct_index": None,
                "sub_topic": item["sub_topic"],
                "difficulty": difficulty,
                "question_type": "coding",
                "starter_code": item.get("starter_code", ""),
                "expected_keywords": item.get("expected_keywords", []),
                "language": item.get("language", "text"),
            })

    return expanded


def _safe_question(q: dict) -> dict:
    return {
        "id":            q["id"],
        "text":          q["text"],
        "question":      q["text"],        # alias for legacy frontend
        "options":       q["options"],
        "sub_topic":     q["sub_topic"],
        "topic_tag":     q["sub_topic"],   # alias so both field names work
        "difficulty":    q.get("difficulty", "easy"),
        "question_type": q.get("question_type", "mcq"),
        "starter_code":  q.get("starter_code", ""),
        "language":      q.get("language", "text"),
    }


def _sample_questions(domain: str, level: str = "mixed", user_id: str | None = None) -> list[dict]:
    """
    Return randomly sampled questions, safe for the frontend.
    Exposes question metadata but never exposes correct_index.
    Never exposes correct_index.
    """
    pool = _build_expanded_question_bank(domain)
    if not pool:
        return []

    level = level if level in LEVEL_COUNTS else "mixed"
    requested_counts = LEVEL_COUNTS[level]
    seed = f"{domain}:{level}:{user_id or 'guest'}:{random.random()}"
    rng = random.Random(seed)
    by_level: dict[str, list[dict]] = defaultdict(list)
    for question in pool:
        by_level[question.get("difficulty", "easy")].append(question)

    sampled: list[dict] = []
    used_ids: set[str] = set()
    coding_targets = LEVEL_CODING_COUNTS.get(level, {})
    for difficulty, coding_count in coding_targets.items():
        if coding_count <= 0:
            continue
        candidates = [
            q for q in by_level.get(difficulty, [])
            if q.get("question_type") == "coding"
        ]
        rng.shuffle(candidates)
        chosen = candidates[:coding_count]
        sampled.extend(chosen)
        used_ids.update(q["id"] for q in chosen)

    for difficulty, count in requested_counts.items():
        existing_for_level = len([q for q in sampled if q.get("difficulty") == difficulty])
        remaining_count = max(0, count - existing_for_level)
        candidates = [
            q for q in by_level.get(difficulty, [])
            if q["id"] not in used_ids
            and not (
                difficulty in coding_targets
                and q.get("question_type") == "coding"
            )
        ]
        rng.shuffle(candidates)
        chosen = candidates[:remaining_count]
        sampled.extend(chosen)
        used_ids.update(q["id"] for q in chosen)

    target_total = sum(requested_counts.values())
    if len(sampled) < target_total:
        fallback = [q for q in pool if q["id"] not in used_ids]
        rng.shuffle(fallback)
        sampled.extend(fallback[:target_total - len(sampled)])

    rng.shuffle(sampled)
    return [_safe_question(q) for q in sampled]


def _parse_answers(raw_answers: list) -> dict[str, int | str]:
    """
    Normalise the answers payload into {question_id: chosen_index (int)}.

    Accepts:
      1. [{"id": "ds_01", "answer": 2}]   ← index-based (preferred)
      2. {"ds_01": 2, ...}                ← dict form
    """
    result: dict[str, int | str] = {}

    if isinstance(raw_answers, dict):
        parsed = {}
        for key, value in raw_answers.items():
            try:
                parsed[str(key)] = int(value)
            except (ValueError, TypeError):
                parsed[str(key)] = str(value)
        return parsed

    for item in raw_answers:
        if isinstance(item, dict):
            qid = str(item.get("id", item.get("question_id", "")))
            val = item.get("answer", item.get("selected", None))
            if qid and val is not None:
                try:
                    result[qid] = int(val)
                except (ValueError, TypeError):
                    result[qid] = str(val)

    return result


def _score_coding_answer(question: dict, answer: int | str) -> bool:
    answer_text = str(answer or "").strip().lower()
    if len(answer_text) < 20:
        return False

    expected_keywords = [keyword.lower() for keyword in question.get("expected_keywords", [])]
    if not expected_keywords:
        return bool(answer_text)

    matches = sum(1 for keyword in expected_keywords if keyword in answer_text)
    required_matches = max(2, min(4, len(expected_keywords) // 2 + 1))
    return matches >= required_matches


def _score_answers(
    served_questions: list[dict],
    user_answer_map: dict[str, int | str],
) -> tuple[int, float, list[str]]:
    """
    Returns (correct_count, quiz_score_pct, weak_area_subtopics).
    Scores by comparing chosen index against correct_index.
    weak_area_subtopics = sub_topic strings for every incorrect answer.
    """
    correct = 0
    weak_subtopics: list[str] = []

    for q in served_questions:
        chosen_answer = user_answer_map.get(q["id"], -1)
        if q.get("question_type") == "coding":
            is_correct = _score_coding_answer(q, chosen_answer)
        else:
            is_correct = chosen_answer == q["correct_index"]

        if is_correct:
            correct += 1
        else:
            weak_subtopics.append(q["sub_topic"])

    total      = len(served_questions)
    quiz_score = round((correct / total) * 100, 1) if total else 0.0
    return correct, quiz_score, weak_subtopics


def _detect_weak_topics(
    served_questions: list[dict],
    user_answer_map: dict[str, int | str],
    threshold: float = 0.4,
) -> list[dict]:
    """
    Group wrong answers by sub_topic.
    Flag any sub-topic where wrong_rate > threshold.
    """
    stats: dict[str, dict] = defaultdict(lambda: {"wrong": 0, "total": 0})

    for q in served_questions:
        tag = q["sub_topic"]
        stats[tag]["total"] += 1
        chosen_answer = user_answer_map.get(q["id"], -1)
        if q.get("question_type") == "coding":
            is_correct = _score_coding_answer(q, chosen_answer)
        else:
            is_correct = chosen_answer == q["correct_index"]

        if not is_correct:
            stats[tag]["wrong"] += 1

    weak = [
        {"sub_topic": tag, "wrong": s["wrong"], "total": s["total"]}
        for tag, s in stats.items()
        if s["total"] > 0 and (s["wrong"] / s["total"]) > threshold
    ]
    weak.sort(key=lambda x: x["wrong"] / x["total"], reverse=True)
    return weak


def _build_company_questions(company: str, role: str = "General") -> list[dict]:
    rows = COMPANY_PRACTICE_BANK.get(company, [])
    safe_company = company.lower().replace(" ", "_")
    questions = []
    for idx, (difficulty, topic, text, options, correct_index) in enumerate(rows, start=1):
        questions.append({
            "id": f"{safe_company}_{idx:02d}",
            "company": company,
            "role": role,
            "difficulty": difficulty,
            "topic_tag": topic,
            "sub_topic": topic,
            "text": text,
            "question": text,
            "options": options,
            "correct_index": correct_index,
            "question_type": "company-practice",
        })
    return questions


def _sample_company_questions(company: str, role: str = "General", level: str = "mixed", user_id: str | None = None) -> list[dict]:
    pool = _build_company_questions(company, role)
    if not pool:
        return []

    level = level if level in LEVEL_COUNTS else "mixed"
    requested = LEVEL_COUNTS[level]
    target_total = min(sum(requested.values()), len(pool))
    rng = random.Random(f"{company}:{role}:{level}:{user_id or 'guest'}:{random.random()}")

    by_level: dict[str, list[dict]] = defaultdict(list)
    for question in pool:
        by_level[question["difficulty"]].append(question)

    sampled: list[dict] = []
    used_ids: set[str] = set()
    for difficulty, count in requested.items():
        candidates = by_level.get(difficulty, [])
        rng.shuffle(candidates)
        chosen = candidates[:count]
        sampled.extend(chosen)
        used_ids.update(q["id"] for q in chosen)

    if len(sampled) < target_total:
        fallback = [q for q in pool if q["id"] not in used_ids]
        rng.shuffle(fallback)
        sampled.extend(fallback[:target_total - len(sampled)])

    rng.shuffle(sampled)
    return [
        {
            "id": q["id"],
            "company": q["company"],
            "role": q["role"],
            "difficulty": q["difficulty"],
            "topic_tag": q["topic_tag"],
            "text": q["text"],
            "question": q["question"],
            "options": q["options"],
            "question_type": q["question_type"],
        }
        for q in sampled
    ]


def _score_company_practice(company: str, role: str, answers: list) -> tuple[int, int, float, dict]:
    full_questions = _build_company_questions(company, role)
    answer_map = _parse_answers(answers)
    served_ids = set(answer_map.keys())
    served_questions = [q for q in full_questions if q["id"] in served_ids]

    correct = 0
    breakdown: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for question in served_questions:
        difficulty = question["difficulty"]
        breakdown[difficulty]["total"] += 1
        is_correct = answer_map.get(question["id"], -1) == question["correct_index"]
        if is_correct:
            correct += 1
            breakdown[difficulty]["correct"] += 1

    total = len(served_questions)
    score = round((correct / total) * 100, 1) if total else 0.0
    return correct, total, score, dict(breakdown)


def _summarise_company_performance(attempts: list[CompanyPracticeResult]) -> list[dict]:
    grouped: dict[tuple[str, str], list[CompanyPracticeResult]] = defaultdict(list)
    for attempt in attempts:
        grouped[(attempt.company, attempt.level)].append(attempt)

    summary = []
    for (company, level), items in grouped.items():
        latest = max(items, key=lambda item: item.created_at)
        scores = [item.score for item in items]
        summary.append({
            "company": company,
            "level": level,
            "attempts": len(items),
            "best_score": round(max(scores), 1),
            "average_score": round(sum(scores) / len(scores), 1),
            "latest_score": round(latest.score, 1),
            "latest_attempt_at": latest.created_at.isoformat(),
        })

    summary.sort(key=lambda item: item["latest_attempt_at"], reverse=True)
    return summary


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Career Intelligence API v3.1 is running", "domains": list(QUESTION_BANK.keys())}


@app.get("/company-practice/companies")
def get_company_practice_companies():
    return {
        "companies": [
            {"name": company, "question_count": len(questions)}
            for company, questions in COMPANY_PRACTICE_BANK.items()
        ],
        "levels": list(LEVEL_COUNTS.keys()),
    }


@app.post("/auth/signup", response_model=AuthResponse)
def signup(data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        public_id=str(uuid4()),
        name=data.name.strip(),
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Account created successfully.",
        "user": {
            "user_id": user.public_id,
            "name": user.name,
            "email": user.email,
        },
    }


@app.post("/auth/login", response_model=AuthResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "message": f"Welcome back, {user.name}.",
        "user": {
            "user_id": user.public_id,
            "name": user.name,
            "email": user.email,
        },
    }


@app.get("/company-practice/{company:path}")
def get_company_practice_questions(
    company: str,
    role: str = "General",
    level: str = Query("mixed", pattern="^(easy|medium|hard|mixed)$"),
    user_id: str | None = None,
):
    company = company.strip()
    questions = _sample_company_questions(company, role=role, level=level, user_id=user_id)
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No company practice questions found for '{company}'. Available: {list(COMPANY_PRACTICE_BANK.keys())}",
        )

    level_mix = defaultdict(int)
    for question in questions:
        level_mix[question["difficulty"]] += 1

    return {
        "company": company,
        "role": role,
        "level": level,
        "questions": questions,
        "total": len(questions),
        "level_mix": dict(sorted(level_mix.items())),
    }


@app.post("/company-practice/evaluate", response_model=CompanyPracticeEvaluateResponse)
def evaluate_company_practice(data: CompanyPracticeSubmission, db: Session = Depends(get_db)):
    company = data.company.strip()
    if company not in COMPANY_PRACTICE_BANK:
        raise HTTPException(status_code=404, detail=f"Company '{company}' not found.")

    correct, total, score, breakdown = _score_company_practice(company, data.role, data.answers)
    if total == 0:
        raise HTTPException(status_code=422, detail="No valid company practice answers received.")

    if score >= 80:
        feedback = "Strong company-practice performance. Keep building speed and consistency."
    elif score >= 55:
        feedback = "Good progress. Review the lower-scoring difficulty areas before the next attempt."
    else:
        feedback = "Focus on fundamentals first, then retake with a smaller difficulty level."

    db.add(CompanyPracticeResult(
        user_id=data.user_id,
        company=company,
        role=data.role,
        level=data.level,
        score=score,
        correct_count=correct,
        total_questions=total,
        difficulty_breakdown=json.dumps(breakdown),
    ))
    db.commit()

    return {
        "company": company,
        "role": data.role,
        "level": data.level,
        "score": int(score),
        "correct_count": correct,
        "total_questions": total,
        "feedback": feedback,
        "difficulty_breakdown": breakdown,
    }


@app.get("/users/{user_id}/dashboard", response_model=JourneyDashboardResponse)
def get_user_dashboard(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.public_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .order_by(UserSession.created_at.desc())
        .all()
    )
    tests = (
        db.query(TestResult)
        .filter(TestResult.user_id == user_id)
        .order_by(TestResult.created_at.desc())
        .all()
    )
    company_attempts = (
        db.query(CompanyPracticeResult)
        .filter(CompanyPracticeResult.user_id == user_id)
        .order_by(CompanyPracticeResult.created_at.desc())
        .all()
    )

    latest_session = sessions[0] if sessions else None
    latest_test = tests[0] if tests else None
    latest_skills = latest_session.skills_input.split(",") if latest_session and latest_session.skills_input else []
    latest_domain = latest_session.top_domain if latest_session else (latest_test.domain if latest_test else None)
    average_readiness = round(
        sum(item.readiness_score for item in tests) / len(tests),
        1,
    ) if tests else 0.0
    latest_readiness = round(latest_test.readiness_score, 1) if latest_test else 0.0

    roadmap = None
    if latest_domain:
        roadmap = build_learning_roadmap(
            user_skills=latest_skills,
            domain=latest_domain,
            recent_readiness=latest_readiness if tests else None,
        )

    return {
        "user": {
            "user_id": user.public_id,
            "name": user.name,
            "email": user.email,
        },
        "overview": {
            "analyses_count": len(sessions),
            "assessments_count": len(tests),
            "latest_top_domain": latest_domain,
            "average_readiness": average_readiness,
            "latest_readiness": latest_readiness,
        },
        "recommendation_history": [
            {
                "id": item.id,
                "skills_input": [skill for skill in item.skills_input.split(",") if skill],
                "top_domain": item.top_domain,
                "confidence": round(item.confidence, 2),
                "created_at": item.created_at.isoformat(),
            }
            for item in sessions
        ],
        "assessment_history": [
            {
                "id": item.id,
                "domain": item.domain,
                "assessment_score": round(item.assessment_score, 1),
                "skill_match": round(item.skill_match, 1),
                "readiness_score": round(item.readiness_score, 1),
                "created_at": item.created_at.isoformat(),
            }
            for item in tests
        ],
        "company_performance": _summarise_company_performance(company_attempts),
        "roadmap": roadmap,
    }


@app.delete("/users/{user_id}/history/recommendations")
def clear_recommendation_history(user_id: str, db: Session = Depends(get_db)):
    """Delete all saved skill-analysis sessions (recommendation history) for this user."""
    user = db.query(User).filter(User.public_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.query(UserSession).filter(UserSession.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return {"ok": True}


@app.delete("/users/{user_id}/history/assessments")
def clear_assessment_history(user_id: str, db: Session = Depends(get_db)):
    """Delete all saved domain assessment results for this user."""
    user = db.query(User).filter(User.public_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.query(TestResult).filter(TestResult.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return {"ok": True}


# ── GitHub Projects ───────────────────────────────────────────────────────────

@app.post("/github-projects", response_model=GitHubProjectResponse)
def add_github_project(data: GitHubProjectCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.public_id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    project = GitHubProject(
        user_id=data.user_id,
        repo_name=data.repo_name,
        repo_url=data.repo_url,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "user_id": project.user_id,
        "repo_name": project.repo_name,
        "repo_url": project.repo_url,
        "created_at": project.created_at.isoformat(),
    }

@app.get("/github-projects/{user_id}", response_model=list[GitHubProjectResponse])
def get_github_projects(user_id: str, db: Session = Depends(get_db)):
    projects = db.query(GitHubProject).filter(GitHubProject.user_id == user_id).order_by(GitHubProject.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "repo_name": p.repo_name,
            "repo_url": p.repo_url,
            "created_at": p.created_at.isoformat(),
        } for p in projects
    ]

@app.delete("/github-projects/{project_id}")
def delete_github_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(GitHubProject).filter(GitHubProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    db.delete(project)
    db.commit()
    return {"ok": True}


# ── GET /questions/{domain}  (new canonical path) ─────────────────────────────
@app.get("/questions/{domain:path}")
def get_questions_v2(
    domain: str,
    level: str = Query("mixed", pattern="^(easy|medium|hard|mixed)$"),
    user_id: str | None = None,
):
    """
    Returns 10 randomly sampled questions for the domain.
    Fields: id, text, question, options (4 items), sub_topic, topic_tag.
    Uses {domain:path} to allow slashes in domain names like 'UI/UX Designer'.
    correct_index is intentionally excluded.
    """
    domain = domain.strip()
    questions = _sample_questions(domain, level=level, user_id=user_id)
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for '{domain}'. Available: {list(QUESTION_BANK.keys())}",
        )
    level_mix = defaultdict(int)
    for question in questions:
        level_mix[question["difficulty"]] += 1

    return {
        "domain": domain,
        "level": level,
        "questions": questions,
        "total": len(questions),
        "level_mix": dict(sorted(level_mix.items())),
    }


# ── GET /get-questions/{domain}  (legacy path — kept for backward compat) ─────
@app.get("/get-questions/{domain:path}")
def get_questions_legacy(
    domain: str,
    level: str = Query("mixed", pattern="^(easy|medium|hard|mixed)$"),
    user_id: str | None = None,
):
    return get_questions_v2(domain, level, user_id)


# ── POST /evaluate  (new canonical path) ──────────────────────────────────────
@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(data: TestSubmission, db: Session = Depends(get_db)):
    """
    Score a completed quiz.

    Request body:
      {
        "domain": "Data Scientist",
        "answers": [{"id": "ds_01", "answer": "df.dropna()"}, ...],
        "skills": ["python", "sql"]   // optional — used for readiness formula
      }

    Scoring:
      quiz_score    = correct / total × 100
      readiness     = 0.6 × skill_match + 0.4 × quiz_score
      weak_topics   = sub-topics where wrong_rate > 40%
    """
    domain = data.domain.strip()
    full_questions = _build_expanded_question_bank(domain)

    if not full_questions:
        raise HTTPException(
            status_code=404,
            detail=f"Domain '{domain}' not found. Available: {list(QUESTION_BANK.keys())}",
        )

    # Parse answers into {id: chosen_option}
    user_answer_map = _parse_answers(data.answers)

    if not user_answer_map:
        raise HTTPException(
            status_code=422,
            detail=(
                "No valid answers received. "
                "Send answers as [{\"id\": \"<question_id>\", \"answer\": <chosen_index>}]."
            ),
        )

    # Resolve which questions were actually served to this user
    served_ids       = set(user_answer_map.keys())
    served_questions = [q for q in full_questions if q["id"] in served_ids]

    if not served_questions:
        raise HTTPException(
            status_code=422,
            detail=(
                f"None of the submitted question IDs match domain '{domain}'. "
                f"Expected IDs like: {[q['id'] for q in full_questions[:3]]}..."
            ),
        )

    # ── Score ─────────────────────────────────────────────────────────────────
    correct, quiz_score, weak_area_subtopics = _score_answers(served_questions, user_answer_map)

    # ── Weak topic detection ──────────────────────────────────────────────────
    weak_sub_topics = _detect_weak_topics(served_questions, user_answer_map)

    # ── Readiness formula: Overall = (0.6 × Skill Match) + (0.4 × Quiz Score) ─
    user_skills  = normalize_skills(data.skills or [])
    gap          = compute_skill_gap(user_skills, domain)
    skill_match  = gap["match_percentage"]
    readiness    = compute_readiness_score(skill_match, quiz_score)
    readiness["domain"] = domain

    # ── Feedback ──────────────────────────────────────────────────────────────
    if quiz_score >= 80:
        feedback = "Excellent — your quiz performance is strong."
    elif quiz_score >= 60:
        feedback = "Good progress. Review the flagged sub-topics to level up."
    elif quiz_score >= 40:
        feedback = "Keep going — focus on the weak areas identified below."
    else:
        feedback = "Start with the fundamentals. Use the resources below to build a solid base."

    # ── Resources ─────────────────────────────────────────────────────────────
    resources = get_resources_for_skills(gap["missing_skills"][:5])

    # ── Persist ───────────────────────────────────────────────────────────────
    db.add(TestResult(
        user_id=data.user_id,
        domain=domain,
        assessment_score=quiz_score,
        skill_match=skill_match,
        readiness_score=readiness["readiness_score"],
    ))
    db.commit()

    return {
        "quiz_score":      int(quiz_score),
        "correct_count":   correct,
        "total_questions":  len(served_questions),
        "score":           int(quiz_score),   # backward compat
        "feedback":        feedback,
        "weak_sub_topics": weak_sub_topics,
        "weak_areas":      list(dict.fromkeys(weak_area_subtopics)),  # unique sub_topics of wrong answers
        "readiness":       readiness,
        "resources":       resources,
    }


# ── POST /evaluate-test  (legacy path) ────────────────────────────────────────
@app.post("/evaluate-test", response_model=EvaluateResponse)
def evaluate_test_legacy(data: TestSubmission, db: Session = Depends(get_db)):
    return evaluate(data, db)


# ── POST /recommend-career ────────────────────────────────────────────────────
@app.post("/recommend-career", response_model=RecommendResponse)
def recommend(data: SkillsInput, db: Session = Depends(get_db)):
    raw_skills = list(data.skills or [])
    user_skills = normalize_skills(data.skills)
    try:
        input_vector = skills_to_feature_vector(data.skills)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if len(input_vector) != len(SKILLS_LIST):
        raise HTTPException(status_code=500, detail="Feature vector length mismatch with model features.")

    logger.info("Career ML raw input: %s", raw_skills)
    logger.info("Career ML normalized skills: %s", user_skills)
    logger.info("Career ML feature sum=%s vector=%s", sum(input_vector), input_vector)

    if not any(input_vector):
        raise HTTPException(
            status_code=400,
            detail="No recognised skills. Try: python, sql, ml, react, docker, cpp, ruby.",
        )

    probs      = model.predict_proba([input_vector])[0]
    classes    = model.classes_
    top_idx    = probs.argsort()[-3:][::-1]

    logger.info("Career ML top prediction: %s (p=%.4f)", classes[top_idx[0]], float(probs[top_idx[0]]))

    recommendations, skill_gap_list, all_missing = [], [], []

    for i in top_idx:
        domain  = classes[i]
        matched = list(set(user_skills) & set(DOMAIN_SKILLS[domain]))
        xai     = get_xai_explanation(model, SKILLS_LIST, input_vector)
        reasoning = build_fit_reasoning(user_skills, domain, round(float(probs[i]) * 100, 2))

        prob_pct = int(round(float(probs[i]) * 100, 0))
        if prob_pct > 70:
            demand_level = "High"
        elif prob_pct >= 40:
            demand_level = "Medium"
        else:
            demand_level = "Low"

        recommendations.append({
            "role":       domain,
            "confidence": round(float(probs[i]) * 100, 2),
            "salary":     DOMAIN_DATA[domain]["salary"],
            "demand": {
                "level": demand_level,
                "percentage": prob_pct
            },
            "reason":     [f"You know {s.upper()}" for s in matched] or ["Explore this domain"],
            "top_skills": xai,
            "fit_summary": reasoning["fit_summary"],
            "growth_summary": reasoning["growth_summary"],
            "missing_priority_skills": reasoning["missing_priority_skills"],
            "project_suggestions": reasoning["project_suggestions"],
        })

        gap = compute_skill_gap(user_skills, domain)
        skill_gap_list.append(gap)
        all_missing.extend(gap["missing_skills"])

    resources = get_resources_for_skills(list(dict.fromkeys(all_missing))[:8])

    db.add(UserSession(
        user_id=data.user_id,
        skills_input=",".join(user_skills),
        top_domain=recommendations[0]["role"],
        confidence=recommendations[0]["confidence"],
    ))
    db.commit()

    return {"recommendations": recommendations, "skill_gap": skill_gap_list, "resources": resources}
