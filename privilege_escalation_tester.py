#!/usr/bin/env python3
"""
Database Privilege Escalation Testing Suite
Tests for privilege escalation vulnerabilities in database systems
"""

import asyncio
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import json
import re
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class PrivilegeLevel(Enum):
    SUPERUSER = "SUPERUSER"
    ADMIN = "ADMIN"
    PRIVILEGED = "PRIVILEGED"
    USER = "USER"
    GUEST = "GUEST"
    UNKNOWN = "UNKNOWN"

class EscalationTechnique(Enum):
    ROLE_ABUSE = "role_abuse"
    FUNCTION_ABUSE = "function_abuse"
    VULNERABLE_EXTENSION = "vulnerable_extension"
    SQL_INJECTION = "sql_injection"
    CONFIGURATION_WEAKNESS = "configuration_weakness"
    DEFAULT_CREDENTIALS = "default_credentials"
    BACKUP_RESTORE = "backup_restore"
    REPLICATION_ABUSE = "replication_abuse"

@dataclass
class PrivilegeFinding:
    database_type: str
    technique: EscalationTechnique
    current_privilege: PrivilegeLevel
    target_privilege: PrivilegeLevel
    severity: str
    description: str
    evidence: str
    recommendation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

class PrivilegeEscalationTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.findings: List[PrivilegeFinding] = []
        self.logger = self.setup_logging()
        self.connections = {}

    def setup_logging(self):
        """Setup detailed logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileWriter('privilege_escalation_test.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('PrivilegeEscalationTester')

    async def setup_connections(self):
        """Setup database connections for testing"""
        try:
            # MongoDB connection
            if 'mongodb' in self.config:
                mongo_config = self.config['mongodb']
                mongo_client = AsyncIOMotorClient(
                    f"mongodb://{mongo_config.get('host', 'localhost')}:{mongo_config.get('port', 27017)}",
                    username=mongo_config.get('username'),
                    password=mongo_config.get('password'),
                    authSource=mongo_config.get('authDatabase', 'admin')
                )
                await mongo_client.admin.command('ping')
                self.connections['mongodb'] = mongo_client
                self.logger.info("✅ MongoDB connection established")

            # PostgreSQL connection
            if 'postgresql' in self.config:
                pg_config = self.config['postgresql']
                pg_conn = await asyncpg.connect(
                    host=pg_config.get('host', 'localhost'),
                    port=pg_config.get('port', 5432),
                    user=pg_config.get('username'),
                    password=pg_config.get('password'),
                    database=pg_config.get('database', 'postgres')
                )
                self.connections['postgresql'] = pg_conn
                self.logger.info("✅ PostgreSQL connection established")

            # Redis connection
            if 'redis' in self.config:
                redis_config = self.config['redis']
                redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    password=redis_config.get('password'),
                    decode_responses=True
                )
                await redis_client.ping()
                self.connections['redis'] = redis_client
                self.logger.info("✅ Redis connection established")

        except Exception as e:
            self.logger.error(f"❌ Failed to establish database connections: {str(e)}")
            raise

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all privilege escalation tests"""
        self.logger.info("🚀 Starting comprehensive privilege escalation testing...")

        # Test PostgreSQL privilege escalation
        if 'postgresql' in self.connections:
            await self.test_postgresql_privilege_escalation()

        # Test MongoDB privilege escalation
        if 'mongodb' in self.connections:
            await self.test_mongodb_privilege_escalation()

        # Test Redis privilege escalation
        if 'redis' in self.connections:
            await self.test_redis_privilege_escalation()

        # Test cross-database escalation
        await self.test_cross_database_escalation()

        # Generate report
        return await self.generate_report()

    async def test_postgresql_privilege_escalation(self):
        """Test PostgreSQL privilege escalation vulnerabilities"""
        self.logger.info("🔍 Testing PostgreSQL privilege escalation...")

        conn = self.connections['postgresql']

        try:
            # Get current user and privileges
            current_user = await conn.fetchval("SELECT current_user;")
            current_privileges = await self.get_postgresql_privileges(conn)

            self.logger.info(f"Current PostgreSQL user: {current_user}")

            # Test for dangerous built-in functions
            await self.test_postgresql_functions(conn, current_user, current_privileges)

            # Test for role abuse
            await self.test_postgresql_role_abuse(conn, current_user)

            # Test for configuration weaknesses
            await self.test_postgresql_config_weaknesses(conn)

            # Test for extension abuse
            await self.test_postgresql_extensions(conn, current_user)

            # Test for backup/restore abuse
            await self.test_postgresql_backup_escalation(conn, current_user)

        except Exception as e:
            self.logger.error(f"Error testing PostgreSQL privilege escalation: {str(e)}")

    async def get_postgresql_privileges(self, conn) -> Dict[str, bool]:
        """Get PostgreSQL user privileges"""
        privileges = {}

        try:
            # Check superuser status
            privileges['superuser'] = await conn.fetchval(
                "SELECT rolsuper FROM pg_roles WHERE rolname = current_user;"
            )

            # Check role creation rights
            privileges['create_role'] = await conn.fetchval(
                "SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user;"
            )

            # Check database creation rights
            privileges['create_db'] = await conn.fetchval(
                "SELECT rolcreatedb FROM pg_roles WHERE rolname = current_user;"
            )

            # Check login rights
            privileges['can_login'] = await conn.fetchval(
                "SELECT rolcanlogin FROM pg_roles WHERE rolname = current_user;"
            )

            # Check replication rights
            privileges['replication'] = await conn.fetchval(
                "SELECT rolreplication FROM pg_roles WHERE rolname = current_user;"
            )

            # Check bypass RLS
            privileges['bypass_rls'] = await conn.fetchval(
                "SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user;"
            )

        except Exception as e:
            self.logger.debug(f"Error getting PostgreSQL privileges: {str(e)}")

        return privileges

    async def test_postgresql_functions(self, conn, current_user: str, privileges: Dict[str, bool]):
        """Test PostgreSQL built-in functions for privilege escalation"""
        dangerous_functions = [
            ("pg_read_file", "File read access", "CRITICAL"),
            ("pg_ls_dir", "Directory listing", "HIGH"),
            ("copy_to_program", "Command execution", "CRITICAL"),
            ("pg_start_backup", "Backup creation", "HIGH"),
            ("pg_reload_conf", "Config reload", "HIGH"),
            ("pg_rotate_logfile", "Log file access", "MEDIUM"),
        ]

        for func_name, description, severity in dangerous_functions:
            try:
                # Test if function can be executed
                if func_name == "pg_read_file":
                    test_query = "SELECT pg_read_file('postgresql.conf', 1, 100);"
                elif func_name == "pg_ls_dir":
                    test_query = "SELECT pg_ls_dir('/tmp');"
                elif func_name == "copy_to_program":
                    test_query = "COPY (SELECT 'test') TO PROGRAM 'echo HELLO';"
                else:
                    test_query = f"SELECT {func_name}();"

                result = await conn.fetchval(test_query)

                if result:
                    finding = PrivilegeFinding(
                        database_type="PostgreSQL",
                        technique=EscalationTechnique.FUNCTION_ABUSE,
                        current_privilege=self.determine_privilege_level(privileges),
                        target_privilege=PrivilegeLevel.SUPERUSER,
                        severity=severity,
                        description=f"User {current_user} can execute dangerous function {func_name}",
                        evidence=f"Function {func_name} returned: {str(result)[:100]}",
                        recommendation="Restrict access to dangerous PostgreSQL functions",
                        cwe_id="CWE-862" if severity == "CRITICAL" else None
                    )
                    self.findings.append(finding)
                    self.logger.warning(f"⚠️  Dangerous function access: {func_name}")

            except Exception as e:
                # Expected for non-privileged users
                pass

        # Test for UDF privilege escalation
        await self.test_postgresql_udf_escalation(conn, current_user)

    async def test_postgresql_udf_escalation(self, conn, current_user: str):
        """Test PostgreSQL User-Defined Function privilege escalation"""
        try:
            # Check if user can create functions
            create_func_check = await conn.fetchval(
                "SELECT has_function_privilege(current_user, 'pg_catalog.int4(integer)', 'CREATE');"
            )

            if create_func_check:
                # Try to create a malicious UDF
                try:
                    malicious_udf = """
                    CREATE OR REPLACE FUNCTION escalate_priv() RETURNS integer AS $$
                    BEGIN
                        EXECUTE 'ALTER USER ' || current_user || ' SUPERUSER';
                        RETURN 1;
                    END;
                    $$ LANGUAGE plpgsql SECURITY DEFINER;
                    """

                    await conn.execute(malicious_udf)

                    finding = PrivilegeFinding(
                        database_type="PostgreSQL",
                        technique=EscalationTechnique.FUNCTION_ABUSE,
                        current_privilege=PrivilegeLevel.USER,
                        target_privilege=PrivilegeLevel.SUPERUSER,
                        severity="CRITICAL",
                        description=f"User {current_user} can create SECURITY DEFINER functions",
                        evidence="Function creation test succeeded",
                        recommendation="Restrict SECURITY DEFINER function creation",
                        cwe_id="CWE-913"
                    )
                    self.findings.append(finding)
                    self.logger.critical(f"🚨 UDF privilege escalation possible for {current_user}")

                    # Clean up
                    await conn.execute("DROP FUNCTION IF EXISTS escalate_priv();")

                except Exception as e:
                    self.logger.debug(f"UDF creation failed (expected): {str(e)}")

        except Exception as e:
            self.logger.debug(f"Error testing UDF escalation: {str(e)}")

    async def test_postgresql_role_abuse(self, conn, current_user: str):
        """Test PostgreSQL role abuse for privilege escalation"""
        try:
            # Get all available roles
            roles = await conn.fetch(
                "SELECT rolname, rolsuper, rolcreaterole FROM pg_roles WHERE rolcanlogin = false;"
            )

            for role in roles:
                role_name = role['rolname']

                try:
                    # Test if current user can SET ROLE
                    set_role_query = f"SET ROLE {role_name};"
                    await conn.execute(set_role_query)

                    # If successful, check new privileges
                    new_privileges = await self.get_postgresql_privileges(conn)

                    if new_privileges.get('superuser') and not await conn.fetchval(
                        "SELECT rolsuper FROM pg_roles WHERE rolname = current_user;"
                    ):
                        finding = PrivilegeFinding(
                            database_type="PostgreSQL",
                            technique=EscalationTechnique.ROLE_ABUSE,
                            current_privilege=PrivilegeLevel.USER,
                            target_privilege=PrivilegeLevel.SUPERUSER,
                            severity="CRITICAL",
                            description=f"User {current_user} can SET ROLE to {role_name} (superuser)",
                            evidence=f"Successfully set role to {role_name}",
                            recommendation="Restrict role membership and SET ROLE privileges",
                            cwe_id="CWE-269"
                        )
                        self.findings.append(finding)
                        self.logger.critical(f"🚨 Role abuse: {current_user} -> {role_name}")

                    # Reset role
                    await conn.execute("RESET ROLE;")

                except Exception:
                    # Expected - user cannot SET ROLE to this role
                    pass

        except Exception as e:
            self.logger.debug(f"Error testing role abuse: {str(e)}")

    async def test_postgresql_config_weaknesses(self, conn):
        """Test PostgreSQL configuration weaknesses"""
        try:
            # Check for dangerous configuration settings
            config_checks = [
                ("config_file", "Configuration file access", "SHOW config_file;"),
                ("data_directory", "Data directory access", "SHOW data_directory;"),
                ("hba_file", "HBA file access", "SHOW hba_file;"),
                ("ident_file", "Ident file access", "SHOW ident_file;"),
            ]

            for setting, description, query in config_checks:
                try:
                    result = await conn.fetchval(query)
                    if result:
                        finding = PrivilegeFinding(
                            database_type="PostgreSQL",
                            technique=EscalationTechnique.CONFIGURATION_WEAKNESS,
                            current_privilege=PrivilegeLevel.USER,
                            target_privilege=PrivilegeLevel.ADMIN,
                            severity="MEDIUM",
                            description=f"PostgreSQL configuration setting {setting} is accessible",
                            evidence=f"Setting value: {result}",
                            recommendation="Restrict access to configuration settings"
                        )
                        self.findings.append(finding)

                except Exception:
                    pass

            # Check for weak authentication methods
            try:
                hba_entries = await conn.fetch("SELECT * FROM pg_hba_file_rules();")
                for entry in hba_entries:
                    if entry['auth_method'] in ['trust', 'password', 'md5']:
                        finding = PrivilegeFinding(
                            database_type="PostgreSQL",
                            technique=EscalationTechnique.CONFIGURATION_WEAKNESS,
                            current_privilege=PrivilegeLevel.GUEST,
                            target_privilege=PrivilegeLevel.USER,
                            severity="HIGH",
                            description=f"Weak authentication method: {entry['auth_method']}",
                            evidence=f"HBA rule: {entry}",
                            recommendation="Use strong authentication methods like SCRAM-SHA-256"
                        )
                        self.findings.append(finding)

            except Exception:
                pass

        except Exception as e:
            self.logger.debug(f"Error testing config weaknesses: {str(e)}")

    async def test_postgresql_extensions(self, conn, current_user: str):
        """Test PostgreSQL extensions for privilege escalation"""
        dangerous_extensions = [
            ("pgcrypto", "Cryptographic functions"),
            ("adminpack", "Administrative functions"),
            ("pg_stat_statements", "Query statistics"),
            ("pg_buffercache", "Buffer cache access"),
        ]

        for ext_name, description in dangerous_extensions:
            try:
                # Check if extension is installed
                ext_check = await conn.fetchval(
                    "SELECT 1 FROM pg_extension WHERE extname = $1;", ext_name
                )

                if ext_check:
                    # Check if user can use extension functions
                    try:
                        if ext_name == "pgcrypto":
                            test_query = "SELECT gen_random_bytes(1);"
                        else:
                            test_query = f"SELECT * FROM pg_extension WHERE extname = '{ext_name}';"

                        result = await conn.fetchval(test_query)

                        finding = PrivilegeFinding(
                            database_type="PostgreSQL",
                            technique=EscalationTechnique.VULNERABLE_EXTENSION,
                            current_privilege=PrivilegeLevel.USER,
                            target_privilege=PrivilegeLevel.PRIVILEGED,
                            severity="MEDIUM",
                            description=f"User {current_user} can access extension {ext_name}: {description}",
                            evidence=f"Extension {ext_name} is accessible",
                            recommendation="Review and restrict access to database extensions"
                        )
                        self.findings.append(finding)

                    except Exception:
                        pass

            except Exception:
                pass

    async def test_postgresql_backup_escalation(self, conn, current_user: str):
        """Test PostgreSQL backup/restore privilege escalation"""
        try:
            # Check if user can create backups
            backup_privilege = await conn.fetchval(
                "SELECT has_database_privilege(current_database(), 'CREATE');"
            )

            if backup_privilege:
                try:
                    # Test COPY command (potential file write)
                    copy_test = "COPY (SELECT 'test') TO '/tmp/pg_backup_test.csv' WITH CSV;"
                    await conn.execute(copy_test)

                    # Clean up
                    await conn.execute("SELECT pg_read_file('/tmp/pg_backup_test.csv');")

                    finding = PrivilegeFinding(
                        database_type="PostgreSQL",
                        technique=EscalationTechnique.BACKUP_RESTORE,
                        current_privilege=PrivilegeLevel.USER,
                        target_privilege=PrivilegeLevel.ADMIN,
                        severity="HIGH",
                        description=f"User {current_user} can use COPY to write files",
                        evidence="COPY command succeeded",
                        recommendation="Restrict COPY command privileges",
                        cwe_id="CWE-89"
                    )
                    self.findings.append(finding)

                except Exception:
                    pass

        except Exception as e:
            self.logger.debug(f"Error testing backup escalation: {str(e)}")

    async def test_mongodb_privilege_escalation(self):
        """Test MongoDB privilege escalation vulnerabilities"""
        self.logger.info("🔍 Testing MongoDB privilege escalation...")

        client = self.connections['mongodb']

        try:
            # Get current user info
            try:
                user_info = await client.admin.command('usersInfo')
                current_user = user_info['users'][0]['user'] if user_info['users'] else 'unknown'
                current_roles = user_info['users'][0]['roles'] if user_info['users'] else []
            except:
                current_user = 'unknown'
                current_roles = []

            self.logger.info(f"Current MongoDB user: {current_user}")

            # Test for dangerous roles
            await self.test_mongodb_dangerous_roles(client, current_user, current_roles)

            # Test for JavaScript injection
            await self.test_mongodb_js_injection(client, current_user)

            # Test for aggregation pipeline abuse
            await self.test_mongodb_aggregation_abuse(client, current_user)

            # Test for mapReduce abuse
            await self.test_mongodb_mapreduce_abuse(client, current_user)

        except Exception as e:
            self.logger.error(f"Error testing MongoDB privilege escalation: {str(e)}")

    async def test_mongodb_dangerous_roles(self, client, current_user: str, current_roles: List[Dict]):
        """Test MongoDB dangerous roles"""
        dangerous_roles = [
            'root', 'dbAdminAnyDatabase', 'userAdminAnyDatabase',
            'readWriteAnyDatabase', 'clusterAdmin', 'clusterManager'
        ]

        for role_info in current_roles:
            role_name = role_info.get('role', '')
            role_db = role_info.get('db', '')

            if role_name in dangerous_roles:
                finding = PrivilegeFinding(
                    database_type="MongoDB",
                    technique=EscalationTechnique.ROLE_ABUSE,
                    current_privilege=PrivilegeLevel.USER,
                    target_privilege=PrivilegeLevel.SUPERUSER,
                    severity="HIGH",
                    description=f"User {current_user} has dangerous role: {role_name}",
                    evidence=f"Role: {role_name} on database: {role_db}",
                    recommendation="Review and minimize MongoDB role assignments",
                    cwe_id="CWE-269"
                )
                self.findings.append(finding)
                self.logger.warning(f"⚠️  Dangerous MongoDB role: {role_name}")

    async def test_mongodb_js_injection(self, client, current_user: str):
        """Test MongoDB JavaScript injection for privilege escalation"""
        try:
            db = client.testdb

            # Test $where operator injection
            test_payloads = [
                {"$where": "return true;"},
                {"$where": "function() { return true; }"},
                {"$where": "this.password == this.password"},
            ]

            for payload in test_payloads:
                try:
                    result = await db.testcollection.find(payload).to_list(length=1)
                    if result:
                        finding = PrivilegeFinding(
                            database_type="MongoDB",
                            technique=EscalationTechnique.SQL_INJECTION,
                            current_privilege=PrivilegeLevel.USER,
                            target_privilege=PrivilegeLevel.ADMIN,
                            severity="CRITICAL",
                            description=f"User {current_user} can use JavaScript in queries",
                            evidence=f"JavaScript payload succeeded: {payload}",
                            recommendation="Disable JavaScript execution in MongoDB queries",
                            cwe_id="CWE-94"
                        )
                        self.findings.append(finding)
                        self.logger.critical(f"🚨 JavaScript injection possible for {current_user}")
                        break

                except Exception:
                    pass

        except Exception as e:
            self.logger.debug(f"Error testing MongoDB JS injection: {str(e)}")

    async def test_mongodb_aggregation_abuse(self, client, current_user: str):
        """Test MongoDB aggregation pipeline abuse"""
        try:
            db = client.testdb

            # Test for dangerous aggregation stages
            dangerous_stages = [
                {"$lookup": {"from": "admin", "as": "admin"}},
                {"$function": {"body": "function() { return 'injected'; }", "args": []}},
                {"$out": "aggregation_test"},
            ]

            for stage in dangerous_stages:
                try:
                    pipeline = [stage]
                    result = await db.testcollection.aggregate(pipeline).to_list(length=1)

                    finding = PrivilegeFinding(
                        database_type="MongoDB",
                        technique=EscalationTechnique.FUNCTION_ABUSE,
                        current_privilege=PrivilegeLevel.USER,
                        target_privilege=PrivilegeLevel.ADMIN,
                        severity="HIGH",
                        description=f"User {current_user} can use dangerous aggregation stage",
                        evidence=f"Aggregation stage succeeded: {stage}",
                        recommendation="Restrict dangerous aggregation pipeline stages"
                    )
                    self.findings.append(finding)

                except Exception:
                    pass

        except Exception as e:
            self.logger.debug(f"Error testing MongoDB aggregation abuse: {str(e)}")

    async def test_mongodb_mapreduce_abuse(self, client, current_user: str):
        """Test MongoDB mapReduce abuse"""
        try:
            db = client.testdb

            # Test for code execution in mapReduce
            map_function = "function() { emit('test', 1); }"
            reduce_function = "function(key, values) { return values; }"

            try:
                result = await db.command(
                    'mapReduce',
                    'testcollection',
                    map=map_function,
                    reduce=reduce_function,
                    out={'inline': 1}
                )

                finding = PrivilegeFinding(
                    database_type="MongoDB",
                    technique=EscalationTechnique.FUNCTION_ABUSE,
                    current_privilege=PrivilegeLevel.USER,
                    target_privilege=PrivilegeLevel.PRIVILEGED,
                    severity="MEDIUM",
                    description=f"User {current_user} can execute mapReduce",
                    evidence="mapReduce command succeeded",
                    recommendation="Review mapReduce execution privileges"
                )
                self.findings.append(finding)

            except Exception:
                pass

        except Exception as e:
            self.logger.debug(f"Error testing MongoDB mapReduce abuse: {str(e)}")

    async def test_redis_privilege_escalation(self):
        """Test Redis privilege escalation vulnerabilities"""
        self.logger.info("🔍 Testing Redis privilege escalation...")

        client = self.connections['redis']

        try:
            # Test for dangerous Redis commands
            dangerous_commands = [
                ('CONFIG', 'Configuration access', 'HIGH'),
                ('SAVE', 'Database dump', 'MEDIUM'),
                ('BGSAVE', 'Background dump', 'MEDIUM'),
                ('DEBUG', 'Debug commands', 'HIGH'),
                ('EVAL', 'Lua script execution', 'CRITICAL'),
                ('SCRIPT', 'Script management', 'HIGH'),
                ('MODULE', 'Module management', 'CRITICAL'),
                ('SLAVEOF', 'Replication control', 'HIGH'),
                ('REPLICAOF', 'Replication control', 'HIGH'),
            ]

            for command, description, severity in dangerous_commands:
                try:
                    # Test command execution (read-only where possible)
                    if command == 'CONFIG':
                        result = await client.config_get('*')
                    elif command == 'INFO':
                        result = await client.info()
                    elif command == 'EVAL':
                        # Test with harmless script
                        result = await client.eval('return 1', 0)
                    else:
                        # Skip potentially destructive commands
                        continue

                    finding = PrivilegeFinding(
                        database_type="Redis",
                        technique=EscalationTechnique.FUNCTION_ABUSE,
                        current_privilege=PrivilegeLevel.USER,
                        target_privilege=PrivilegeLevel.ADMIN,
                        severity=severity,
                        description=f"User can execute Redis command {command}: {description}",
                        evidence=f"Command {command} succeeded",
                        recommendation="Restrict dangerous Redis commands using ACL rules"
                    )
                    self.findings.append(finding)
                    self.logger.warning(f"⚠️  Dangerous Redis command accessible: {command}")

                except Exception as e:
                    # Expected for restricted commands
                    pass

            # Test for authentication bypass
            await self.test_redis_auth_bypass(client)

        except Exception as e:
            self.logger.error(f"Error testing Redis privilege escalation: {str(e)}")

    async def test_redis_auth_bypass(self, client):
        """Test Redis authentication bypass"""
        try:
            # Check if authentication is required
            info = await client.info()
            if 'requirepass' not in str(info):
                finding = PrivilegeFinding(
                    database_type="Redis",
                    technique=EscalationTechnique.DEFAULT_CREDENTIALS,
                    current_privilege=PrivilegeLevel.GUEST,
                    target_privilege=PrivilegeLevel.ADMIN,
                    severity="HIGH",
                    description="Redis instance does not require authentication",
                    evidence="No requirepass in INFO output",
                    recommendation="Enable Redis authentication with strong password"
                )
                self.findings.append(finding)
                self.logger.warning("⚠️  Redis authentication not required")

        except Exception as e:
            self.logger.debug(f"Error testing Redis auth bypass: {str(e)}")

    async def test_cross_database_escalation(self):
        """Test cross-database privilege escalation"""
        self.logger.info("🔍 Testing cross-database privilege escalation...")

        # Test if compromised database can access other databases
        if 'mongodb' in self.connections and 'postgresql' in self.connections:
            await self.test_mongo_to_pg_escalation()

        if 'postgresql' in self.connections and 'mongodb' in self.connections:
            await self.test_pg_to_mongo_escalation()

    async def test_mongo_to_pg_escalation(self):
        """Test MongoDB to PostgreSQL escalation"""
        try:
            # Check if MongoDB can connect to PostgreSQL
            # This would require network access testing
            self.logger.info("ℹ️  Cross-database escalation testing requires network access checks")

        except Exception as e:
            self.logger.debug(f"Error testing Mongo to PG escalation: {str(e)}")

    async def test_pg_to_mongo_escalation(self):
        """Test PostgreSQL to MongoDB escalation"""
        try:
            # Check if PostgreSQL can connect to MongoDB
            # This would require dblink or foreign data wrapper testing
            self.logger.info("ℹ️  Cross-database escalation testing requires foreign data wrapper checks")

        except Exception as e:
            self.logger.debug(f"Error testing PG to Mongo escalation: {str(e)}")

    def determine_privilege_level(self, privileges: Dict[str, bool]) -> PrivilegeLevel:
        """Determine privilege level from PostgreSQL privileges"""
        if privileges.get('superuser', False):
            return PrivilegeLevel.SUPERUSER
        elif any(privileges.get(key, False) for key in ['create_role', 'create_db']):
            return PrivilegeLevel.ADMIN
        elif any(privileges.get(key, False) for key in ['replication', 'bypass_rls']):
            return PrivilegeLevel.PRIVILEGED
        elif privileges.get('can_login', False):
            return PrivilegeLevel.USER
        else:
            return PrivilegeLevel.GUEST

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive privilege escalation report"""
        self.logger.info("📋 Generating privilege escalation report...")

        report = {
            "scan_date": datetime.utcnow().isoformat(),
            "total_findings": len(self.findings),
            "findings": [],
            "summary": {},
            "recommendations": []
        }

        # Categorize findings
        findings_by_db = {}
        findings_by_severity = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }

        for finding in self.findings:
            # Convert to dictionary
            finding_dict = {
                "database_type": finding.database_type,
                "technique": finding.technique.value,
                "current_privilege": finding.current_privilege.value,
                "target_privilege": finding.target_privilege.value,
                "severity": finding.severity,
                "description": finding.description,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
                "cwe_id": finding.cwe_id
            }
            report["findings"].append(finding_dict)

            # Categorize
            db_type = finding.database_type
            if db_type not in findings_by_db:
                findings_by_db[db_type] = []
            findings_by_db[db_type].append(finding_dict)

            severity = finding.severity
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1

        report["summary"] = {
            "by_database": findings_by_db,
            "by_severity": findings_by_severity,
            "by_technique": self.count_by_technique()
        }

        # Generate recommendations
        if findings_by_severity["CRITICAL"] > 0:
            report["recommendations"].append({
                "priority": "IMMEDIATE",
                "issue": "Critical privilege escalation vulnerabilities",
                "action": "Address all critical findings immediately",
                "affected_systems": len(set(f.database_type for f in self.findings if f.severity == "CRITICAL"))
            })

        if findings_by_severity["HIGH"] > 0:
            report["recommendations"].append({
                "priority": "URGENT",
                "issue": "High-risk privilege escalation",
                "action": "Address high-risk findings within 48 hours",
                "affected_systems": len(set(f.database_type for f in self.findings if f.severity == "HIGH"))
            })

        report["recommendations"].extend([
            {
                "priority": "STANDARD",
                "issue": "Principle of least privilege",
                "action": "Apply principle of least privilege to all database users"
            },
            {
                "priority": "STANDARD",
                "issue": "Regular privilege audits",
                "action": "Conduct regular privilege audits and role reviews"
            },
            {
                "priority": "STANDARD",
                "issue": "Database hardening",
                "action": "Implement database hardening guidelines and secure configurations"
            },
            {
                "priority": "STANDARD",
                "issue": "Monitoring and logging",
                "action": "Enable comprehensive logging and monitoring of privilege usage"
            }
        ])

        # Save report
        report_file = f"privilege_escalation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"✅ Privilege escalation report saved to: {report_file}")
        return report

    def count_by_technique(self) -> Dict[str, int]:
        """Count findings by escalation technique"""
        technique_count = {}
        for finding in self.findings:
            technique = finding.technique.value
            technique_count[technique] = technique_count.get(technique, 0) + 1
        return technique_count

    async def cleanup(self):
        """Cleanup database connections"""
        for db_type, conn in self.connections.items():
            try:
                if db_type == 'postgresql':
                    await conn.close()
                elif db_type == 'mongodb':
                    conn.close()
                elif db_type == 'redis':
                    await conn.close()
            except Exception as e:
                self.logger.error(f"Error closing {db_type} connection: {str(e)}")

async def main():
    """Main execution function"""
    config = {
        "mongodb": {
            "host": "localhost",
            "port": 27017,
            "username": os.getenv("MONGO_USERNAME"),
            "password": os.getenv("MONGO_PASSWORD"),
            "authDatabase": "admin"
        },
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "psychsync",
            "username": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD")
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "password": os.getenv("REDIS_PASSWORD")
        }
    }

    tester = PrivilegeEscalationTester(config)

    try:
        await tester.setup_connections()
        report = await tester.run_all_tests()

        print(f"\n🔍 Privilege Escalation Test Complete")
        print(f"📊 Total Findings: {report['total_findings']}")
        print(f"🚨 Critical: {report['summary']['by_severity'].get('CRITICAL', 0)}")
        print(f"⚠️  High: {report['summary']['by_severity'].get('HIGH', 0)}")
        print(f"⚡ Medium: {report['summary']['by_severity'].get('MEDIUM', 0)}")
        print(f"ℹ️  Low: {report['summary']['by_severity'].get('LOW', 0)}")

        # Show database breakdown
        print(f"\n📊 Findings by Database:")
        for db_type, findings in report['summary']['by_database'].items():
            print(f"• {db_type}: {len(findings)} findings")

        # Show critical findings
        critical_findings = [f for f in tester.findings if f.severity == 'CRITICAL']
        if critical_findings:
            print(f"\n🚨 CRITICAL FINDINGS:")
            for finding in critical_findings[:5]:
                print(f"• {finding.database_type}: {finding.description}")

    except Exception as e:
        print(f"❌ Error during privilege escalation testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())