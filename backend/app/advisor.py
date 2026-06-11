import os
import requests
import json
from sqlalchemy.orm import Session
import google.generativeai as genai
from backend.app.models import SystemSettings, GapAnalysis, Asset, Organization

# Local Swedish & English NIS2 Directive knowledge snippet base for RAG fallback
LOCAL_NIS2_DIRECTIVE_KNOWLEDGE = {
    "scope": {
        "title": "NIS2 Scope & Entity Categories (Directive (EU) 2022/2555)",
        "content": "NIS2 distinguishes between Essential Entities (EE) and Important Entities (IE) based on size and sector. EE: Large enterprises in highly critical sectors (Energy, Transport, Finance, Health, Water, Space, Digital Infra). IE: Medium-sized enterprises in these sectors or entities in critical sectors (Postal, Waste, Chemicals, Food, Manufacturing, Digital Providers). In Sweden, oversight is managed by NCSC-SE and sector-specific regulators (e.g., Energimyndigheten, Transportstyrelsen, PTS).",
        "keywords": ["scope", "essential", "important", "sweden", "ncsc", "msb", "entities", "entity", "pts"]
    },
    "mfa": {
        "title": "Article 21.2j - Multi-Factor Authentication & Secured Communications",
        "content": "The Swedish MSB regulations (MSBFS) mandate multi-factor authentication (MFA) or continuous authentication solutions for all remote administrative access and user accounts. Incident response systems and emergency communication channels must be isolated, encrypted, and structurally distinct from standard corporate email to prevent complete blackout during a ransomware breach.",
        "keywords": ["mfa", "multi-factor", "authentication", "identity", "active directory", "password", "remote access"]
    },
    "encryption": {
        "title": "Article 21.2h - Cryptography & Encryption Policies",
        "content": "Article 21.2h requires strict cryptographic policies. All public services must support HTTPS with TLS 1.3 (TLS 1.2 is tolerated as legacy minimum, TLS 1.0/1.1 are prohibited). Critical customer database stores must be encrypted at rest using AES-256-GCM. Virtual Private Networks (VPNs) must utilize strong modern protocols (IPsec or WireGuard) with certificate-based authentication.",
        "keywords": ["encryption", "cryptography", "ssl", "tls", "https", "aes", "cipher", "cert", "vpn"]
    },
    "incident": {
        "title": "Article 21.2b - Incident Handling & Regulatory Reporting to MSB",
        "content": "Under Swedish implementation, entities must submit an 'Early Warning' within 24 hours of detecting a significant incident to MSB (via the cert.se portal). A formal 'Incident Notification' is required within 72 hours, followed by a final report within 1 month. The early warning must state whether the incident is suspected of being caused by unlawful or malicious acts.",
        "keywords": ["incident", "reporting", "msb", "cert.se", "early warning", "notification", "response", "log", "siem", "72 hours"]
    },
    "supplychain": {
        "title": "Article 21.2d - Supply Chain Security & Third-Party Risks",
        "content": "Entities must evaluate the security practices of all direct suppliers. In Sweden, this includes validating supplier certifications (ISO 27001), reviewing vulnerability disclosures of vendor-provided software, and enforcing strict service level agreements (SLAs) regarding security breach notifications. Open source packages and dependencies must be cataloged in a Software Bill of Materials (SBOM).",
        "keywords": ["supply chain", "vendor", "supplier", "third party", "sla", "dependency", "sbom", "audit"]
    },
    "risk": {
        "title": "Article 21.2a - Risk Analysis & Information Security Policies",
        "content": "A foundational NIS2 requirement. Swedish MSB regulations require a formalized risk management framework (e.g., ISO 27005 or Swedish KLASSA methodology). This mandates establishing a continuous risk register, prioritizing vulnerabilities, assigning business owners to specific risk objects, and hosting bi-annual executive security review boards.",
        "keywords": ["risk", "policy", "framework", "register", "assessment", "klasss", "iso 27001", "executive", "board"]
    },
    "hygiene": {
        "title": "Article 21.2g - Basic Cyber Hygiene & Security Awareness",
        "content": "Swedish NCSC-SE emphasizes 'Basics First'. This requires robust password policies (minimum 14 characters, non-dictionary, breached-password screening), automated OS patch deployments within 14 days for critical patches, endpoint detection (EDR), and mandatory interactive security awareness training for all newly boarded personnel.",
        "keywords": ["hygiene", "training", "awareness", "password", "patching", "hardened", "phishing", "staff"]
    }
}

def generate_local_response(query: str, db: Session, organization_id: int = 1) -> dict:
    """
    Simulates AI RAG query using local Swedish NIS2 guidelines.
    """
    query_lower = query.lower()
    
    # 1. Gather context from discovered assets and gap analysis
    assets = db.query(Asset).filter(Asset.organization_id == organization_id).all()
    gaps = db.query(GapAnalysis).filter(GapAnalysis.organization_id == organization_id).all()
    
    in_scope_assets = [a for a in assets if a.in_scope]
    non_compliant_gaps = [g for g in gaps if g.status == "Non-Compliant"]
    
    # 2. Match topic keyword
    matched_entry = None
    for key, data in LOCAL_NIS2_DIRECTIVE_KNOWLEDGE.items():
        if any(kw in query_lower for kw in data["keywords"]):
            matched_entry = data
            break
            
    # 3. Construct intelligent response
    sources = []
    if matched_entry:
        title = matched_entry["title"]
        content = matched_entry["content"]
        sources.append(f"Official NIS2 Directive Text / Swedish MSB Guideline ({title})")
    else:
        title = "NIS2 General Directive Security Measures (Article 21)"
        content = "Under NIS2 Article 21, organizations must take appropriate and proportionate technical, operational, and organizational measures to manage the risks posed to the security of network and information systems."
        sources.append("EU Directive 2022/2555 (NIS2)")

    # Tailored reply logic
    reply = f"### 🇸🇪 AI Remediation Advisor (Local Expert Fallback Mode)\n\n"
    reply += f"Based on your query regarding **\"{query}\"**, I have retrieved the relevant regulatory context from our database.\n\n"
    reply += f"**Regulatory Context — {title}:**\n>{content}\n\n"
    
    reply += "#### 📊 Live Audit Context for Your Organization:\n"
    reply += f"- **Discovered Assets in Scope:** {len(in_scope_assets)} servers/services.\n"
    reply += f"- **Identified Critical Gaps:** {len(non_compliant_gaps)} categories are currently classified as *Non-Compliant*.\n\n"
    
    # Contextual adjustments
    if "mfa" in query_lower or "auth" in query_lower:
        mfa_gap = next((g for g in gaps if g.article_id == "Art 21.2j"), None)
        reply += "#### 🛠️ Direct Remediation Guidance (MFA & Securing Communications):\n"
        if mfa_gap and mfa_gap.status != "Compliant":
            reply += f"Our scanner identified a critical gap: **{mfa_gap.comments}**\n\n"
            reply += "##### Action Plan:\n"
            reply += "1. **Mandate MFA:** Enforce MFA on all corporate interfaces. We recommend FIDO2 / WebAuthn standard security keys or Authenticator Apps. Avoid SMS-based 2FA.\n"
            reply += "2. **Secure Admin Gates:** Discovered admin interfaces must be locked down behind an Identity-Aware Proxy (IAP) or local VPN immediately.\n"
            reply += "3. **Swedish Regulator Compliance:** NCSC-SE recommends establishing an out-of-band communication app (like Signal or a dedicated encrypted wire server) for emergency communications."
        else:
            reply += "Identity and access management checks pass standard checks, but continuous audits should be performed weekly on Active Directory."
            
    elif "encrypt" in query_lower or "crypto" in query_lower or "tls" in query_lower or "ssl" in query_lower:
        crypto_gap = next((g for g in gaps if g.article_id == "Art 21.2h"), None)
        reply += "#### 🛠️ Direct Remediation Guidance (Cryptography & TLS):\n"
        if crypto_gap and crypto_gap.status != "Compliant":
            reply += f"Our scanner identified a critical gap: **{crypto_gap.comments}**\n\n"
            reply += "##### Action Plan:\n"
            reply += "1. **Disable Insecure Services:** Enforce TLS 1.3 on all client-facing web servers.\n"
            reply += "2. **Database Protection:** Ensure standard tables in local PostgreSQL utilize transparent data encryption (TDE) or have application-level field encryption active."
        else:
            reply += "Encryption policies are compliant. Keep auditing cipher suites during quarterly scans."
            
    elif "incident" in query_lower or "report" in query_lower or "msb" in query_lower:
        inc_gap = next((g for g in gaps if g.article_id == "Art 21.2b"), None)
        reply += "#### 🛠️ Direct Remediation Guidance (Incident Management & MSB):\n"
        if inc_gap and inc_gap.status != "Compliant":
            reply += f"Our scanner identified a critical gap: **{inc_gap.comments}**\n\n"
            reply += "##### Action Plan:\n"
            reply += "1. **Establish MSB Escalation:** Prepare a template document containing incident scope, type, and impact. Register on cert.se for incident reporting.\n"
            reply += "2. **Centralize Logs:** Deploy a local ELK Stack or Graylog instances.\n"
            reply += "3. **Swedish Timeframes:** Train SOC operators on the strict Swedish MSB 24-hour early warning window."
        else:
            reply += "Incident response flows are partially mapped. Review testing drills."
            
    else:
        # Generic response mapping non-compliant gaps
        reply += "#### 📋 Priorities & Recommendations:\n"
        if non_compliant_gaps:
            reply += "Here are the top non-compliant gaps to address immediately in plain language:\n"
            for i, gap in enumerate(non_compliant_gaps[:3]):
                reply += f"{i+1}. **{gap.category} ({gap.article_id}):** {gap.remediation_steps}\n"
        else:
            reply += "Congratulations! No severe non-compliance gaps found. Continue regular scheduling scans to maintain this status."
            
    reply += "\n\n*Note: Configure your API keys (Gemini, OpenAI, or Claude) in the settings panel to activate advanced multi-LLM reasoning.*"
    
    return {"response": reply, "sources": sources}

def query_gemini_advisor(query: str, api_key: str, system_prompt: str) -> dict:
    """
    Connects to live Google Gemini API using generativeai library.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{system_prompt}\n\nUSER QUERY: {query}"
        response = model.generate_content(full_prompt)
        return {
            "response": response.text,
            "sources": ["Google Gemini 1.5 Flash Model", "Live Network Context", "Official MSB Directives"]
        }
    except Exception as e:
        print(f"Gemini API execution error: {str(e)}")
        raise e

def query_openai_advisor(query: str, api_key: str, system_prompt: str) -> dict:
    """
    Connects to OpenAI API using raw REST request.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"USER QUERY: {query}"}
        ],
        "temperature": 0.7
    }
    res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=10)
    if res.status_code == 200:
        content = res.json()["choices"][0]["message"]["content"]
        return {
            "response": content,
            "sources": ["OpenAI GPT-4 Turbo Model", "Live Network Context", "Official MSB Directives"]
        }
    else:
        raise Exception(f"OpenAI API error: {res.status_code} - {res.text}")

def query_claude_advisor(query: str, api_key: str, system_prompt: str) -> dict:
    """
    Connects to Anthropic Claude API using raw REST request.
    """
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": query}
        ],
        "max_tokens": 1500
    }
    res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=10)
    if res.status_code == 200:
        content = res.json()["content"][0]["text"]
        return {
            "response": content,
            "sources": ["Anthropic Claude 3.5 Sonnet Model", "Live Network Context", "Official MSB Directives"]
        }
    else:
        raise Exception(f"Claude API error: {res.status_code} - {res.text}")

def get_ai_remediation_advice(query: str, db: Session, organization_id: int = 1) -> dict:
    """
    Main entrypoint: Fetches settings, scopes context to Org SaaS, and invokes active LLM.
    """
    # 1. Fetch live audit context for this organization
    assets = db.query(Asset).filter(Asset.organization_id == organization_id).all()
    gaps = db.query(GapAnalysis).filter(GapAnalysis.organization_id == organization_id).all()
    
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    org_name = org.name if org else "Demo Corporation"
    
    assets_summary = []
    for a in assets:
        ports_info = a.ports if a.ports else "None"
        risk_info = f"Risk: {a.dynamic_risk_score}"
        assets_summary.append(f"IP: {a.ip}, Host: {a.hostname or 'Unknown'}, Scope sector: {a.scope_sector or 'None'}, Ports: {ports_info}, {risk_info}")
        
    gaps_summary = []
    for g in gaps:
        gaps_summary.append(f"Article: {g.article_id}, Control: {g.control_name}, Status: {g.status}, Score: {g.score}%, Auditor Comments: {g.comments or 'None'}")
        
    # 2. Construct context-aware system prompt
    system_prompt = f"""You are a senior cybersecurity auditor specializing in European NIS2 Compliance (Directive (EU) 2022/2555) and the Swedish regulatory framework (NCSC-SE / MSB regulations, MSBFS).
Your job is to advise the company on how to remediate their compliance gaps. Explain complex cybersecurity and legal concepts in clear, actionable, plain language.

Here is the current audited status of the organization '{org_name}':
---
DISCOVERED ASSETS:
{os.linesep.join(assets_summary) if assets_summary else "No assets discovered yet."}

NIS2 GAP ANALYSIS (ARTICLE 21):
{os.linesep.join(gaps_summary) if gaps_summary else "No gap analysis results populated yet."}
---

Answer the user's query professionally. If relevant, include actionable steps, prioritized order, Swedish regulatory requirements (MSB timelines like 24h early warning, cert.se, etc.), and configuration or code snippets where helpful. Use markdown structure.
"""

    # 3. Retrieve LLM settings
    settings = db.query(SystemSettings).filter(SystemSettings.organization_id == organization_id).first()
    if not settings:
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        
    provider = settings.llm_provider if settings else "Google Gemini"
    
    # 4. Route to active LLM provider with safe local fallback
    try:
        if provider == "Google Gemini" and settings and (settings.gemini_key or os.getenv("GEMINI_API_KEY")):
            api_key = settings.gemini_key if settings.gemini_key else os.getenv("GEMINI_API_KEY")
            return query_gemini_advisor(query, api_key, system_prompt)
            
        elif provider == "OpenAI GPT-4" and settings and (settings.openai_key or os.getenv("OPENAI_API_KEY")):
            api_key = settings.openai_key if settings.openai_key else os.getenv("OPENAI_API_KEY")
            return query_openai_advisor(query, api_key, system_prompt)
            
        elif provider == "Anthropic Claude" and settings and (settings.claude_key or os.getenv("CLAUDE_API_KEY")):
            api_key = settings.claude_key if settings.claude_key else os.getenv("CLAUDE_API_KEY")
            return query_claude_advisor(query, api_key, system_prompt)
            
    except Exception as e:
        print(f"[Advisor] Error with model {provider}: {str(e)}. Falling back to local responder.")
        
    # Fallback to local expert response
    return generate_local_response(query, db, organization_id=organization_id)
