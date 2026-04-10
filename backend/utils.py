DOMAIN_SKILLS = {
    "Data Scientist": {
        "core": ["python", "ml"],
        "optional": ["sql", "tensorflow"]
    },
    "AI-ML Engineer": {
        "core": ["python", "ml"],
        "optional": ["tensorflow", "aws"]
    },
    "Data Analyst": {
        "core": ["sql", "excel"],
        "optional": ["powerbi", "python"]
    },
    "Full Stack Developer": {
        "core": ["html", "css", "js"],
        "optional": ["react", "node"]
    },
    "Software Engineer": {
        "core": ["dsa", "python"],
        "optional": ["java", "html", "css", "js"]
    },
    "DevOps Engineer": {
        "core": ["docker", "linux"],
        "optional": ["aws"]
    },
    "Cybersecurity Analyst": {
        "core": ["networking", "security"],
        "optional": ["linux"]
    },
    "UI/UX Designer": {
        "core": ["figma"],
        "optional": []
    },
    "Backend Developer": {
        "core": ["python", "node"],
        "optional": ["sql"]
    }
}

DOMAIN_DATA = {
    "Software Engineer": {"salary": "₹5–12 LPA", "demand": "High"},
    "Data Scientist": {"salary": "₹6–15 LPA", "demand": "High"},
    "AI-ML Engineer": {"salary": "₹10–18 LPA", "demand": "Very High"},
    "DevOps Engineer": {"salary": "₹6–15 LPA", "demand": "High"},
    "Cybersecurity Analyst": {"salary": "₹7–12 LPA", "demand": "High"},
    "UI/UX Designer": {"salary": "₹4–10 LPA", "demand": "Medium"},
    "Data Analyst": {"salary": "₹4–10 LPA", "demand": "High"},
    "Full Stack Developer": {"salary": "₹5–14 LPA", "demand": "Very High"},
    "Backend Developer": {"salary": "₹5–13 LPA", "demand": "High"}
}

DOMAIN_SKILLS = {
    "Software Engineer": ["python", "java", "dsa", "html", "css", "js"],
    "Data Scientist": ["python", "sql", "ml", "tensorflow"],
    "AI-ML Engineer": ["python", "ml", "tensorflow"],
    "DevOps Engineer": ["docker", "linux", "aws"],
    "Cybersecurity Analyst": ["networking", "linux", "security"],
    "UI/UX Designer": ["figma"],
    "Data Analyst": ["excel", "sql", "powerbi", "python"],
    "Full Stack Developer": ["html", "css", "js", "react", "node"],
    "Backend Developer": ["python", "node", "sql"]
}

SKILL_ALIASES = {
    "mysql": "sql",
    "postgres": "sql",
    "postgresql": "sql",
    "sqlite": "sql",

    "javascript": "js",
    "nodejs": "node",
    "reactjs": "react",

    "machinelearning": "ml",
    "deep learning": "ml",

    "aws cloud": "aws",

    "linux os": "linux",

    "excel sheets": "excel",

    "power bi": "powerbi",

    "cyber security": "security"
}

DOMAIN_QUESTIONS = {

    "Data Scientist": [
        {"question": "Which library is used for data analysis?", "options": ["NumPy", "Pandas", "TensorFlow", "Keras"], "answer": "Pandas"},
        {"question": "What does ML stand for?", "options": ["Machine Learning", "Meta Learning", "Model Logic", "None"], "answer": "Machine Learning"},
        {"question": "Which is used for visualization?", "options": ["Matplotlib", "Flask", "Django", "Node"], "answer": "Matplotlib"},
        {"question": "Which algorithm is supervised?", "options": ["K-Means", "Linear Regression", "PCA", "Apriori"], "answer": "Linear Regression"},
        {"question": "Which is used for big data?", "options": ["Hadoop", "HTML", "CSS", "React"], "answer": "Hadoop"},
        {"question": "Which metric is used for classification?", "options": ["Accuracy", "MSE", "RMSE", "None"], "answer": "Accuracy"},
        {"question": "Which is used for data cleaning?", "options": ["Pandas", "React", "Docker", "AWS"], "answer": "Pandas"},
        {"question": "Which language is most used in DS?", "options": ["Python", "HTML", "CSS", "PHP"], "answer": "Python"},
        {"question": "Which is NOT ML type?", "options": ["Supervised", "Unsupervised", "Reinforcement", "Compilation"], "answer": "Compilation"},
        {"question": "Which tool is used for notebooks?", "options": ["Jupyter", "VS Code", "Eclipse", "Android Studio"], "answer": "Jupyter"}
    ],

    "AI-ML Engineer": [
        {"question": "Which library is used for deep learning?", "options": ["TensorFlow", "Pandas", "Flask", "Django"], "answer": "TensorFlow"},
        {"question": "Which is a neural network type?", "options": ["CNN", "SQL", "HTML", "CSS"], "answer": "CNN"},
        {"question": "Which is used for model training?", "options": ["Python", "HTML", "CSS", "JS"], "answer": "Python"},
        {"question": "Which is a loss function?", "options": ["MSE", "HTML", "CSS", "Docker"], "answer": "MSE"},
        {"question": "Which is used for NLP?", "options": ["Transformers", "React", "Node", "Linux"], "answer": "Transformers"},
        {"question": "Which is used for GPU computing?", "options": ["CUDA", "SQL", "Excel", "PowerBI"], "answer": "CUDA"},
        {"question": "Which is overfitting?", "options": ["Model too complex", "Model too simple", "No data", "None"], "answer": "Model too complex"},
        {"question": "Which optimizer is common?", "options": ["Adam", "HTML", "CSS", "JS"], "answer": "Adam"},
        {"question": "Which activation function?", "options": ["ReLU", "SQL", "Docker", "Linux"], "answer": "ReLU"},
        {"question": "Which framework for ML?", "options": ["Scikit-learn", "Bootstrap", "Tailwind", "jQuery"], "answer": "Scikit-learn"}
    ],

    "Data Analyst": [
        {"question": "Which tool is used for dashboards?", "options": ["PowerBI", "React", "Node", "Docker"], "answer": "PowerBI"},
        {"question": "Which language is used for queries?", "options": ["SQL", "HTML", "CSS", "JS"], "answer": "SQL"},
        {"question": "Which is used for spreadsheets?", "options": ["Excel", "VS Code", "Linux", "AWS"], "answer": "Excel"},
        {"question": "Which chart shows trends?", "options": ["Line chart", "Pie chart", "Bar chart", "None"], "answer": "Line chart"},
        {"question": "Which function aggregates data?", "options": ["SUM", "HTML", "CSS", "React"], "answer": "SUM"},
        {"question": "Which is used for filtering?", "options": ["WHERE", "JOIN", "GROUP BY", "ORDER"], "answer": "WHERE"},
        {"question": "Which is used for joins?", "options": ["SQL", "CSS", "JS", "React"], "answer": "SQL"},
        {"question": "Which tool for ETL?", "options": ["SQL", "HTML", "CSS", "JS"], "answer": "SQL"},
        {"question": "Which chart shows proportions?", "options": ["Pie chart", "Line chart", "Scatter", "None"], "answer": "Pie chart"},
        {"question": "Which skill is key?", "options": ["Data cleaning", "Painting", "Gaming", "Cooking"], "answer": "Data cleaning"}
    ],

    "Full Stack Developer": [
        {"question": "Which is frontend?", "options": ["React", "Node", "Docker", "Linux"], "answer": "React"},
        {"question": "Which is backend runtime?", "options": ["Node", "React", "HTML", "CSS"], "answer": "Node"},
        {"question": "Which is styling language?", "options": ["CSS", "Python", "Java", "SQL"], "answer": "CSS"},
        {"question": "Which is markup?", "options": ["HTML", "CSS", "JS", "Python"], "answer": "HTML"},
        {"question": "Which is database?", "options": ["MongoDB", "React", "CSS", "HTML"], "answer": "MongoDB"},
        {"question": "Which is API type?", "options": ["REST", "CSS", "HTML", "JS"], "answer": "REST"},
        {"question": "Which is version control?", "options": ["Git", "Docker", "Linux", "AWS"], "answer": "Git"},
        {"question": "Which handles routing?", "options": ["React Router", "CSS", "HTML", "SQL"], "answer": "React Router"},
        {"question": "Which is server framework?", "options": ["Express", "React", "HTML", "CSS"], "answer": "Express"},
        {"question": "Which is package manager?", "options": ["npm", "SQL", "Excel", "PowerBI"], "answer": "npm"}
    ],

    "Software Engineer": [
        {"question": "What is OOP?", "options": ["Object Oriented Programming", "Only One Program", "Open Program", "None"], "answer": "Object Oriented Programming"},
        {"question": "Which is data structure?", "options": ["Array", "HTML", "CSS", "React"], "answer": "Array"},
        {"question": "Which is sorting algorithm?", "options": ["Merge Sort", "SQL", "HTML", "CSS"], "answer": "Merge Sort"},
        {"question": "Which is language?", "options": ["Java", "HTML", "CSS", "SQL"], "answer": "Java"},
        {"question": "Which is complexity?", "options": ["O(n)", "HTML", "CSS", "JS"], "answer": "O(n)"},
        {"question": "Which is paradigm?", "options": ["Functional", "CSS", "HTML", "SQL"], "answer": "Functional"},
        {"question": "Which is recursion?", "options": ["Function calling itself", "Loop", "Condition", "None"], "answer": "Function calling itself"},
        {"question": "Which is stack?", "options": ["LIFO", "FIFO", "None", "Both"], "answer": "LIFO"},
        {"question": "Which is queue?", "options": ["FIFO", "LIFO", "None", "Both"], "answer": "FIFO"},
        {"question": "Which is compiler?", "options": ["Converts code", "Executes HTML", "Runs CSS", "None"], "answer": "Converts code"}
    ],

    "DevOps Engineer": [
        {"question": "What is Docker?", "options": ["Container tool", "Database", "Language", "Framework"], "answer": "Container tool"},
        {"question": "Which is CI/CD tool?", "options": ["Jenkins", "React", "Node", "HTML"], "answer": "Jenkins"},
        {"question": "Which OS is common?", "options": ["Linux", "Windows", "Mac", "None"], "answer": "Linux"},
        {"question": "What is AWS?", "options": ["Cloud platform", "Database", "Language", "Tool"], "answer": "Cloud platform"},
        {"question": "Which is version control?", "options": ["Git", "Docker", "AWS", "Linux"], "answer": "Git"},
        {"question": "Which is container orchestration?", "options": ["Kubernetes", "SQL", "HTML", "CSS"], "answer": "Kubernetes"},
        {"question": "What is pipeline?", "options": ["Automation flow", "Database", "Language", "None"], "answer": "Automation flow"},
        {"question": "Which is monitoring tool?", "options": ["Prometheus", "React", "Node", "CSS"], "answer": "Prometheus"},
        {"question": "Which is config tool?", "options": ["Ansible", "HTML", "CSS", "JS"], "answer": "Ansible"},
        {"question": "What is deployment?", "options": ["Release app", "Write code", "Design UI", "None"], "answer": "Release app"}
    ],

    "Cybersecurity Analyst": [
        {"question": "What is firewall?", "options": ["Security system", "Database", "Language", "Framework"], "answer": "Security system"},
        {"question": "What is phishing?", "options": ["Attack", "Tool", "Language", "None"], "answer": "Attack"},
        {"question": "Which is encryption?", "options": ["AES", "HTML", "CSS", "JS"], "answer": "AES"},
        {"question": "What is malware?", "options": ["Malicious software", "Database", "Language", "None"], "answer": "Malicious software"},
        {"question": "Which is protocol?", "options": ["HTTPS", "React", "Node", "CSS"], "answer": "HTTPS"},
        {"question": "What is VPN?", "options": ["Secure network", "Database", "Language", "None"], "answer": "Secure network"},
        {"question": "What is IDS?", "options": ["Intrusion Detection", "Database", "Language", "None"], "answer": "Intrusion Detection"},
        {"question": "Which is attack type?", "options": ["DDoS", "HTML", "CSS", "JS"], "answer": "DDoS"},
        {"question": "What is hashing?", "options": ["One-way encryption", "Two-way", "None", "Both"], "answer": "One-way encryption"},
        {"question": "Which is tool?", "options": ["Wireshark", "React", "Node", "CSS"], "answer": "Wireshark"}
    ],

    "UI/UX Designer": [
        {"question": "Which tool for design?", "options": ["Figma", "React", "Node", "Docker"], "answer": "Figma"},
        {"question": "What is UX?", "options": ["User Experience", "User XML", "None", "Both"], "answer": "User Experience"},
        {"question": "What is UI?", "options": ["User Interface", "User Input", "None", "Both"], "answer": "User Interface"},
        {"question": "What is wireframe?", "options": ["Layout", "Code", "Database", "None"], "answer": "Layout"},
        {"question": "What is prototype?", "options": ["Working model", "Database", "Language", "None"], "answer": "Working model"},
        {"question": "What is usability?", "options": ["Ease of use", "Code", "Design", "None"], "answer": "Ease of use"},
        {"question": "Which principle?", "options": ["Consistency", "Code", "Database", "None"], "answer": "Consistency"},
        {"question": "Which color model?", "options": ["RGB", "SQL", "HTML", "CSS"], "answer": "RGB"},
        {"question": "What is typography?", "options": ["Fonts", "Code", "Database", "None"], "answer": "Fonts"},
        {"question": "What is accessibility?", "options": ["Usable for all", "Code", "Database", "None"], "answer": "Usable for all"}
    ],

    "Backend Developer": [
        {"question": "Which language is backend?", "options": ["Python", "HTML", "CSS", "Figma"], "answer": "Python"},
        {"question": "Which is database?", "options": ["SQL", "React", "CSS", "HTML"], "answer": "SQL"},
        {"question": "What is API?", "options": ["Interface", "Database", "Language", "None"], "answer": "Interface"},
        {"question": "Which framework?", "options": ["Django", "React", "HTML", "CSS"], "answer": "Django"},
        {"question": "What is server?", "options": ["Handles requests", "Database", "Language", "None"], "answer": "Handles requests"},
        {"question": "What is REST?", "options": ["API style", "Language", "Tool", "None"], "answer": "API style"},
        {"question": "Which method creates data?", "options": ["POST", "GET", "PUT", "DELETE"], "answer": "POST"},
        {"question": "Which method fetches?", "options": ["GET", "POST", "PUT", "DELETE"], "answer": "GET"},
        {"question": "What is JSON?", "options": ["Data format", "Language", "Tool", "None"], "answer": "Data format"},
        {"question": "What is authentication?", "options": ["Verify user", "Store data", "Design UI", "None"], "answer": "Verify user"}
    ]
}