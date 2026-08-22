<<<<<<< HEAD
# autonomus_agent
=======
# 🛡️ WEB-AUDITOR

### Autonomous Web Security Auditing & Browser Agent

WEB-AUDITOR is an autonomous browser security auditing system that combines **Gemini AI**, **WebCMD**, browser automation, workflow memory, self-healing recovery, and security analysis to inspect web applications.

The system can understand a web page, generate a browser workflow, execute actions, verify the result, recover from failures, and then perform a security audit of the target website.

---

## 🚀 Key Features

- 🤖 **AI-powered autonomous browser agent**
- 🧠 **Gemini-based workflow generation**
- 🌐 **WebCMD browser automation**
- 📚 **Workflow memory**
- 🩹 **Self-healing workflow recovery**
- 🔍 **Automated security scanning**
- 📊 **Risk scoring and severity analysis**
- 📄 **Interactive HTML security dashboard**
- 💾 **JSON security and risk reports**
- 🖼️ **Failure screenshots and recovery reports**
- 🔄 **Fallback execution when Gemini is unavailable**

---

## 🏗️ System Workflow

```text
                    ┌──────────────────┐
                    │    Target Web    │
                    │     Website      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Browser Agent  │
                    │   reads page     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Gemini AI     │
                    │ Generate Plan    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     WebCMD       │
                    │ Execute Actions  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Verification   │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
              SUCCESS                  FAILURE
                │                         │
                │                         ▼
                │                ┌──────────────────┐
                │                │ Recovery System  │
                │                │ + Memory Fallback│
                │                └────────┬─────────┘
                │                         │
                └────────────┬────────────┘
                             ▼
                    ┌──────────────────┐
                    │ Security Scanner │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Risk Analysis  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  HTML Dashboard  │
                    └──────────────────┘
>>>>>>> 2d2a911 (Complete WEB-AUDITOR implementation)
