"""
WEB-AUDITOR Backend API
=======================
FastAPI server connecting the agent, security scanner, risk analyzer,
WebCMD tools, and HTML dashboard to any frontend or external consumer.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure agent directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

# Import agent modules safely
try:
    from security_scanner import scan_page, scan_website
    from risk_analyzer import analyze_report
    from report_generator import generate_report
    from webcmd_tools import (
        list_sessions,
        cleanup_idle_sessions,
        create_session,
        close_session,
        start_webcmd
    )
except ImportError as e:
    print(f"⚠️ Warning during agent module imports: {e}")

app = FastAPI(
    title="WEB-AUDITOR API",
    description="REST API connecting autonomous security auditing, risk analysis, and WebCMD execution.",
    version="1.0.0"
)

# Enable CORS for all frontends/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory scan status tracking
scan_status: Dict[str, Any] = {
    "state": "idle",
    "last_url": None,
    "last_scan_time": None,
    "error": None
}


class ScanRequest(BaseModel):
    url: str
    auto_discover: Optional[bool] = False
    background: Optional[bool] = False


PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ WEB-AUDITOR — Autonomous Web Security Platform</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #080d16;
            color: #e8ecf1;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            min-height: 100vh;
            padding: 30px 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .hero-card {
            background: #0d1422;
            border: 1px solid #243047;
            border-radius: 18px;
            padding: 35px;
            margin-bottom: 30px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35);
        }
        .brand-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .brand-title { font-size: 32px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
        .brand-badge {
            background: #1c3654;
            color: #7fc1ff;
            border: 1px solid #315b84;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        .hero-subtitle { color: #8996a8; font-size: 15px; margin-bottom: 25px; }
        .input-group { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
        .url-input {
            flex: 1;
            min-width: 280px;
            background: #101827;
            border: 1px solid #27344c;
            border-radius: 12px;
            padding: 16px 20px;
            color: #ffffff;
            font-size: 15px;
            font-family: "Consolas", monospace;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .url-input:focus {
            border-color: #62b0ff;
            box-shadow: 0 0 0 3px rgba(98, 176, 255, 0.2);
        }
        .scan-btn {
            background: linear-gradient(135deg, #1e70bf 0%, #0052cc 100%);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 16px 28px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: transform 0.15s, box-shadow 0.15s, opacity 0.2;
            white-space: nowrap;
        }
        .scan-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 82, 204, 0.4);
        }
        .scan-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none; }
        .options-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
        }
        .presets { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .preset-label { font-size: 12px; color: #687587; text-transform: uppercase; font-weight: 700; }
        .preset-chip {
            background: #141f33;
            color: #cbd3dd;
            border: 1px solid #27344c;
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .preset-chip:hover { background: #1c2e4d; color: #62b0ff; border-color: #62b0ff; }
        .toggle-label { display: flex; align-items: center; gap: 8px; color: #a0aec0; font-size: 13px; cursor: pointer; user-select: none; }
        .toggle-label input { cursor: pointer; accent-color: #62b0ff; width: 16px; height: 16px; }
        .status-card {
            display: none;
            background: #101c2e;
            border: 1px solid #1e4976;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 30px;
            animation: pulse-glow 2s infinite alternate;
        }
        @keyframes pulse-glow {
            from { box-shadow: 0 0 15px rgba(98, 176, 255, 0.1); }
            to { box-shadow: 0 0 25px rgba(98, 176, 255, 0.25); }
        }
        .status-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(98, 176, 255, 0.2);
            border-top-color: #62b0ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .status-title { font-size: 18px; font-weight: 700; color: #62b0ff; }
        .status-log {
            font-family: "Consolas", monospace;
            font-size: 13px;
            color: #cbd3dd;
            background: #080d16;
            padding: 14px;
            border-radius: 8px;
            border: 1px solid #1a273b;
        }
        #resultsSection { display: none; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 25px;
        }
        .card {
            background: #0d1422;
            border: 1px solid #243047;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
        }
        .card:hover { transform: translateY(-2px); border-color: #52617c; }
        .card h3 { font-size: 11px; color: #8d99aa; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
        .card .value { font-size: 28px; font-weight: 800; color: #ffffff; }
        .card .score-total { font-size: 14px; color: #687587; }
        .card.high-card .value { color: #ff8585; }
        .card.medium-card .value { color: #ffc46b; }
        .card.low-card .value { color: #ffe46b; }
        .card.info-card .value { color: #7fc1ff; }
        .risk-bar { height: 6px; background: #1a2538; border-radius: 4px; margin: 10px 0; overflow: hidden; }
        .risk-fill { height: 100%; background: linear-gradient(90deg, #62b0ff, #ffb84d, #ff5c5c); transition: width 0.6s ease; }
        .risk-label {
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        .risk-label.high { background: #4b1e25; color: #ff8585; }
        .risk-label.medium { background: #4b361c; color: #ffc46b; }
        .risk-label.low { background: #4a431c; color: #ffe46b; }
        .risk-label.safe { background: #1c4b2b; color: #7fe48d; }
        .section-box {
            background: #0d1422;
            border: 1px solid #243047;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 25px;
        }
        .section-box h2 { font-size: 18px; color: #ffffff; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
        .method-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
        .method-item {
            background: #101827;
            border: 1px solid #27324a;
            border-radius: 10px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .method-label { color: #687587; font-size: 11px; text-transform: uppercase; font-weight: 700; }
        .method-item strong { color: #62b0ff; font-size: 14px; }
        .table-controls { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; }
        .search-box {
            flex: 1;
            min-width: 220px;
            max-width: 400px;
            background: #101827;
            border: 1px solid #27324a;
            border-radius: 8px;
            padding: 10px 14px;
            color: #ffffff;
            font-size: 13px;
            outline: none;
        }
        .search-box:focus { border-color: #62b0ff; }
        .filters { display: flex; gap: 6px; flex-wrap: wrap; }
        .filter-btn {
            background: #101827;
            border: 1px solid #27324a;
            color: #9eabbc;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.15s;
        }
        .filter-btn:hover, .filter-btn.active {
            background: #1c3654;
            color: #7fc1ff;
            border-color: #62b0ff;
        }
        .table-wrapper { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; background: #101827; border-radius: 10px; overflow: hidden; font-size: 13px; }
        th {
            background: #151f31;
            color: #9eabbc;
            padding: 12px 14px;
            text-align: left;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.6px;
            border-bottom: 1px solid #27324a;
        }
        td { padding: 12px 14px; border-bottom: 1px solid #1c2739; color: #cbd3dd; }
        tbody tr:hover { background: #141f33; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
        .badge.high { background: #4b1e25; color: #ff8585; border: 1px solid #7a3039; }
        .badge.medium { background: #4b361c; color: #ffc46b; border: 1px solid #795722; }
        .badge.low { background: #4a431c; color: #ffe46b; border: 1px solid #756b24; }
        .badge.info { background: #1c3654; color: #7fc1ff; border: 1px solid #315b84; }
        .risk-item { background: #101827; border: 1px solid #27324a; border-left: 4px solid #ff5c5c; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
        .risk-item-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
        .risk-page { color: #7fc1ff; font-family: "Consolas", monospace; font-size: 12px; margin-bottom: 4px; }
        .risk-msg { color: #cbd3dd; font-size: 13px; }
        ul.recs-list { padding-left: 20px; }
        ul.recs-list li { color: #cbd3dd; margin-bottom: 10px; }
        ul.recs-list li::marker { color: #62b0ff; }
        .action-bar { display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
        .action-btn {
            background: #101827;
            color: #cbd3dd;
            border: 1px solid #27324a;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .action-btn:hover { background: #1c3654; color: #7fc1ff; border-color: #62b0ff; }
        footer { margin-top: 40px; text-align: center; color: #556275; font-size: 12px; }
    </style>
</head>
<body>
<div class="container">
    <div class="hero-card">
        <div class="brand-header">
            <h1 class="brand-title">🛡️ WEB-AUDITOR</h1>
            <span class="brand-badge">Autonomous Web Security Engine</span>
        </div>
        <p class="hero-subtitle">
            Enter any website URL to autonomously discover pages, audit DOM security, check HTTP headers & storage leaks, and generate executive vulnerability reports.
        </p>
        <div class="input-group">
            <input
                type="text"
                id="targetUrl"
                class="url-input"
                placeholder="http://127.0.0.1:5500/website/index.html or https://..."
                value="http://127.0.0.1:5500/website/index.html"
            >
            <button id="scanBtn" class="scan-btn" onclick="startAudit()">
                <span>🚀</span> Start Security Audit
            </button>
        </div>
        <div class="options-row">
            <div class="presets">
                <span class="preset-label">Quick Presets:</span>
                <span class="preset-chip" onclick="setTarget('http://127.0.0.1:5500/website/index.html')">🛒 ShopDemo</span>
                <span class="preset-chip" onclick="setTarget('http://127.0.0.1:3000')">🍹 Juice Shop</span>
                <span class="preset-chip" onclick="setTarget('https://example.com')">🌐 Example.com</span>
            </div>
            <label class="toggle-label">
                <input type="checkbox" id="autoDiscover" checked>
                <span>🔎 Auto-Discover All Pages (Deep Crawler)</span>
            </label>
        </div>
    </div>

    <div id="statusCard" class="status-card">
        <div class="status-header">
            <div class="spinner"></div>
            <div id="statusTitle" class="status-title">AI Agent Initializing...</div>
        </div>
        <div id="statusLog" class="status-log">Connecting to WebCMD browser runtime and preparing target URL...</div>
    </div>

    <div id="resultsSection">
        <div class="cards">
            <div class="card">
                <h3>Risk Score</h3>
                <div class="value" id="cardRiskScore">0<span class="score-total">/100</span></div>
                <div class="risk-bar">
                    <div id="cardRiskFill" class="risk-fill" style="width: 0%"></div>
                </div>
                <span id="cardRiskLevel" class="risk-label safe">SAFE</span>
            </div>
            <div class="card">
                <h3>Pages Scanned</h3>
                <div class="value" id="cardPages">0</div>
            </div>
            <div class="card">
                <h3>Total Findings</h3>
                <div class="value" id="cardTotal">0</div>
            </div>
            <div class="card high-card">
                <h3>High</h3>
                <div class="value" id="cardHigh">0</div>
            </div>
            <div class="card medium-card">
                <h3>Medium</h3>
                <div class="value" id="cardMedium">0</div>
            </div>
            <div class="card low-card">
                <h3>Low</h3>
                <div class="value" id="cardLow">0</div>
            </div>
            <div class="card info-card">
                <h3>Info</h3>
                <div class="value" id="cardInfo">0</div>
            </div>
        </div>

        <div class="section-box">
            <h2>⚙️ Scan Information</h2>
            <div class="method-grid">
                <div class="method-item">
                    <span class="method-label">🎯 Target URL</span>
                    <strong id="infoTargetUrl" style="word-break: break-all; font-family: monospace;">-</strong>
                </div>
                <div class="method-item">
                    <span class="method-label">🤖 AI Agent</span>
                    <strong>Gemini</strong>
                </div>
                <div class="method-item">
                    <span class="method-label">🌐 Browser Runtime</span>
                    <strong>Playwright + WebCMD</strong>
                </div>
                <div class="method-item">
                    <span class="method-label">🛡️ Audit Type</span>
                    <strong>Passive & Interactive Security Scan</strong>
                </div>
            </div>
        </div>

        <div class="section-box">
            <h2>📋 Executive Summary</h2>
            <p id="execSummaryText" style="color: #cbd3dd; font-size: 14px; line-height: 1.7;">-</p>
        </div>

        <div class="section-box">
            <h2>🚨 Top Security Risks</h2>
            <div id="topRisksList"></div>
        </div>

        <div class="section-box">
            <h2>🔍 Detailed Security Findings</h2>
            <div class="table-controls">
                <input
                    type="text"
                    id="searchFindings"
                    class="search-box"
                    placeholder="Search findings (XSS, headers, password, url...)"
                    oninput="filterTable()"
                >
                <div class="filters">
                    <button class="filter-btn active" onclick="setSeverityFilter('ALL', this)">All</button>
                    <button class="filter-btn" onclick="setSeverityFilter('HIGH', this)">High</button>
                    <button class="filter-btn" onclick="setSeverityFilter('MEDIUM', this)">Medium</button>
                    <button class="filter-btn" onclick="setSeverityFilter('LOW', this)">Low</button>
                    <button class="filter-btn" onclick="setSeverityFilter('INFO', this)">Info</button>
                </div>
            </div>
            <div class="table-wrapper">
                <table id="findingsTable">
                    <thead>
                        <tr>
                            <th style="width: 100px;">Severity</th>
                            <th style="width: 160px;">Type</th>
                            <th>Page</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody id="findingsTableBody"></tbody>
                </table>
            </div>
        </div>

        <div class="section-box">
            <h2>💡 Remediation Recommendations</h2>
            <ul id="recsList" class="recs-list"></ul>
        </div>

        <div class="action-bar">
            <a href="/api/report/html" target="_blank" class="action-btn">
                <span>📄</span> Open Standalone Report
            </a>
            <a href="/api/report" target="_blank" class="action-btn">
                <span>📊</span> View Raw Security JSON
            </a>
            <a href="/api/risk" target="_blank" class="action-btn">
                <span>🧠</span> View Risk Analysis JSON
            </a>
            <button class="action-btn" onclick="cleanupWebcmdSessions()">
                <span>🧹</span> Cleanup WebCMD Sessions
            </button>
        </div>
    </div>

    <footer>
        🛡️ WEB-AUDITOR &bull; Autonomous Security Intelligence Engine &bull; Powered by Gemini & WebCMD
    </footer>
</div>

<script>
    let allFindings = [];
    let currentSeverityFilter = 'ALL';

    function setTarget(url) {
        document.getElementById('targetUrl').value = url;
    }

    async function startAudit() {
        const url = document.getElementById('targetUrl').value.trim();
        const autoDiscover = document.getElementById('autoDiscover').checked;

        if (!url) {
            alert('Please enter a valid website URL.');
            return;
        }

        const scanBtn = document.getElementById('scanBtn');
        const statusCard = document.getElementById('statusCard');
        const statusTitle = document.getElementById('statusTitle');
        const statusLog = document.getElementById('statusLog');
        const resultsSection = document.getElementById('resultsSection');

        scanBtn.disabled = true;
        scanBtn.innerHTML = '<span>⏳</span> Auditing...';
        statusCard.style.display = 'block';

        const steps = [
            "🌐 Initializing WebCMD browser session and connecting to target...",
            "🤖 Gemini Agent analyzing page structure and DOM links...",
            "🔎 Scanning forms, password inputs, and script event handlers...",
            "🛡️ Auditing HTTP response headers, Web Storage, and cookie flags...",
            "📊 Calculating risk scores and generating recommendations..."
        ];

        let stepIndex = 0;
        statusTitle.innerText = "Audit in Progress...";
        statusLog.innerText = steps[0];

        const interval = setInterval(() => {
            stepIndex = (stepIndex + 1) % steps.length;
            statusLog.innerText = steps[stepIndex];
        }, 3000);

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    auto_discover: autoDiscover,
                    background: false
                })
            });

            clearInterval(interval);

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Scan failed');
            }

            const data = await response.json();
            statusTitle.innerText = "✅ Audit Completed Successfully!";
            statusLog.innerText = `Scan finished for ${url}. Audited ${data.result.pages_scanned} pages with ${data.result.total_findings} findings.`;

            await loadAuditResults();

            setTimeout(() => {
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }, 300);

        } catch (error) {
            clearInterval(interval);
            statusTitle.innerText = "❌ Scan Error";
            statusLog.innerText = "Failed to complete audit: " + error.message;
        } finally {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<span>🚀</span> Start Security Audit';
        }
    }

    async function loadAuditResults() {
        try {
            const [reportRes, riskRes] = await Promise.all([
                fetch('/api/report'),
                fetch('/api/risk')
            ]);

            if (!reportRes.ok || !riskRes.ok) return;

            const report = await reportRes.json();
            const risk = await riskRes.json();

            document.getElementById('resultsSection').style.display = 'block';

            const score = risk.risk_score || 0;
            const level = (risk.risk_level || 'SAFE').toUpperCase();
            document.getElementById('cardRiskScore').innerHTML = `${score}<span class="score-total">/100</span>`;
            document.getElementById('cardRiskFill').style.width = `${score}%`;

            const levelBadge = document.getElementById('cardRiskLevel');
            levelBadge.innerText = level;
            levelBadge.className = `risk-label ${level.toLowerCase()}`;

            document.getElementById('cardPages').innerText = report.pages_scanned || 0;
            document.getElementById('cardTotal').innerText = report.total_findings || 0;

            const summary = report.severity_summary || {};
            document.getElementById('cardHigh').innerText = summary.HIGH || 0;
            document.getElementById('cardMedium').innerText = summary.MEDIUM || 0;
            document.getElementById('cardLow').innerText = summary.LOW || 0;
            document.getElementById('cardInfo').innerText = summary.INFO || 0;

            document.getElementById('infoTargetUrl').innerText = report.base_url || document.getElementById('targetUrl').value;
            document.getElementById('execSummaryText').innerText = risk.executive_summary || 'No summary available.';

            const topRisksContainer = document.getElementById('topRisksList');
            topRisksContainer.innerHTML = '';
            const topRisks = risk.top_risks || [];

            if (topRisks.length === 0) {
                topRisksContainer.innerHTML = '<p style="color: #7fe48d;">✅ No high-priority risks detected.</p>';
            } else {
                topRisks.forEach(item => {
                    const sev = (item.severity || 'INFO').toLowerCase();
                    const el = document.createElement('div');
                    el.className = 'risk-item';
                    el.innerHTML = `
                        <div class="risk-item-header">
                            <span class="badge ${sev}">${item.severity}</span>
                            <strong>${item.type}</strong>
                        </div>
                        <div class="risk-page">Page: ${item.page || ''}</div>
                        <div class="risk-msg">${item.message || ''}</div>
                    `;
                    topRisksContainer.appendChild(el);
                });
            }

            const recsContainer = document.getElementById('recsList');
            recsContainer.innerHTML = '';
            const recs = risk.recommendations || [];
            if (recs.length === 0) {
                recsContainer.innerHTML = '<li>✅ No immediate remediation required.</li>';
            } else {
                recs.forEach(rec => {
                    const li = document.createElement('li');
                    li.innerText = rec;
                    recsContainer.appendChild(li);
                });
            }

            allFindings = report.findings || [];
            renderFindingsTable(allFindings);

        } catch (e) {
            console.error("Failed to load audit results:", e);
        }
    }

    function renderFindingsTable(findings) {
        const tbody = document.getElementById('findingsTableBody');
        tbody.innerHTML = '';

        if (findings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #687587; padding: 20px;">No findings matched the criteria.</td></tr>';
            return;
        }

        findings.forEach(f => {
            const tr = document.createElement('tr');
            const sev = (f.severity || 'INFO').toLowerCase();
            tr.innerHTML = `
                <td><span class="badge ${sev}">${f.severity || 'INFO'}</span></td>
                <td><strong>${f.type || 'UNKNOWN'}</strong></td>
                <td style="font-family: monospace; font-size: 12px; color: #7fc1ff; word-break: break-all;">${f.page || ''}</td>
                <td>${f.message || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function setSeverityFilter(severity, btn) {
        currentSeverityFilter = severity;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filterTable();
    }

    function filterTable() {
        const search = document.getElementById('searchFindings').value.toLowerCase().trim();

        const filtered = allFindings.filter(f => {
            const sev = (f.severity || 'INFO').toUpperCase();
            const matchesSeverity = (currentSeverityFilter === 'ALL' || sev === currentSeverityFilter);

            const text = `${f.type} ${f.page} ${f.message} ${f.severity}`.toLowerCase();
            const matchesSearch = !search || text.includes(search);

            return matchesSeverity && matchesSearch;
        });

        renderFindingsTable(filtered);
    }

    async function cleanupWebcmdSessions() {
        try {
            const res = await fetch('/api/sessions/cleanup', { method: 'POST' });
            const data = await res.json();
            alert(`🧹 Cleaned up ${data.closed_sessions} idle WebCMD sessions.`);
        } catch (e) {
            alert('Failed to cleanup sessions: ' + e.message);
        }
    }

    window.addEventListener('DOMContentLoaded', () => {
        loadAuditResults();
    });
</script>
</body>
</html>
"""


# ============================================================
# ROOT & HEALTH CHECK
# ============================================================

@app.get("/", response_class=HTMLResponse)
def home():
    """Serves the interactive WEB-AUDITOR frontend portal."""
    return HTMLResponse(content=PORTAL_HTML)


@app.get("/api")
def api_info():
    """Returns REST API endpoints and metadata."""
    return {
        "service": "WEB-AUDITOR API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "web_portal": "GET /",
            "health": "GET /api/health",
            "report_json": "GET /api/report",
            "report_html": "GET /api/report/html",
            "risk_analysis": "GET /api/risk",
            "workflow_memory": "GET /api/workflows",
            "webcmd_sessions": "GET /api/sessions",
            "trigger_scan": "POST /api/scan"
        }
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "scan_state": scan_status["state"]
    }


# ============================================================
# AUDIT REPORTS & DASHBOARD
# ============================================================

@app.get("/api/report")
def get_report():
    """Returns the latest JSON security scan report."""
    report_path = AGENT_DIR / "security_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="No security report found. Run a scan first.")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/risk")
def get_risk_analysis():
    """Returns the latest risk score, severity breakdown, and AI recommendations."""
    risk_path = AGENT_DIR / "risk_analysis.json"
    if not risk_path.exists():
        raise HTTPException(status_code=404, detail="No risk analysis found. Run a scan first.")
    with open(risk_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/report/html", response_class=HTMLResponse)
def get_html_report():
    """Serves the generated interactive HTML security report dashboard."""
    html_path = AGENT_DIR / "web_audit_report.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="HTML report not found. Run a scan or generate_report first.")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/workflows")
def get_workflows():
    """Returns the learned agent workflow memory."""
    memory_path = AGENT_DIR / "workflow_memory.json"
    if not memory_path.exists():
        return {"workflows": []}
    with open(memory_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# WEBCMD SESSIONS
# ============================================================

@app.get("/api/sessions")
def get_sessions():
    """Lists active and idle WebCMD browser sessions."""
    try:
        return {
            "sessions": list_sessions()
        }
    except Exception as e:
        return {"error": str(e), "sessions": []}


@app.post("/api/sessions/cleanup")
def cleanup_sessions():
    """Closes all idle WebCMD sessions to free memory and browser instances."""
    try:
        count = cleanup_idle_sessions()
        return {"status": "success", "closed_sessions": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TRIGGER SECURITY AUDIT
# ============================================================

def run_full_scan_pipeline(url: str, auto_discover: bool = False):
    """Executes the full auditing, risk analysis, and HTML report generation pipeline."""
    from playwright.sync_api import sync_playwright
    from datetime import datetime

    global scan_status
    scan_status["state"] = "running"
    scan_status["last_url"] = url
    scan_status["error"] = None

    try:
        pages_to_scan = [url]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            if auto_discover:
                from explorer import explore_website
                try:
                    pages_to_scan = explore_website(page, start_url=url)
                except Exception as e:
                    print(f"⚠️ Page discovery fallback: {e}")
                    pages_to_scan = [url]

            # Run Security Scan
            audit_report = scan_website(browser, url, pages_to_scan)
            browser.close()

        # Save security report
        sec_report_file = AGENT_DIR / "security_report.json"
        with open(sec_report_file, "w", encoding="utf-8") as f:
            json.dump(audit_report, f, indent=2, ensure_ascii=False)

        # Run Risk Analysis
        analysis = analyze_report(audit_report)
        risk_file = AGENT_DIR / "risk_analysis.json"
        with open(risk_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        # Generate HTML Report
        generate_report()

        scan_status["state"] = "completed"
        scan_status["last_scan_time"] = datetime.now().isoformat()
        return {
            "status": "completed",
            "pages_scanned": audit_report["pages_scanned"],
            "total_findings": audit_report["total_findings"],
            "risk_score": analysis["risk_score"],
            "risk_level": analysis["risk_level"]
        }

    except Exception as error:
        scan_status["state"] = "failed"
        scan_status["error"] = str(error)
        raise error


@app.post("/api/scan")
def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Triggers an automated security scan for the provided target URL.
    Can be run in background or synchronously.
    """
    if request.background:
        background_tasks.add_task(run_full_scan_pipeline, request.url, request.auto_discover)
        return {
            "message": "Scan initiated in background",
            "url": request.url,
            "status": "running"
        }

    try:
        result = run_full_scan_pipeline(request.url, request.auto_discover)
        return {
            "message": "Scan completed successfully",
            "url": request.url,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting WEB-AUDITOR Backend on http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
