\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{multicol}
\usepackage{graphicx}
\usepackage{fontawesome5}
\input{glyphtounicode}

% Margins
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.19in}
\addtolength{\topmargin}{-.7in}
\addtolength{\textheight}{1.4in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\titleformat{\section}{\scshape\raggedright\large\bfseries}{}{0em}{}[\titlerule]
\pdfgentounicode=1

% Commands
\newcommand{\resumeItem}[1]{\item\small{#1 \vspace{-2pt}}}
\newcommand{\resumeSubheading}[4]{
  \item \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{\large #1} & \textbf{\small #2} \\
    \textit{\large #3} & \textit{\small #4} \\
  \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeProjectHeading}[2]{
  \item \begin{tabular*}{1.0\textwidth}{l@{\extracolsep{\fill}}r}
    \textbf{\large #1} & \textbf{\small #2} \\
  \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

\begin{center}
  {\Huge \scshape Mariyala Abhinav Teja} \\ \vspace{1pt}
  Hyderabad, Telangana, India \\ \vspace{3pt}

  \makebox[\linewidth]{\small
    \href{tel:+917893286907}{\faPhone\ +91 7893286907} ~
    \href{https://abhinavteja.vercel.app}{\faGlobe\ Portfolio} ~
    \href{mailto:mariyalaabhinavteja@gmail.com}{\faEnvelope\ mariyalaabhinavteja@gmail.com} ~
    \href{https://linkedin.com/in/abhinav-teja-40855a293/}{\faLinkedin\ linkedin/abhinav-teja} ~
    \href{https://github.com/abhinavteja123}{\faGithub\ github/abhinavteja123}
  }
\end{center}

% ---------- EDUCATION ----------
\section{Education}
\resumeSubHeadingListStart
\resumeSubheading{SRM University AP}{2023 -- 2027}
{B.Tech in Computer Science and Engineering — CGPA: \textbf{8.08}}{Andhra Pradesh, India}

\resumeSubheading{Sri Chaitanya Junior College}{2021 -- 2023}
{Class XII (MPC) — \textbf{93.1\%}}{Hyderabad, India}

\resumeSubheading{Johnson Grammar School}{2021}
{Class X (CBSE) — \textbf{86\%}}{Hyderabad, India}
\resumeSubHeadingListEnd

% ---------- SKILLS ----------
\section{Coursework / Skills}
\begin{multicols}{3}
\begin{itemize}[itemsep=-1pt]
\item Data Structures \& Algorithms
\item AWS Cloud Practitioner
\item Web Development
\item Machine Learning
\item Power BI
\item Advanced Excel
\item MS Office
\item UI/UX Design (Figma)
\item Docker
\item Prompt Engineering
\item AI Tools
\item Digital Marketing
\item Stock Market Analysis
\item Leadership
\item Creativity
\end{itemize}
\end{multicols}

% ---------- PROJECTS ----------
\section{Projects}
\resumeSubHeadingListStart

\resumeProjectHeading{E-commerce Website | HTML, CSS, JavaScript, PHP, MySQL}{2025}
\resumeItemListStart
\resumeItem{Enhanced a full-stack e-commerce platform with an admin dashboard managing \textbf{100+ products}, authentication, and order tracking.}
\resumeItemListEnd

\resumeProjectHeading{Autonomous Incident Management System | Python,Gemini API,Google ADK}{2025}
\resumeItemListStart
\resumeItem{Built a multi-agent AI system to autonomously detect, analyze, and remediate production incidents in real time.}
\resumeItem{Implemented LLM-powered agents for log analysis, risk classification, planning, and automated execution.}
\resumeItem{React Vite,Fast API,Python,ML,Multi Agent}
\resumeItem{Integrated WhatsApp and Email alerts with human-in-the-loop approval for critical remediations.}

\resumeItemListEnd


\resumeProjectHeading{ERP Attendance App | React Native, PostgreSQL}{2025}
\resumeItemListStart
\resumeItem{Built an ERP-based attendance application supporting manual and face-recognition based entry.}
\resumeItemListEnd

\resumeProjectHeading{Anomaly Detection System | Python, Machine Learning}{2025}
\resumeItemListStart
\resumeItem{Trained machine learning models for time-series anomaly detection, achieving \textbf{80\% detection accuracy}.}
\resumeItemListEnd

\resumeProjectHeading{AI Attendance System | CNN, Raspberry Pi, React Native}{2025}
\resumeItemListStart
\resumeItem{Engineered an AI-based attendance system with PostgreSQL and SQLite backends, supporting offline access for rural environments.}
\resumeItemListEnd

\resumeProjectHeading{Transformer-Based Abstract Classification | Python, DistilBERT, Streamlit}{2025}
\resumeItemListStart
\resumeItem{Designed a GenAI text classification system using DistilBERT, achieving \textbf{90\%+ accuracy}.}
\resumeItemListEnd

\resumeProjectHeading
{Stock Market Prediction | ML, DL, Python, React-Vite \hspace{0.5em}
\href{https://stock-market-prediction-frontend.onrender.com/}{[Project Link]}}
{2025}
\resumeItemListStart
\resumeItem{Deployed ML and LSTM-based stock prediction models achieving \textbf{70\% accuracy} for next-day prediction.}
\resumeItemListEnd

\resumeSubHeadingListEnd

% ---------- INTERNSHIP ----------
\section{Internship}
\resumeSubHeadingListStart

\resumeSubheading
{Kokonda Dental Hospital \hspace{0.5em}
\href{https://kokondadentalhospital.com}{[Website]}}
{May -- Aug 2025}
{Full Stack Developer Intern}
{Hyderabad, India}
\resumeItemListStart
\resumeItem{Improved full-stack features using React.js and Firebase backend, reducing page load time by \textbf{25\%}.}
\resumeItemListEnd

\resumeSubheading{Auracoders}{May 2025 -- Present}
{Data Entry \& IT Support}{Hyderabad, India}
\resumeItemListStart
\resumeItem{Processed and validated \textbf{1,000+ records} using Advanced Excel while supporting internal IT operations.}
\resumeItemListEnd

\resumeSubHeadingListEnd

% ---------- TECHNICAL SKILLS ----------
\section{Technical Skills}
\begin{itemize}[leftmargin=0.15in, label={}]
\item \textbf{Languages:} Python, C, C++, JavaScript, SQL, PHP, HTML, CSS,Java
\item \textbf{Frameworks \& Tools:} React, Firebase, PostgreSQL, MySQL, Docker, AWS (EC2, S3, IAM), Power BI, Figma,Google ADK, Excel 
\end{itemize}

% ---------- CERTIFICATIONS ----------
\section{Certifications}
\href{https://www.credly.com/badges/68f883dc-de95-4a4d-bc50-27ef493a0e81/public_url}{AWS Cloud Practitioner — 2025} \\
\href{https://trainings.internshala.com/s/v/3522349/8182c6a9}{Digital Marketing — Internshala} \\
\href{https://www.udemy.com/certificate/UC-5b27b270-a4fd-4584-ab92-b012a963937d/}{Web \& Mobile UI/UX Design (Figma) — Udemy} \\
\href{https://www.udemy.com/certificate/UC-480b35f6-7fda-4825-8ab4-1468910a57f2/}{Microsoft Power BI — Udemy} \\
\href{https://www.nptel.com}{The Joy of Python — NPTEL}

% ---------- EXTRACURRICULAR ----------
\section{Extracurricular}
\resumeSubHeadingListStart

\resumeSubheading{Student Council Member}{2024 -- 2025}
{Cultural Co-Head — SRM University AP}{Andhra Pradesh, India}
\resumeItemListStart
\resumeItem{Coordinated national-level cultural events with \textbf{1,000+ participants}.}
\resumeItemListEnd

\resumeSubheading{Student Council Member}{2025 -- 2026}
{Cultural Head — SRM University AP}{Andhra Pradesh, India}
\resumeItemListStart
\resumeItem{Led cultural council operations and coordinated multiple student clubs and events.}
\resumeItemListEnd

\resumeSubHeadingListEnd

\end{document}
