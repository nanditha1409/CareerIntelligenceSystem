import hashlib
import hmac
import secrets

# ── Canonical skill list (must match dataset columns, in this exact order) ───
SKILLS_LIST = [
    "python", "sql", "ml", "html", "css", "js",
    "docker", "linux", "figma", "react", "node",
    "java", "c", "cpp", "dsa", "aws", "excel", "powerbi",
    "tensorflow", "networking", "security",
    "git", "typescript", "mongodb", "redis",
    "kubernetes", "graphql", "rust", "go",
    "spark", "tableau", "pytorch",
    "fastapi", "django", "ruby",
]

# ── ML / UI skill map: synonyms → canonical token (lowercase keys) ────────────
SKILL_MAP = {
    "ml": "ml",
    "machine learning": "ml",
    "ai": "ml",
    "artificial intelligence": "ml",
    "c": "c",
    "c++": "cpp",
    "cpp": "cpp",
    "ruby": "ruby",
}

# ── Additional alias normalisation (legacy + common variants) ────────────────
SKILL_ALIASES = {
    **SKILL_MAP,
    "mysql": "sql", "postgres": "sql", "postgresql": "sql", "sqlite": "sql",
    "javascript": "js", "nodejs": "node", "reactjs": "react", "next.js": "react",
    "nextjs": "react", "vuejs": "js", "angular": "js",
    "machinelearning": "ml", "deep learning": "ml",
    "aws cloud": "aws", "amazon web services": "aws",
    "linux os": "linux", "ubuntu": "linux", "debian": "linux",
    "excel sheets": "excel", "google sheets": "excel",
    "power bi": "powerbi", "powerbi desktop": "powerbi",
    "cyber security": "security", "cybersecurity": "security", "infosec": "security",
    "k8s": "kubernetes", "kube": "kubernetes",
    "ts": "typescript",
    "mongo": "mongodb",
    "gql": "graphql",
    "tf": "tensorflow",
    "pt": "pytorch",
    "pyspark": "spark",
    "tableau desktop": "tableau",
}


def _canonical_skill(raw: str) -> str:
    """Lowercase, trim, collapse spaces, apply SKILL_ALIASES for a single token."""
    s = raw.strip().lower().replace("-", " ")
    s = " ".join(s.split())
    if not s:
        return ""
    return SKILL_ALIASES.get(s, s)

# ── Domain master skill sets ──────────────────────────────────────────────────
DOMAIN_SKILLS = {
    "Data Scientist":        ["python", "ml", "sql", "tensorflow", "pytorch", "spark", "git", "tableau", "excel"],
    "AI-ML Engineer":        ["python", "ml", "tensorflow", "pytorch", "fastapi", "docker", "git", "aws", "kubernetes"],
    "Data Analyst":          ["sql", "excel", "powerbi", "tableau", "python", "git", "spark"],
    "Full Stack Developer":  ["html", "css", "js", "react", "node", "typescript", "mongodb", "graphql", "git", "docker"],
    "Software Engineer":     ["python", "java", "c", "cpp", "dsa", "git", "html", "css", "js", "rust", "go", "ruby"],
    "DevOps Engineer":       ["docker", "linux", "aws", "kubernetes", "git", "python", "redis", "go"],
    "Cybersecurity Analyst": ["networking", "security", "linux", "python", "git"],
    "UI/UX Designer":        ["figma", "html", "css", "js", "react", "typescript"],
    "Backend Developer":     ["python", "node", "sql", "fastapi", "django", "docker", "redis", "mongodb", "git", "ruby"],
}

# ── Domain metadata ───────────────────────────────────────────────────────────
DOMAIN_DATA = {
    "Data Scientist":        {"salary": "₹6–15 LPA",  "demand": "High"},
    "AI-ML Engineer":        {"salary": "₹10–18 LPA", "demand": "Very High"},
    "Data Analyst":          {"salary": "₹4–10 LPA",  "demand": "High"},
    "Full Stack Developer":  {"salary": "₹5–14 LPA",  "demand": "Very High"},
    "Software Engineer":     {"salary": "₹5–12 LPA",  "demand": "High"},
    "DevOps Engineer":       {"salary": "₹6–15 LPA",  "demand": "High"},
    "Cybersecurity Analyst": {"salary": "₹7–12 LPA",  "demand": "High"},
    "UI/UX Designer":        {"salary": "₹4–10 LPA",  "demand": "Medium"},
    "Backend Developer":     {"salary": "₹5–13 LPA",  "demand": "High"},
}

DOMAIN_PROJECT_TEMPLATES = {
    "Data Scientist": [
        "Build a predictive analytics notebook using {skills} and publish the insights with clear business takeaways.",
        "Create an end-to-end churn or sales forecasting project that highlights data cleaning, feature engineering, and model evaluation.",
        "Design an interactive dashboard that explains a machine learning model's outputs to non-technical stakeholders.",
    ],
    "AI-ML Engineer": [
        "Ship a model-serving API using {skills} with one trained model, one inference endpoint, and deployment-ready documentation.",
        "Build a deep learning mini-project that fine-tunes a pretrained model and exposes predictions in a simple app.",
        "Create an MLOps-flavored project with training, evaluation, and deployment steps that show production thinking.",
    ],
    "Data Analyst": [
        "Create a KPI dashboard project using {skills} to track business trends and explain decisions from the data.",
        "Build a sales or operations analysis case study with SQL queries, data cleaning, and executive-style recommendations.",
        "Publish a portfolio report that turns raw tabular data into charts, trends, and clear business insights.",
    ],
    "Full Stack Developer": [
        "Build a full-stack product using {skills} with authentication, CRUD flows, and a polished frontend experience.",
        "Create a portfolio-grade app with a React frontend, backend APIs, and one real user workflow from start to finish.",
        "Ship a collaborative web app that demonstrates clean UI state, API integration, and deployment readiness.",
    ],
    "Software Engineer": [
        "Build a problem-solving project in {skills} that shows data structures, clean architecture, and testing discipline.",
        "Create a command-line or backend tool that solves a real workflow and documents its complexity and design tradeoffs.",
        "Publish a small system design style project with modular code, tests, and a thoughtful README.",
    ],
    "DevOps Engineer": [
        "Build a deployment pipeline using {skills} that automates build, test, and release for a sample application.",
        "Create an infrastructure project that provisions services, containers, and monitoring with reproducible steps.",
        "Ship an operations dashboard or automation toolkit that demonstrates reliability and observability thinking.",
    ],
    "Cybersecurity Analyst": [
        "Build a security review project using {skills} that audits a sample app or infrastructure setup and documents findings.",
        "Create a threat detection or log analysis workflow that flags suspicious behavior from sample events.",
        "Publish a portfolio case study on hardening, monitoring, and incident response for a realistic scenario.",
    ],
    "UI/UX Designer": [
        "Design and prototype a product workflow using {skills} with wireframes, polished UI, and usability rationale.",
        "Create a case study that shows user flows, high-fidelity screens, and accessibility-minded design decisions.",
        "Build a mini design system project that demonstrates components, interaction states, and visual consistency.",
    ],
    "Backend Developer": [
        "Build a backend service using {skills} with authentication, caching, and clearly documented REST endpoints.",
        "Create a production-style API project that includes database design, background jobs, and performance considerations.",
        "Ship a scalable service demo with rate limiting, persistence, and deployment-ready architecture notes.",
    ],
}

# ── Learning resources mapped to skills ──────────────────────────────────────
SKILL_RESOURCES = {
    "python":      [{"title": "Python for Everybody – Coursera",        "url": "https://www.coursera.org/specializations/python",                    "type": "course"},
                    {"title": "Official Python Tutorial",                "url": "https://docs.python.org/3/tutorial/",                                "type": "article"}],
    "sql":         [{"title": "SQL for Data Science – Coursera",        "url": "https://www.coursera.org/learn/sql-for-data-science",                "type": "course"},
                    {"title": "SQLZoo Interactive Tutorial",             "url": "https://sqlzoo.net/",                                               "type": "article"}],
    "ml":          [{"title": "Machine Learning Specialization – Andrew Ng", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "type": "course"},
                    {"title": "Scikit-learn User Guide",                 "url": "https://scikit-learn.org/stable/user_guide.html",                   "type": "article"}],
    "tensorflow":  [{"title": "TensorFlow Developer Certificate",       "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "type": "course"},
                    {"title": "TensorFlow Official Tutorials",           "url": "https://www.tensorflow.org/tutorials",                              "type": "article"}],
    "pytorch":     [{"title": "Deep Learning with PyTorch – fast.ai",   "url": "https://course.fast.ai/",                                           "type": "course"},
                    {"title": "PyTorch Official Tutorials",              "url": "https://pytorch.org/tutorials/",                                    "type": "article"}],
    "docker":      [{"title": "Docker for Beginners – YouTube",         "url": "https://www.youtube.com/watch?v=fqMOX6JJhGo",                       "type": "video"},
                    {"title": "Docker Official Get Started",             "url": "https://docs.docker.com/get-started/",                              "type": "article"}],
    "kubernetes":  [{"title": "Kubernetes Basics – Official",           "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/",            "type": "article"},
                    {"title": "CKA Prep – TechWorld with Nana",         "url": "https://www.youtube.com/watch?v=X48VuDVv0do",                       "type": "video"}],
    "aws":         [{"title": "AWS Cloud Practitioner – Udemy",         "url": "https://www.udemy.com/course/aws-certified-cloud-practitioner-new/", "type": "course"},
                    {"title": "AWS Free Tier Hands-on",                  "url": "https://aws.amazon.com/free/",                                      "type": "article"}],
    "react":       [{"title": "React Official Docs",                    "url": "https://react.dev/learn",                                           "type": "article"},
                    {"title": "Full React Course – freeCodeCamp",       "url": "https://www.youtube.com/watch?v=bMknfKXIFA8",                       "type": "video"}],
    "node":        [{"title": "Node.js Official Docs",                  "url": "https://nodejs.org/en/docs/",                                       "type": "article"},
                    {"title": "Node.js Crash Course – Traversy Media",  "url": "https://www.youtube.com/watch?v=fBNz5xF-Kx4",                      "type": "video"}],
    "typescript":  [{"title": "TypeScript Handbook",                    "url": "https://www.typescriptlang.org/docs/handbook/",                     "type": "article"},
                    {"title": "TypeScript Full Course – freeCodeCamp",  "url": "https://www.youtube.com/watch?v=30LWjhZzg50",                       "type": "video"}],
    "mongodb":     [{"title": "MongoDB University Free Courses",        "url": "https://learn.mongodb.com/",                                        "type": "course"},
                    {"title": "MongoDB Crash Course",                    "url": "https://www.youtube.com/watch?v=-56x56UppqQ",                      "type": "video"}],
    "git":         [{"title": "Git & GitHub Crash Course",              "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",                       "type": "video"},
                    {"title": "Pro Git Book (free)",                     "url": "https://git-scm.com/book/en/v2",                                   "type": "article"}],
    "linux":       [{"title": "Linux Command Line Basics – Udacity",    "url": "https://www.udacity.com/course/linux-command-line-basics--ud595",   "type": "course"},
                    {"title": "The Linux Command Line (free book)",      "url": "https://linuxcommand.org/tlcl.php",                                 "type": "article"}],
    "networking":  [{"title": "Computer Networking – Coursera",         "url": "https://www.coursera.org/learn/computer-networking",                "type": "course"},
                    {"title": "Networking Fundamentals – Professor Messer", "url": "https://www.professormesser.com/network-plus/n10-008/n10-008-video/n10-008-training-course/", "type": "video"}],
    "security":    [{"title": "Google Cybersecurity Certificate",       "url": "https://www.coursera.org/professional-certificates/google-cybersecurity", "type": "course"},
                    {"title": "OWASP Top 10",                            "url": "https://owasp.org/www-project-top-ten/",                            "type": "article"}],
    "figma":       [{"title": "Figma for Beginners – YouTube",          "url": "https://www.youtube.com/watch?v=FTFaQWZBqQ8",                       "type": "video"},
                    {"title": "Figma Official Learn Hub",                "url": "https://www.figma.com/resources/learn-design/",                    "type": "article"}],
    "powerbi":     [{"title": "Power BI Full Course – YouTube",         "url": "https://www.youtube.com/watch?v=AGrl-H87pRU",                       "type": "video"},
                    {"title": "Microsoft Power BI Learning",             "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", "type": "article"}],
    "excel":       [{"title": "Excel for Beginners – GCFGlobal",        "url": "https://edu.gcfglobal.org/en/excel/",                               "type": "article"},
                    {"title": "Excel Full Course – freeCodeCamp",       "url": "https://www.youtube.com/watch?v=Vl0H-qTclOg",                      "type": "video"}],
    "tableau":     [{"title": "Tableau Public Free Training",           "url": "https://www.tableau.com/learn/training",                            "type": "course"},
                    {"title": "Tableau for Beginners – YouTube",        "url": "https://www.youtube.com/watch?v=TPMlZxRRaBQ",                       "type": "video"}],
    "spark":       [{"title": "Apache Spark with Python – Udemy",       "url": "https://www.udemy.com/course/apache-spark-with-python-big-data-with-pyspark-and-spark/", "type": "course"},
                    {"title": "PySpark Official Docs",                   "url": "https://spark.apache.org/docs/latest/api/python/",                  "type": "article"}],
    "fastapi":     [{"title": "FastAPI Official Tutorial",              "url": "https://fastapi.tiangolo.com/tutorial/",                            "type": "article"},
                    {"title": "FastAPI Full Course – YouTube",           "url": "https://www.youtube.com/watch?v=7t2alSnE2-I",                      "type": "video"}],
    "django":      [{"title": "Django Official Tutorial",               "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",        "type": "article"},
                    {"title": "Django for Beginners – YouTube",         "url": "https://www.youtube.com/watch?v=rHux0gMZ3Eg",                      "type": "video"}],
    "redis":       [{"title": "Redis University Free Courses",          "url": "https://university.redis.com/",                                     "type": "course"},
                    {"title": "Redis Crash Course – YouTube",           "url": "https://www.youtube.com/watch?v=jgpVdJB2sKQ",                      "type": "video"}],
    "graphql":     [{"title": "GraphQL Official Learn",                 "url": "https://graphql.org/learn/",                                        "type": "article"},
                    {"title": "GraphQL Full Course – freeCodeCamp",     "url": "https://www.youtube.com/watch?v=ed8SzALpx1Q",                      "type": "video"}],
    "java":        [{"title": "Java Programming – MOOC.fi",             "url": "https://java-programming.mooc.fi/",                                 "type": "course"},
                    {"title": "Java Full Course – YouTube",             "url": "https://www.youtube.com/watch?v=eIrMbAQSU34",                      "type": "video"}],
    "dsa":         [{"title": "DSA – freeCodeCamp",                     "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "type": "course"},
                    {"title": "NeetCode DSA Roadmap",                   "url": "https://neetcode.io/roadmap",                                       "type": "article"}],
    "rust":        [{"title": "The Rust Book (free)",                   "url": "https://doc.rust-lang.org/book/",                                   "type": "article"},
                    {"title": "Rust Crash Course – YouTube",            "url": "https://www.youtube.com/watch?v=zF34dRivLOw",                      "type": "video"}],
    "go":          [{"title": "A Tour of Go",                           "url": "https://go.dev/tour/",                                              "type": "article"},
                    {"title": "Go Full Course – YouTube",               "url": "https://www.youtube.com/watch?v=un6ZyFkqFKo",                      "type": "video"}],
    "html":        [{"title": "HTML Full Course – freeCodeCamp",        "url": "https://www.youtube.com/watch?v=pQN-pnXPaVg",                      "type": "video"},
                    {"title": "MDN HTML Docs",                           "url": "https://developer.mozilla.org/en-US/docs/Web/HTML",                 "type": "article"}],
    "css":         [{"title": "CSS Full Course – freeCodeCamp",         "url": "https://www.youtube.com/watch?v=OXGznpKZ_sA",                      "type": "video"},
                    {"title": "MDN CSS Docs",                            "url": "https://developer.mozilla.org/en-US/docs/Web/CSS",                  "type": "article"}],
    "js":          [{"title": "JavaScript Full Course – freeCodeCamp",  "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg",                      "type": "video"},
                    {"title": "javascript.info",                         "url": "https://javascript.info/",                                         "type": "article"}],
    "c":           [{"title": "CS50 Introduction to C",               "url": "https://cs50.harvard.edu/x/2023/",                                   "type": "course"},
                    {"title": "C Reference – cppreference",              "url": "https://en.cppreference.com/w/c",                                   "type": "article"}],
    "cpp":         [{"title": "Learn C++ – Microsoft",                  "url": "https://learn.microsoft.com/en-us/cpp/cpp/",                        "type": "article"},
                    {"title": "C++ Core Guidelines",                   "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines",    "type": "article"}],
    "ruby":        [{"title": "Ruby Official Documentation",            "url": "https://www.ruby-lang.org/en/documentation/",                     "type": "article"},
                    {"title": "Ruby Course – freeCodeCamp",             "url": "https://www.youtube.com/watch?v=t_ispmWmdjY",                      "type": "video"}],
}

# ── Domain test questions ─────────────────────────────────────────────────────
DOMAIN_QUESTIONS = {
    "Data Scientist": [
        {"question": "Which library is primarily used for data manipulation?",       "options": ["NumPy", "Pandas", "TensorFlow", "Keras"],          "answer": "Pandas"},
        {"question": "What does ML stand for?",                                       "options": ["Machine Learning", "Meta Learning", "Model Logic", "None"], "answer": "Machine Learning"},
        {"question": "Which library is used for data visualisation?",                "options": ["Matplotlib", "Flask", "Django", "Node"],           "answer": "Matplotlib"},
        {"question": "Which algorithm is supervised?",                               "options": ["K-Means", "Linear Regression", "PCA", "Apriori"],  "answer": "Linear Regression"},
        {"question": "Which platform is used for big data processing?",              "options": ["Hadoop", "HTML", "CSS", "React"],                  "answer": "Hadoop"},
        {"question": "Which metric is used for classification evaluation?",          "options": ["Accuracy", "MSE", "RMSE", "None"],                 "answer": "Accuracy"},
        {"question": "Which tool is used for interactive notebooks?",                "options": ["Jupyter", "VS Code", "Eclipse", "Android Studio"], "answer": "Jupyter"},
        {"question": "Which is NOT a type of machine learning?",                     "options": ["Supervised", "Unsupervised", "Reinforcement", "Compilation"], "answer": "Compilation"},
        {"question": "Which Python library is used for statistical modelling?",      "options": ["statsmodels", "React", "Docker", "AWS"],           "answer": "statsmodels"},
        {"question": "What is a train-test split used for?",                         "options": ["Model evaluation", "Data storage", "UI design", "Deployment"], "answer": "Model evaluation"},
    ],
    "AI-ML Engineer": [
        {"question": "Which library is used for deep learning?",                     "options": ["TensorFlow", "Pandas", "Flask", "Django"],         "answer": "TensorFlow"},
        {"question": "Which is a type of neural network?",                           "options": ["CNN", "SQL", "HTML", "CSS"],                       "answer": "CNN"},
        {"question": "Which is a common loss function for regression?",              "options": ["MSE", "HTML", "CSS", "Docker"],                    "answer": "MSE"},
        {"question": "Which technique is used for NLP?",                             "options": ["Transformers", "React", "Node", "Linux"],          "answer": "Transformers"},
        {"question": "What is overfitting?",                                         "options": ["Model too complex", "Model too simple", "No data", "None"], "answer": "Model too complex"},
        {"question": "Which optimiser is most commonly used in deep learning?",      "options": ["Adam", "HTML", "CSS", "JS"],                       "answer": "Adam"},
        {"question": "Which activation function is most popular in hidden layers?",  "options": ["ReLU", "SQL", "Docker", "Linux"],                  "answer": "ReLU"},
        {"question": "Which framework is used for classical ML?",                    "options": ["Scikit-learn", "Bootstrap", "Tailwind", "jQuery"], "answer": "Scikit-learn"},
        {"question": "What is GPU computing library used with deep learning?",       "options": ["CUDA", "SQL", "Excel", "PowerBI"],                 "answer": "CUDA"},
        {"question": "What is transfer learning?",                                   "options": ["Reusing pretrained models", "Training from scratch", "Data cleaning", "None"], "answer": "Reusing pretrained models"},
    ],
    "Data Analyst": [
        {"question": "Which tool is used for BI dashboards?",                        "options": ["PowerBI", "React", "Node", "Docker"],              "answer": "PowerBI"},
        {"question": "Which language is used for database queries?",                 "options": ["SQL", "HTML", "CSS", "JS"],                        "answer": "SQL"},
        {"question": "Which is used for spreadsheet analysis?",                      "options": ["Excel", "VS Code", "Linux", "AWS"],                "answer": "Excel"},
        {"question": "Which chart type best shows trends over time?",                "options": ["Line chart", "Pie chart", "Bar chart", "None"],    "answer": "Line chart"},
        {"question": "Which SQL clause filters rows?",                               "options": ["WHERE", "JOIN", "GROUP BY", "ORDER BY"],           "answer": "WHERE"},
        {"question": "Which SQL clause aggregates grouped data?",                    "options": ["HAVING", "WHERE", "SELECT", "FROM"],               "answer": "HAVING"},
        {"question": "Which chart shows proportions of a whole?",                    "options": ["Pie chart", "Line chart", "Scatter", "None"],      "answer": "Pie chart"},
        {"question": "What is ETL?",                                                 "options": ["Extract Transform Load", "Edit Test Launch", "None", "Both"], "answer": "Extract Transform Load"},
        {"question": "Which Python library is used for data analysis?",              "options": ["Pandas", "React", "Docker", "AWS"],                "answer": "Pandas"},
        {"question": "What is a KPI?",                                               "options": ["Key Performance Indicator", "Key Python Interface", "None", "Both"], "answer": "Key Performance Indicator"},
    ],
    "Full Stack Developer": [
        {"question": "Which is a frontend JavaScript framework?",                    "options": ["React", "Node", "Docker", "Linux"],                "answer": "React"},
        {"question": "Which is a backend JavaScript runtime?",                       "options": ["Node", "React", "HTML", "CSS"],                    "answer": "Node"},
        {"question": "Which language handles page styling?",                         "options": ["CSS", "Python", "Java", "SQL"],                    "answer": "CSS"},
        {"question": "Which language defines page structure?",                       "options": ["HTML", "CSS", "JS", "Python"],                     "answer": "HTML"},
        {"question": "Which is a NoSQL database?",                                   "options": ["MongoDB", "React", "CSS", "HTML"],                 "answer": "MongoDB"},
        {"question": "Which is the most common API architectural style?",            "options": ["REST", "CSS", "HTML", "JS"],                       "answer": "REST"},
        {"question": "Which tool is used for version control?",                      "options": ["Git", "Docker", "Linux", "AWS"],                   "answer": "Git"},
        {"question": "Which handles client-side routing in React?",                  "options": ["React Router", "CSS", "HTML", "SQL"],              "answer": "React Router"},
        {"question": "Which is a Node.js server framework?",                         "options": ["Express", "React", "HTML", "CSS"],                 "answer": "Express"},
        {"question": "What does TypeScript add to JavaScript?",                      "options": ["Static typing", "Styling", "Routing", "None"],     "answer": "Static typing"},
    ],
    "Software Engineer": [
        {"question": "What does OOP stand for?",                                     "options": ["Object Oriented Programming", "Only One Program", "Open Program", "None"], "answer": "Object Oriented Programming"},
        {"question": "Which is a linear data structure?",                            "options": ["Array", "Tree", "Graph", "Heap"],                  "answer": "Array"},
        {"question": "Which sorting algorithm has O(n log n) average complexity?",   "options": ["Merge Sort", "Bubble Sort", "Selection Sort", "None"], "answer": "Merge Sort"},
        {"question": "What is Big-O notation used for?",                             "options": ["Algorithm complexity", "HTML styling", "DB queries", "None"], "answer": "Algorithm complexity"},
        {"question": "What is recursion?",                                           "options": ["Function calling itself", "Loop", "Condition", "None"], "answer": "Function calling itself"},
        {"question": "Which data structure follows LIFO?",                           "options": ["Stack", "Queue", "Array", "Tree"],                 "answer": "Stack"},
        {"question": "Which data structure follows FIFO?",                           "options": ["Queue", "Stack", "Array", "Tree"],                 "answer": "Queue"},
        {"question": "What is a compiler?",                                          "options": ["Converts source to machine code", "Executes HTML", "Runs CSS", "None"], "answer": "Converts source to machine code"},
        {"question": "What is a design pattern?",                                    "options": ["Reusable solution to common problem", "CSS layout", "DB schema", "None"], "answer": "Reusable solution to common problem"},
        {"question": "What is the purpose of unit testing?",                         "options": ["Test individual components", "Deploy app", "Design UI", "None"], "answer": "Test individual components"},
    ],
    "DevOps Engineer": [
        {"question": "What is Docker used for?",                                     "options": ["Containerisation", "Database", "Language", "Framework"], "answer": "Containerisation"},
        {"question": "Which is a popular CI/CD tool?",                               "options": ["Jenkins", "React", "Node", "HTML"],                "answer": "Jenkins"},
        {"question": "Which OS is most common in DevOps?",                           "options": ["Linux", "Windows", "Mac", "None"],                 "answer": "Linux"},
        {"question": "What is Kubernetes used for?",                                 "options": ["Container orchestration", "Database", "Language", "Tool"], "answer": "Container orchestration"},
        {"question": "What is a CI/CD pipeline?",                                    "options": ["Automated build/test/deploy flow", "Database", "Language", "None"], "answer": "Automated build/test/deploy flow"},
        {"question": "Which tool is used for infrastructure monitoring?",            "options": ["Prometheus", "React", "Node", "CSS"],              "answer": "Prometheus"},
        {"question": "Which tool is used for configuration management?",             "options": ["Ansible", "HTML", "CSS", "JS"],                    "answer": "Ansible"},
        {"question": "What is Infrastructure as Code (IaC)?",                       "options": ["Managing infra via code", "Writing HTML", "Designing UI", "None"], "answer": "Managing infra via code"},
        {"question": "Which is a cloud provider?",                                   "options": ["AWS", "React", "Node", "CSS"],                     "answer": "AWS"},
        {"question": "What is a load balancer?",                                     "options": ["Distributes traffic", "Stores data", "Writes code", "None"], "answer": "Distributes traffic"},
    ],
    "Cybersecurity Analyst": [
        {"question": "What is a firewall?",                                          "options": ["Network security system", "Database", "Language", "Framework"], "answer": "Network security system"},
        {"question": "What is phishing?",                                            "options": ["Social engineering attack", "Tool", "Language", "None"], "answer": "Social engineering attack"},
        {"question": "Which is a symmetric encryption algorithm?",                   "options": ["AES", "HTML", "CSS", "JS"],                        "answer": "AES"},
        {"question": "What is malware?",                                             "options": ["Malicious software", "Database", "Language", "None"], "answer": "Malicious software"},
        {"question": "What is a VPN?",                                               "options": ["Encrypted private network", "Database", "Language", "None"], "answer": "Encrypted private network"},
        {"question": "What is IDS?",                                                 "options": ["Intrusion Detection System", "Database", "Language", "None"], "answer": "Intrusion Detection System"},
        {"question": "What is a DDoS attack?",                                       "options": ["Distributed Denial of Service", "HTML", "CSS", "JS"], "answer": "Distributed Denial of Service"},
        {"question": "What is hashing?",                                             "options": ["One-way data transformation", "Two-way encryption", "None", "Both"], "answer": "One-way data transformation"},
        {"question": "Which tool is used for network packet analysis?",              "options": ["Wireshark", "React", "Node", "CSS"],               "answer": "Wireshark"},
        {"question": "What is the principle of least privilege?",                    "options": ["Minimum access rights", "Maximum access", "No access", "None"], "answer": "Minimum access rights"},
    ],
    "UI/UX Designer": [
        {"question": "Which tool is most popular for UI design?",                    "options": ["Figma", "React", "Node", "Docker"],                "answer": "Figma"},
        {"question": "What does UX stand for?",                                      "options": ["User Experience", "User XML", "None", "Both"],     "answer": "User Experience"},
        {"question": "What is a wireframe?",                                         "options": ["Low-fidelity layout sketch", "Code", "Database", "None"], "answer": "Low-fidelity layout sketch"},
        {"question": "What is a prototype?",                                         "options": ["Interactive working model", "Database", "Language", "None"], "answer": "Interactive working model"},
        {"question": "What is usability?",                                           "options": ["Ease of use", "Code quality", "Design aesthetics", "None"], "answer": "Ease of use"},
        {"question": "Which design principle ensures visual consistency?",           "options": ["Consistency", "Code", "Database", "None"],         "answer": "Consistency"},
        {"question": "What is typography in design?",                                "options": ["Art of arranging fonts", "Code", "Database", "None"], "answer": "Art of arranging fonts"},
        {"question": "What is accessibility in design?",                             "options": ["Usable by all people", "Code", "Database", "None"], "answer": "Usable by all people"},
        {"question": "What is a design system?",                                     "options": ["Reusable component library", "Database", "Language", "None"], "answer": "Reusable component library"},
        {"question": "What is user research?",                                       "options": ["Understanding user needs", "Writing code", "DB design", "None"], "answer": "Understanding user needs"},
    ],
    "Backend Developer": [
        {"question": "Which Python framework is used for REST APIs?",                "options": ["FastAPI", "React", "HTML", "CSS"],                 "answer": "FastAPI"},
        {"question": "Which is a relational database query language?",               "options": ["SQL", "React", "CSS", "HTML"],                     "answer": "SQL"},
        {"question": "What is an API?",                                              "options": ["Application Programming Interface", "Database", "Language", "None"], "answer": "Application Programming Interface"},
        {"question": "What is server-side rendering?",                               "options": ["HTML generated on server", "CSS styling", "JS animation", "None"], "answer": "HTML generated on server"},
        {"question": "What is REST?",                                                "options": ["Architectural API style", "Language", "Tool", "None"], "answer": "Architectural API style"},
        {"question": "Which HTTP method creates a resource?",                        "options": ["POST", "GET", "PUT", "DELETE"],                    "answer": "POST"},
        {"question": "Which HTTP method retrieves a resource?",                      "options": ["GET", "POST", "PUT", "DELETE"],                    "answer": "GET"},
        {"question": "What is JSON?",                                                "options": ["Lightweight data format", "Language", "Tool", "None"], "answer": "Lightweight data format"},
        {"question": "What is authentication?",                                      "options": ["Verifying user identity", "Storing data", "Designing UI", "None"], "answer": "Verifying user identity"},
        {"question": "What is caching?",                                             "options": ["Storing data for fast retrieval", "Deleting data", "Encrypting data", "None"], "answer": "Storing data for fast retrieval"},
    ],
}


# ── Core logic functions ──────────────────────────────────────────────────────

def normalize_skills(user_skills: list[str]) -> list[str]:
    """Normalise and alias-resolve raw skill strings (order-preserving, deduped)."""
    seen: dict[str, None] = {}
    for skill in user_skills:
        c = _canonical_skill(skill)
        if c:
            seen[c] = None
    return list(seen.keys())


def skills_to_feature_vector(user_skills: list[str]) -> list[int]:
    """
    Build the binary feature vector for the ML model: one column per SKILLS_LIST entry.
    Unknown or unmapped skills are ignored (all zeros for those features).
    """
    skill_set = set(normalize_skills(user_skills))
    vec = [1 if name in skill_set else 0 for name in SKILLS_LIST]
    if len(vec) != len(SKILLS_LIST):
        raise ValueError("Feature vector length does not match SKILLS_LIST")
    return vec


def compute_skill_gap(user_skills: list[str], domain: str) -> dict:
    """
    Compare user skills against the domain master set.
    Returns a dict with missing_skills, matched_skills, and match_percentage.
    """
    master_ordered = DOMAIN_SKILLS.get(domain, [])
    master = set(master_ordered)
    user_set = set(user_skills)
    matched = [skill for skill in master_ordered if skill in user_set]
    missing = [skill for skill in master_ordered if skill not in user_set]
    pct = round((len(matched) / len(master)) * 100, 1) if master else 0.0
    return {
        "domain": domain,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": pct,
    }


def compute_readiness_score(skill_match: float, assessment_performance: float) -> dict:
    """
    Weighted readiness formula:
        Score = (0.6 × skill_match) + (0.4 × assessment_performance)
    Both inputs are 0-100 percentages.
    """
    score = round((0.6 * skill_match) + (0.4 * assessment_performance), 1)
    if score >= 75:
        label = "Job Ready"
    elif score >= 45:
        label = "Developing"
    else:
        label = "Beginner"
    return {
        "skill_match": round(skill_match, 1),
        "assessment_performance": round(assessment_performance, 1),
        "readiness_score": score,
        "label": label,
    }


def get_resources_for_skills(missing_skills: list[str], limit: int = 2) -> list[dict]:
    """
    Return learning resources for each missing skill (up to `limit` per skill).
    """
    resources = []
    for skill in missing_skills:
        entries = SKILL_RESOURCES.get(skill, [])
        for entry in entries[:limit]:
            resources.append({"skill": skill, **entry})
    return resources


def get_xai_explanation(model, feature_names: list[str], input_vector: list[int], top_n: int = 3) -> list[str]:
    """
    Explainable AI: identify the top-N skills that most influenced the prediction
    by multiplying feature importances with the user's binary input vector.
    Returns a list of human-readable strings.
    """
    importances = model.feature_importances_
    # Weight importances by whether the user actually has the skill
    weighted = [(feat, importances[i] * input_vector[i])
                for i, feat in enumerate(feature_names)]
    weighted.sort(key=lambda x: x[1], reverse=True)
    top = [feat for feat, score in weighted if score > 0][:top_n]
    return [f"Your {skill.upper()} skill is a strong signal for this domain" for skill in top]


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC and a random salt."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored PBKDF2-HMAC hash."""
    try:
        salt, expected = password_hash.split("$", 1)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(candidate.hex(), expected)


def build_learning_roadmap(user_skills: list[str], domain: str, recent_readiness: float | None = None) -> dict | None:
    """
    Build a lightweight personalised roadmap from the user's current skill snapshot
    and their most likely target domain.
    """
    if domain not in DOMAIN_SKILLS:
        return None

    gap = compute_skill_gap(user_skills, domain)
    matched = gap["matched_skills"]
    missing = gap["missing_skills"]
    resources = get_resources_for_skills(missing[:4], limit=2)

    if not missing:
        summary = (
            f"You already cover the core {domain} stack. Focus now on portfolio depth, "
            "mock interviews, and shipping real projects that prove your readiness."
        )
        weekly_plan = [
            {
                "week": 1,
                "title": "Polish your portfolio",
                "objective": f"Turn your existing {domain} skills into strong proof of work.",
                "skills": matched[:3],
                "checkpoint": "Publish or refine one portfolio project with clear outcomes.",
            },
            {
                "week": 2,
                "title": "Interview preparation",
                "objective": "Translate your skill base into job-ready stories and practice rounds.",
                "skills": matched[3:6] or matched[:3],
                "checkpoint": "Complete at least one mock interview or timed practice session.",
            },
        ]
    else:
        summary = (
            f"Your current profile covers {gap['match_percentage']}% of the {domain} skill set. "
            f"Closing the next {min(4, len(missing))} gaps will make your recommendations and readiness stronger."
        )
        weekly_plan = []
        for index, skill in enumerate(missing[:4], start=1):
            checkpoint = (
                f"Finish one hands-on exercise in {skill} and add a short note about what you learned."
                if index < 4 else
                f"Combine {', '.join(missing[:min(3, len(missing))])} in one mini project for your portfolio."
            )
            weekly_plan.append({
                "week": index,
                "title": f"Week {index}: Focus on {skill.upper()}",
                "objective": f"Build practical confidence in {skill} for the {domain} path.",
                "skills": missing[max(0, index - 1):index + 1],
                "checkpoint": checkpoint,
            })

    if recent_readiness is not None:
        summary += f" Your latest readiness score is {round(recent_readiness, 1)}%."

    return {
        "target_domain": domain,
        "match_percentage": gap["match_percentage"],
        "current_strengths": matched[:5],
        "next_skills": missing[:6],
        "summary": summary,
        "weekly_plan": weekly_plan,
        "resources": resources,
    }


def build_fit_reasoning(user_skills: list[str], domain: str, confidence: float) -> dict:
    """
    Build richer, user-facing reasoning for why a domain fits the user now,
    what is holding them back, and what projects would best strengthen the match.
    """
    gap = compute_skill_gap(user_skills, domain)
    matched = gap["matched_skills"]
    missing = gap["missing_skills"]

    strongest = ", ".join(skill.upper() for skill in matched[:3]) if matched else "foundational transferable skills"
    short_missing = ", ".join(skill.upper() for skill in missing[:3]) if missing else "portfolio proof and interview depth"

    if matched and missing:
        fit_summary = (
            f"This role fits because your current profile already aligns with core signals like {strongest}. "
            f"That gives you a realistic starting point for {domain}, even though the recommendation is still limited by gaps in {short_missing}."
        )
        growth_summary = (
            f"Your match is strongest on what you already know, but moving from interest to real readiness means closing the next gaps in {short_missing}. "
            f"If you do that, this {round(confidence, 1)}% recommendation can become much more defensible."
        )
    elif matched:
        fit_summary = (
            f"This role fits strongly because you already cover many of the foundation skills, especially {strongest}. "
            f"Right now the biggest next step is turning those strengths into visible, portfolio-ready proof."
        )
        growth_summary = (
            f"You are not blocked by major stack gaps here. The growth opportunity is to show depth through projects, outcomes, and interview-ready explanations."
        )
    else:
        fit_summary = (
            f"This role is showing up more as a directional fit than a near-term fit. "
            f"You do not yet have strong direct skill overlap, so the recommendation is based on adjacent potential rather than immediate readiness."
        )
        growth_summary = (
            f"To make this role genuinely realistic, start by building foundations in {short_missing} and use projects to prove early momentum."
        )

    project_templates = DOMAIN_PROJECT_TEMPLATES.get(domain, [])
    project_skills = matched[:2] + missing[:2]
    skill_phrase = ", ".join(skill.upper() for skill in project_skills if skill) or domain
    project_suggestions = [
        template.format(skills=skill_phrase)
        for template in project_templates[:3]
    ]

    return {
        "fit_summary": fit_summary,
        "growth_summary": growth_summary,
        "missing_priority_skills": missing[:4],
        "project_suggestions": project_suggestions,
    }
