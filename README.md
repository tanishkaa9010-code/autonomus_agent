# WEB-AUDITOR

## Overview

WEB-AUDITOR is a web security auditing application designed to perform automated, first-level security analysis of websites.

The application accepts a website URL, retrieves the accessible webpage and its HTTP response information, analyzes the collected data for common security-related issues, and presents the findings in a structured format.

The project is intended to help developers quickly identify common security weaknesses without requiring manual inspection of webpage source code, forms, scripts, headers, and links.

WEB-AUDITOR is designed as an initial security assessment tool. It does not replace a professional penetration test, vulnerability assessment, or comprehensive security audit.

---

## Objectives

The primary objectives of WEB-AUDITOR are to:

* Automate common website security checks.
* Identify potentially insecure website configurations and implementation patterns.
* Reduce the effort required for initial security inspection.
* Present security observations in a clear and understandable format.
* Provide a foundation for expanding into more advanced automated security analysis.

---

## Core Features

### 1. Website Analysis

Users can provide a website URL for analysis.

The backend retrieves the website and analyzes available HTTP response data and webpage content.

The analysis can include:

* HTTP response information
* HTTP security headers
* HTML structure
* Forms
* Password fields
* JavaScript event handlers
* External links
* Other security-related observations

### 2. Security Header Analysis

WEB-AUDITOR checks for important security-related HTTP headers and identifies headers that are missing.

Examples include:

* Content-Security-Policy
* X-Frame-Options
* X-Content-Type-Options
* Referrer-Policy
* Permissions-Policy
* Strict-Transport-Security

These headers provide important browser-level security controls and help mitigate several classes of web-based attacks.

### 3. Password Form Analysis

The application identifies password forms and examines their implementation for relevant security attributes.

The audit can identify:

* Password forms
* Missing password autocomplete attributes
* Other password-related observations

This provides developers with information that can be used to improve authentication form configuration.

### 4. Inline JavaScript Detection

WEB-AUDITOR detects inline JavaScript event handlers such as:

```html
<button onclick="login()">
```

Inline event handlers can make the implementation of strict Content Security Policies more difficult and therefore represent an important security-related observation.

### 5. External Link Analysis

The application identifies external links present on the analyzed webpage.

This provides visibility into third-party destinations and external resources that may require additional review.

### 6. Structured Audit Results

The backend produces structured audit findings that can be consumed by the frontend.

This allows the application to present security observations in a consistent format and provides a foundation for future severity classification, recommendations, and reporting.

---

## System Architecture

WEB-AUDITOR follows a frontend-backend architecture.

```text
                         User
                           |
                           v
                  +----------------+
                  |    Frontend    |
                  |  Audit Interface|
                  +-------+--------+
                          |
                          | HTTP Request
                          v
                  +----------------+
                  |     Backend    |
                  |    FastAPI     |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Website Fetcher|
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | HTML / Header  |
                  |    Analysis    |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Audit Findings |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  |    Frontend    |
                  | Results Display|
                  +----------------+
```

The frontend is responsible for user interaction and displaying results, while the backend handles website retrieval, analysis, and generation of audit findings.

---

## Project Structure

```text
WEB-AUDITOR/
|
├── backend/
│   ├── main.py
│   └── ...
|
├── frontend/
│   └── ...
|
├── .venv/
|
├── .gitignore
├── README.md
└── ...
```

### Backend

The `backend` directory contains the server-side implementation of the auditing system.

The backend is responsible for:

* Receiving audit requests
* Processing website URLs
* Retrieving website content
* Inspecting HTTP response headers
* Parsing webpage content
* Running security checks
* Generating structured findings
* Returning results to the frontend

The primary FastAPI application is located at:

```text
backend/main.py
```

### Frontend

The frontend provides the user-facing interface.

Its responsibilities include:

* Accepting the website URL
* Initiating an audit
* Communicating with the backend
* Displaying audit results
* Presenting security observations in an understandable format

---

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* HTTP and HTML parsing libraries used by the project

### Frontend

* HTML
* CSS
* JavaScript
* Frontend framework and libraries configured in the project

### Development and Version Control

* Git
* GitHub
* Visual Studio Code
* Python virtual environment

---

## Audit Workflow

The application follows the following workflow:

```text
1. User enters a website URL
             |
             v
2. Frontend sends request
             |
             v
3. Backend receives URL
             |
             v
4. Backend retrieves website
             |
             v
5. HTTP response is analyzed
             |
             v
6. HTML content is analyzed
             |
             v
7. Security checks are performed
             |
             v
8. Findings are structured
             |
             v
9. Results are returned
             |
             v
10. Frontend displays the audit
```

---

## Security Checks

WEB-AUDITOR currently focuses on lightweight, automated security observations.

| Check                   | Description                                                               |
| ----------------------- | ------------------------------------------------------------------------- |
| Security Headers        | Identifies missing security-related HTTP headers                          |
| Password Forms          | Detects password-related forms                                            |
| Password Autocomplete   | Identifies password fields without appropriate autocomplete configuration |
| Inline JavaScript       | Detects inline JavaScript event handlers                                  |
| External Links          | Identifies links pointing to external destinations                        |
| Additional Observations | Provides other security-related information detected during analysis      |

The exact checks and results depend on the implementation and the website being analyzed.

---

## Backend API

The backend is implemented using FastAPI.

When the development server is running, FastAPI provides interactive API documentation.

```text
http://127.0.0.1:8000/docs
```

An alternative documentation interface is available at:

```text
http://127.0.0.1:8000/redoc
```

The available endpoints depend on the implementation in `backend/main.py`.

---

## Installation

### Prerequisites

Ensure the following are installed:

* Python 3.x
* Node.js and npm, if required by the frontend
* Git

### Clone the Repository

```bash
git clone <repository-url>
cd WEB-AUDITOR
```

### Create a Python Virtual Environment

```bash
python -m venv .venv
```

### Activate the Virtual Environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### Install Backend Dependencies

If a `requirements.txt` file is provided:

```bash
pip install -r requirements.txt
```

---

## Running the Backend

From the project root directory:

```bash
python -m uvicorn backend.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

The `--reload` option enables automatic server reloading during development when source files are modified.

---

## Running the Frontend

The frontend should be started according to its configured build system.

For a Node.js-based frontend, the typical setup is:

```bash
npm install
```

followed by the appropriate development command, such as:

```bash
npm start
```

or:

```bash
npm run dev
```

The exact command depends on the frontend configuration present in the repository.

---

## Example Audit

A typical audit may produce findings such as:

```text
Website: https://example.com

Security Observations

- Missing security headers
- Password form detected
- Missing password autocomplete attributes
- Inline JavaScript event handlers detected
- External links detected
```

The actual findings depend on the configuration and implementation of the website being analyzed.

---

## Design Considerations

### Automated First-Level Analysis

The system focuses on quickly identifying common security-related observations rather than attempting to perform a complete penetration test.

### Separation of Responsibilities

The frontend and backend are separated so that the auditing logic can be developed independently from the user interface.

### Extensibility

The auditing architecture can be extended with additional checks without requiring fundamental changes to the overall application structure.

### Structured Findings

Audit results are returned in a structured format, allowing the frontend and future reporting systems to consume the same audit data.

---

## Future Development

Potential future improvements include:

### Advanced Security Checks

* Cookie security attribute analysis
* CORS configuration analysis
* Content Security Policy analysis
* Mixed-content detection
* TLS configuration analysis
* Subresource Integrity checks
* Clickjacking protection checks
* Open redirect detection
* Security.txt detection
* Sensitive information exposure detection

### Risk Classification

Introduce standardized severity levels such as:

```text
Critical
High
Medium
Low
Informational
```

This would allow findings to be prioritized according to their potential impact.

### Remediation Recommendations

Each finding could provide:

* Explanation of the issue
* Potential security impact
* Recommended remediation
* Example of a secure configuration

### Reporting

Future versions could support:

* Downloadable audit reports
* PDF reports
* JSON export
* Audit history
* Comparison between multiple audits

### AI-Assisted Analysis

An AI-based analysis layer could be introduced to:

* Explain technical findings in simpler language
* Prioritize security observations
* Generate remediation recommendations
* Summarize the overall audit
* Identify relationships between multiple findings

### Continuous Monitoring

A future version could periodically scan authorized websites and notify users when security configurations or audit results change.

---

## Limitations

WEB-AUDITOR performs automated checks based on information that is accessible during the audit.

It may not detect:

* Application-specific vulnerabilities
* Authentication bypasses
* Business logic vulnerabilities
* Complex authorization issues
* Server-side vulnerabilities
* Vulnerabilities requiring authenticated access
* Vulnerabilities requiring extensive manual testing

Therefore, the results should be treated as an initial security assessment rather than a complete security evaluation.

---

## Security and Responsible Use

WEB-AUDITOR should only be used to analyze websites that you own or have explicit authorization to test.

Users are responsible for ensuring that their use of the application complies with applicable laws, policies, and authorization requirements.

The project is intended for authorized security testing, development, research, and educational purposes.

---

## Development

The project is structured to allow additional auditing modules and security checks to be integrated as development continues.

Contributions can focus on:

* New security checks
* Improved analysis accuracy
* Better result classification
* Frontend improvements
* Performance optimization
* Reporting capabilities
* Automated testing
* Documentation

---

## Conclusion

WEB-AUDITOR provides an automated approach to performing an initial security inspection of websites.

By combining website retrieval, HTTP header analysis, HTML inspection, form analysis, JavaScript detection, and external-link analysis, the application provides developers with a practical overview of common security-related observations.

The current implementation establishes a foundation that can be extended into a more comprehensive web security assessment platform with advanced vulnerability detection, risk scoring, remediation guidance, reporting, and continuous monitoring.
