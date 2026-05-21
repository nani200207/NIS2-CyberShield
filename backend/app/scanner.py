import time
import socket
import json
import random
import threading
from datetime import datetime
from sqlalchemy.orm import Session
import requests

from backend.app.models import Asset, ScanLog, SystemSettings
from backend.app.gap_analysis import evaluate_all_rules  # we will implement this next

def log_scan(db: Session, message: str, level: str = "INFO"):
    log = ScanLog(timestamp=datetime.utcnow(), level=level, message=message)
    db.add(log)
    db.commit()
    print(f"[{level}] {message}")

def simulate_scan(db: Session, target: str, settings: SystemSettings):
    """
    High-fidelity simulation of Nmap scan + Shodan query.
    Logs step-by-step progress and inserts assets.
    """
    log_scan(db, f"Initializing NIS2 CyberShield Discovery Engine...", "INFO")
    time.sleep(1)
    
    log_scan(db, f"Scanning target network range: {target} (Simulated Nmap Engine v7.92)", "INFO")
    time.sleep(1)
    
    # Step 1: Ping scan & Host discovery
    log_scan(db, "Phase 1: Running ICMP Host Discovery & ARP sweep...", "INFO")
    time.sleep(1.5)
    log_scan(db, "Discovered 5 active hosts on the subnet. Initiating deep port scan & OS finger-printing...", "SUCCESS")
    time.sleep(1)
    
    # Predefined authentic assets representing a typical company environment under NIS2
    simulated_assets = [
        {
            "ip": "10.100.4.10",
            "hostname": "ad-domain-controller.vasteras-group.local",
            "ports": "53,88,135,389,445,3389",
            "os": "Windows Server 2019",
            "services": json.dumps([
                {"port": 53, "service": "domain", "version": "Microsoft DNS v6.1"},
                {"port": 88, "service": "kerberos", "version": "Active Directory Kerberos"},
                {"port": 389, "service": "ldap", "version": "Microsoft LDAP v3"},
                {"port": 445, "service": "microsoft-ds", "version": "Windows SMBv2/SMBv3"}
            ]),
            "in_scope": True,
            "scope_sector": "ICT Management",
            "criticality": "Critical",
            "shodan_data": None
        },
        {
            "ip": "10.100.4.45",
            "hostname": "kratos-api-gateway.prod.stockholm.se",
            "ports": "80,443,8080,9090",
            "os": "Linux / Ubuntu 22.04 LTS",
            "services": json.dumps([
                {"port": 80, "service": "http", "version": "nginx 1.22.1"},
                {"port": 443, "service": "https", "version": "nginx 1.22.1 (SSL/TLS v1.3)"},
                {"port": 8080, "service": "http-proxy", "version": "Envoy Proxy v1.26"}
            ]),
            "in_scope": True,
            "scope_sector": "Digital Infrastructure",
            "criticality": "High",
            "shodan_data": None
        },
        {
            "ip": "10.100.4.78",
            "hostname": "siemens-s7-scada.hmi.vasteras.ot",
            "ports": "102,502",
            "os": "Embedded RTOS / Siemens Ruggedcom",
            "services": json.dumps([
                {"port": 102, "service": "iso-tsap", "version": "Siemens S7 Protocol"},
                {"port": 502, "service": "modbus", "version": "Modbus TCP Server"}
            ]),
            "in_scope": True,
            "scope_sector": "Energy",
            "criticality": "Critical",
            "shodan_data": None
        },
        {
            "ip": "10.100.4.112",
            "hostname": "ehr-portal.gothenburg-clinic.health",
            "ports": "443,8443",
            "os": "Linux / RedHat Enterprise Linux 8",
            "services": json.dumps([
                {"port": 443, "service": "https", "version": "Apache httpd 2.4.41 (OpenSSL 1.1.1)"},
                {"port": 8443, "service": "https-alt", "version": "Tomcat Web Application Manager"}
            ]),
            "in_scope": True,
            "scope_sector": "Health",
            "criticality": "High",
            "shodan_data": None
        },
        {
            "ip": "185.190.140.22",
            "hostname": "exposed-elastic-dashboard.vasteras.se",
            "ports": "9200,5601",
            "os": "Linux / Docker Container",
            "services": json.dumps([
                {"port": 9200, "service": "elasticsearch", "version": "Elasticsearch v7.17.0 (No auth)"},
                {"port": 5601, "service": "kibana", "version": "Kibana Dashboard v7.17.0"}
            ]),
            "in_scope": True,
            "scope_sector": "Digital Infrastructure",
            "criticality": "High",
            "shodan_data": json.dumps({
                "shodan_vulns": ["CVE-2021-44228", "CVE-2022-33980"],
                "org": "Vasteras Energy and Digital Systems",
                "isp": "Telia Sweden AB",
                "exposed_services": ["Elasticsearch REST API", "Kibana Panel"],
                "warning": "CRITICAL EXPOSURE: Database is publicly indexable without authentication."
            })
        }
    ]

    # Port scanning simulation
    for asset in simulated_assets:
        log_scan(db, f"Port-scanning host: {asset['ip']} ({asset['hostname'] or 'Unknown'})", "INFO")
        time.sleep(0.8)
        log_scan(db, f"Discovered open ports on {asset['ip']}: [{asset['ports']}]", "SUCCESS")
        
        # Simulated Shodan API call
        if settings.shodan_key:
            log_scan(db, f"Querying Shodan API for external threat footprint on {asset['ip']}...", "INFO")
            time.sleep(0.5)
            if asset["shodan_data"]:
                log_scan(db, f"Shodan WARNING: Vulnerable exposure detected for {asset['ip']}", "WARNING")
            else:
                log_scan(db, f"Shodan reports no public indicators for {asset['ip']}", "SUCCESS")
        
        # Save or update asset in Database
        existing = db.query(Asset).filter(Asset.ip == asset["ip"]).first()
        if existing:
            existing.hostname = asset["hostname"]
            existing.ports = asset["ports"]
            existing.os = asset["os"]
            existing.services = asset["services"]
            existing.shodan_data = asset["shodan_data"]
            existing.in_scope = asset["in_scope"]
            existing.scope_sector = asset["scope_sector"]
            existing.criticality = asset["criticality"]
            existing.detected_at = datetime.utcnow()
        else:
            new_asset = Asset(
                ip=asset["ip"],
                hostname=asset["hostname"],
                ports=asset["ports"],
                os=asset["os"],
                services=asset["services"],
                shodan_data=asset["shodan_data"],
                in_scope=asset["in_scope"],
                scope_sector=asset["scope_sector"],
                criticality=asset["criticality"],
                detected_at=datetime.utcnow()
            )
            db.add(new_asset)
        db.commit()
        
    time.sleep(1)
    log_scan(db, "Phase 2: Running NIS2 scoping analysis mapping...", "INFO")
    time.sleep(0.8)
    log_scan(db, "Identified 5 critical systems that fall directly under NIS2 Directive scope (essential/important entity requirements).", "WARNING")
    
    time.sleep(0.5)
    log_scan(db, "Initiating Gap Analysis Module calculations...", "INFO")
    # Trigger Gap analysis engine!
    evaluate_all_rules(db)
    
    log_scan(db, "NIS2 Scans and Compliance Gap Analysis completed successfully!", "SUCCESS")

def run_real_scan(db: Session, target: str, settings: SystemSettings):
    """
    Actual socket scan (fast port scanner) for top common administrative/web ports,
    combined with Shodan API queries.
    """
    log_scan(db, f"Initializing REAL Network Discovery Scanner for: {target}", "INFO")
    
    # Extract subnet IP range (naive parser for 192.168.1.1 style or just a single host)
    base_ip = target.split("/")[0]
    parts = base_ip.split(".")
    
    if len(parts) != 4:
        log_scan(db, f"Invalid scan target '{target}'. Falling back to safe simulation scan...", "WARNING")
        simulate_scan(db, target, settings)
        return
        
    log_scan(db, f"Performing light socket port-scan on target: {base_ip}", "INFO")
    common_ports = [21, 22, 23, 25, 53, 80, 443, 445, 3389, 8080]
    
    # Try resolving hostname
    try:
        hostname, _, _ = socket.gethostbyaddr(base_ip)
    except socket.herror:
        hostname = "unknown.local"
        
    open_ports = []
    services_list = []
    
    for port in common_ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        result = s.connect_ex((base_ip, port))
        if result == 0:
            open_ports.append(str(port))
            # Rough service name
            try:
                srv = socket.getservbyport(port)
            except:
                srv = "unknown"
            services_list.append({"port": port, "service": srv, "version": "unknown"})
        s.close()
        
    ports_str = ",".join(open_ports) if open_ports else "None"
    log_scan(db, f"Discovered open ports on {base_ip}: [{ports_str}]", "SUCCESS")
    
    # Shodan scan integration
    shodan_data_str = None
    if settings.shodan_key:
        log_scan(db, f"Querying Shodan API for: {base_ip}", "INFO")
        try:
            url = f"https://api.shodan.io/shodan/host/{base_ip}?key={settings.shodan_key}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                shodan_data_str = res.text
                log_scan(db, f"Shodan query successful for {base_ip}!", "SUCCESS")
            else:
                log_scan(db, f"Shodan API returned status code {res.status_code}", "WARNING")
        except Exception as e:
            log_scan(db, f"Shodan API request failed: {str(e)}", "ERROR")
            
    # Scope detection logic
    # If the user targets a real local machine, let's categorize it based on common open ports
    in_scope = False
    scope_sector = None
    criticality = "Medium"
    
    if "443" in open_ports or "80" in open_ports:
        in_scope = True
        scope_sector = "Digital Infrastructure"
        criticality = "High"
    elif "445" in open_ports or "3389" in open_ports:
        in_scope = True
        scope_sector = "ICT Management"
        criticality = "High"
        
    # Write to database
    existing = db.query(Asset).filter(Asset.ip == base_ip).first()
    if existing:
        existing.hostname = hostname
        existing.ports = ports_str
        existing.services = json.dumps(services_list)
        existing.shodan_data = shodan_data_str
        existing.in_scope = in_scope
        existing.scope_sector = scope_sector
        existing.criticality = criticality
        existing.detected_at = datetime.utcnow()
    else:
        new_asset = Asset(
            ip=base_ip,
            hostname=hostname,
            ports=ports_str,
            services=json.dumps(services_list),
            shodan_data=shodan_data_str,
            in_scope=in_scope,
            scope_sector=scope_sector,
            criticality=criticality,
            detected_at=datetime.utcnow()
        )
        db.add(new_asset)
    db.commit()
    
    # Run gap evaluator
    evaluate_all_rules(db)
    log_scan(db, "Real network discovery and gap calculations finished!", "SUCCESS")

def start_background_scan(db: Session, target: str, real_scan: bool = False):
    """
    Runs scanner in a separate daemon thread to not block FastAPI's response.
    """
    settings = db.query(SystemSettings).first()
    if not settings:
        settings = SystemSettings()
        db.add(settings)
        db.commit()
        
    if real_scan:
        thread = threading.Thread(target=run_real_scan, args=(db, target, settings))
    else:
        thread = threading.Thread(target=simulate_scan, args=(db, target, settings))
        
    thread.daemon = True
    thread.start()
