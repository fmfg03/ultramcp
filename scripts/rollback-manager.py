#!/usr/bin/env python3
"""
UltraMCP Comprehensive Rollback Manager
Handles system rollbacks, migrations, and recovery procedures
"""

import json
import os
import shutil
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import tarfile
import hashlib

@dataclass
class BackupSnapshot:
    """Backup snapshot metadata"""
    id: str
    timestamp: datetime
    version: str
    description: str
    size_mb: float
    file_path: str
    checksum: str
    components: List[str]
    rollback_tested: bool = False

@dataclass
class RollbackPlan:
    """Rollback execution plan"""
    snapshot_id: str
    target_version: str
    steps: List[Dict[str, Any]]
    estimated_downtime: int  # minutes
    risk_level: str  # 'low', 'medium', 'high'
    validation_checks: List[str]

class SystemBackupManager:
    """Manages system backups for rollback purposes"""
    
    def __init__(self, backup_dir: str = "data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_file = self.backup_dir / "snapshots.json"
        self.max_backups = 10
        self.load_snapshots()
    
    def load_snapshots(self):
        """Load backup snapshots metadata"""
        if self.snapshots_file.exists():
            try:
                with open(self.snapshots_file, 'r') as f:
                    data = json.load(f)
                    self.snapshots = [
                        BackupSnapshot(**snapshot) for snapshot in data.get('snapshots', [])
                    ]
            except Exception as e:
                logging.error(f"Failed to load snapshots: {e}")
                self.snapshots = []
        else:
            self.snapshots = []
    
    def save_snapshots(self):
        """Save backup snapshots metadata"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "snapshots": [asdict(snapshot) for snapshot in self.snapshots]
            }
            
            with open(self.snapshots_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logging.error(f"Failed to save snapshots: {e}")
    
    def create_backup(self, description: str = "", components: List[str] = None) -> Optional[BackupSnapshot]:
        """Create a comprehensive system backup"""
        timestamp = datetime.now()
        backup_id = f"backup_{int(timestamp.timestamp())}"
        backup_file = self.backup_dir / f"{backup_id}.tar.gz"
        
        if components is None:
            components = [
                "configurations",
                "scripts", 
                "data",
                "logs",
                "docker-compose",
                "environment"
            ]
        
        try:
            # Create backup archive
            with tarfile.open(backup_file, "w:gz") as tar:
                
                # Backup configurations
                if "configurations" in components:
                    config_files = [
                        ".env",
                        "Makefile",
                        "docker-compose.yml",
                        "docker-compose.hybrid.yml",
                        "docker-compose.dev.yml",
                        "requirements.txt",
                        "package.json",
                        "CLAUDE.md"
                    ]
                    
                    for config_file in config_files:
                        if Path(config_file).exists():
                            tar.add(config_file, arcname=f"configs/{config_file}")
                
                # Backup scripts
                if "scripts" in components and Path("scripts").exists():
                    tar.add("scripts", arcname="scripts")
                
                # Backup data (excluding large files)
                if "data" in components and Path("data").exists():
                    self._add_data_to_backup(tar, "data")
                
                # Backup recent logs
                if "logs" in components and Path("logs").exists():
                    self._add_logs_to_backup(tar, "logs")
                
                # Backup service registry
                if Path("data/fallback").exists():
                    tar.add("data/fallback", arcname="fallback")
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_file)
            
            # Get file size
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            
            # Create snapshot metadata
            snapshot = BackupSnapshot(
                id=backup_id,
                timestamp=timestamp,
                version=self._get_current_version(),
                description=description or f"Automatic backup {timestamp.strftime('%Y-%m-%d %H:%M')}",
                size_mb=round(size_mb, 2),
                file_path=str(backup_file),
                checksum=checksum,
                components=components
            )
            
            # Add to snapshots
            self.snapshots.append(snapshot)
            self.save_snapshots()
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            logging.info(f"Created backup: {backup_id} ({size_mb:.2f} MB)")
            return snapshot
            
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            if backup_file.exists():
                backup_file.unlink()  # Cleanup failed backup
            return None
    
    def _add_data_to_backup(self, tar, data_path: str):
        """Add data directory to backup (excluding large files)"""
        data_dir = Path(data_path)
        
        for item in data_dir.rglob("*"):
            if item.is_file():
                # Skip large files (>100MB)
                if item.stat().st_size > 100 * 1024 * 1024:
                    logging.warning(f"Skipping large file in backup: {item}")
                    continue
                
                # Skip temporary files
                if item.suffix in ['.tmp', '.temp', '.cache']:
                    continue
                
                arcname = str(item.relative_to(Path.cwd()))
                tar.add(item, arcname=arcname)
    
    def _add_logs_to_backup(self, tar, logs_path: str):
        """Add recent logs to backup"""
        logs_dir = Path(logs_path)
        cutoff_date = datetime.now() - timedelta(days=7)  # Last 7 days
        
        for log_file in logs_dir.glob("*.log"):
            if log_file.stat().st_mtime > cutoff_date.timestamp():
                arcname = str(log_file.relative_to(Path.cwd()))
                tar.add(log_file, arcname=arcname)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_current_version(self) -> str:
        """Get current system version"""
        try:
            # Try to get git commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return f"git-{result.stdout.strip()}"
        except:
            pass
        
        # Fallback to timestamp
        return f"version-{int(datetime.now().timestamp())}"
    
    def _cleanup_old_backups(self):
        """Remove old backups beyond max_backups limit"""
        if len(self.snapshots) > self.max_backups:
            # Sort by timestamp, keep newest
            self.snapshots.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Remove old snapshots
            old_snapshots = self.snapshots[self.max_backups:]
            for snapshot in old_snapshots:
                try:
                    backup_file = Path(snapshot.file_path)
                    if backup_file.exists():
                        backup_file.unlink()
                    logging.info(f"Removed old backup: {snapshot.id}")
                except Exception as e:
                    logging.error(f"Failed to remove old backup {snapshot.id}: {e}")
            
            # Keep only recent snapshots
            self.snapshots = self.snapshots[:self.max_backups]
            self.save_snapshots()
    
    def verify_backup(self, snapshot_id: str) -> bool:
        """Verify backup integrity"""
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return False
        
        backup_file = Path(snapshot.file_path)
        if not backup_file.exists():
            logging.error(f"Backup file not found: {backup_file}")
            return False
        
        # Verify checksum
        current_checksum = self._calculate_checksum(backup_file)
        if current_checksum != snapshot.checksum:
            logging.error(f"Backup checksum mismatch for {snapshot_id}")
            return False
        
        # Verify archive integrity
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.getnames()  # This will fail if archive is corrupted
            logging.info(f"Backup verification successful: {snapshot_id}")
            return True
        except Exception as e:
            logging.error(f"Backup archive verification failed: {e}")
            return False
    
    def get_snapshot(self, snapshot_id: str) -> Optional[BackupSnapshot]:
        """Get backup snapshot by ID"""
        for snapshot in self.snapshots:
            if snapshot.id == snapshot_id:
                return snapshot
        return None
    
    def list_snapshots(self) -> List[BackupSnapshot]:
        """List all backup snapshots"""
        return sorted(self.snapshots, key=lambda x: x.timestamp, reverse=True)

class RollbackManager:
    """Manages system rollbacks and recovery procedures"""
    
    def __init__(self):
        self.backup_manager = SystemBackupManager()
        self.rollback_log = Path("data/rollback_history.json")
        self.rollback_log.parent.mkdir(parents=True, exist_ok=True)
    
    def create_rollback_plan(self, snapshot_id: str) -> Optional[RollbackPlan]:
        """Create a rollback execution plan"""
        snapshot = self.backup_manager.get_snapshot(snapshot_id)
        if not snapshot:
            logging.error(f"Snapshot not found: {snapshot_id}")
            return None
        
        # Verify backup before creating plan
        if not self.backup_manager.verify_backup(snapshot_id):
            logging.error(f"Backup verification failed: {snapshot_id}")
            return None
        
        # Create rollback steps
        steps = [
            {
                "step": 1,
                "action": "pre_rollback_backup",
                "description": "Create pre-rollback backup",
                "command": "python3 scripts/rollback-manager.py --backup 'Pre-rollback backup'",
                "rollback_on_failure": False
            },
            {
                "step": 2,
                "action": "stop_services",
                "description": "Stop all services gracefully",
                "command": "make docker-down",
                "rollback_on_failure": False
            },
            {
                "step": 3,
                "action": "restore_configurations",
                "description": "Restore configuration files",
                "command": f"tar -xzf {snapshot.file_path} configs/",
                "rollback_on_failure": True
            },
            {
                "step": 4,
                "action": "restore_scripts",
                "description": "Restore script files",
                "command": f"tar -xzf {snapshot.file_path} scripts/",
                "rollback_on_failure": True
            },
            {
                "step": 5,
                "action": "restore_data",
                "description": "Restore data files",
                "command": f"tar -xzf {snapshot.file_path} data/",
                "rollback_on_failure": True
            },
            {
                "step": 6,
                "action": "restore_fallback_data",
                "description": "Restore fallback registry",
                "command": f"tar -xzf {snapshot.file_path} fallback/",
                "rollback_on_failure": True
            },
            {
                "step": 7,
                "action": "restart_services",
                "description": "Restart services",
                "command": "make docker-hybrid",
                "rollback_on_failure": False
            },
            {
                "step": 8,
                "action": "validate_system",
                "description": "Validate system health",
                "command": "make health-check",
                "rollback_on_failure": False
            }
        ]
        
        # Determine risk level
        age_hours = (datetime.now() - snapshot.timestamp).total_seconds() / 3600
        if age_hours < 24:
            risk_level = "low"
        elif age_hours < 168:  # 1 week
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Validation checks
        validation_checks = [
            "Services are responding",
            "Database connectivity",
            "API endpoints accessible",
            "Core functionality working",
            "No critical errors in logs"
        ]
        
        plan = RollbackPlan(
            snapshot_id=snapshot_id,
            target_version=snapshot.version,
            steps=steps,
            estimated_downtime=5,  # 5 minutes estimated
            risk_level=risk_level,
            validation_checks=validation_checks
        )
        
        return plan
    
    def execute_rollback(self, plan: RollbackPlan, dry_run: bool = False) -> Dict[str, Any]:
        """Execute rollback plan"""
        rollback_id = f"rollback_{int(datetime.now().timestamp())}"
        
        execution_log = {
            "rollback_id": rollback_id,
            "plan": asdict(plan),
            "started_at": datetime.now().isoformat(),
            "dry_run": dry_run,
            "steps_executed": [],
            "status": "in_progress",
            "error": None
        }
        
        try:
            logging.info(f"{'DRY RUN: ' if dry_run else ''}Starting rollback {rollback_id}")
            
            for step in plan.steps:
                step_start = datetime.now()
                step_log = {
                    "step": step["step"],
                    "action": step["action"],
                    "description": step["description"],
                    "command": step["command"],
                    "started_at": step_start.isoformat(),
                    "status": "running"
                }
                
                try:
                    if not dry_run:
                        # Execute the command
                        result = subprocess.run(
                            step["command"],
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes timeout per step
                        )
                        
                        step_log["exit_code"] = result.returncode
                        step_log["stdout"] = result.stdout
                        step_log["stderr"] = result.stderr
                        
                        if result.returncode != 0:
                            step_log["status"] = "failed"
                            logging.error(f"Rollback step {step['step']} failed: {result.stderr}")
                            
                            if step.get("rollback_on_failure", False):
                                execution_log["status"] = "failed"
                                execution_log["error"] = f"Step {step['step']} failed: {result.stderr}"
                                break
                        else:
                            step_log["status"] = "completed"
                    else:
                        # Dry run - just log what would be executed
                        step_log["status"] = "dry_run"
                        step_log["note"] = "Command not executed (dry run)"
                    
                    step_log["completed_at"] = datetime.now().isoformat()
                    step_log["duration_seconds"] = (datetime.now() - step_start).total_seconds()
                    
                except subprocess.TimeoutExpired:
                    step_log["status"] = "timeout"
                    step_log["error"] = "Command timed out"
                    execution_log["status"] = "failed"
                    execution_log["error"] = f"Step {step['step']} timed out"
                    break
                
                except Exception as e:
                    step_log["status"] = "error"
                    step_log["error"] = str(e)
                    logging.error(f"Rollback step {step['step']} error: {e}")
                    
                    if step.get("rollback_on_failure", False):
                        execution_log["status"] = "failed"
                        execution_log["error"] = f"Step {step['step']} error: {str(e)}"
                        break
                
                execution_log["steps_executed"].append(step_log)
                logging.info(f"Rollback step {step['step']}: {step_log['status']}")
            
            # If we completed all steps successfully
            if execution_log["status"] == "in_progress":
                execution_log["status"] = "completed"
                
                # Run validation checks
                if not dry_run:
                    validation_results = self._run_validation_checks(plan.validation_checks)
                    execution_log["validation"] = validation_results
                    
                    if not validation_results["all_passed"]:
                        execution_log["status"] = "completed_with_warnings"
                        logging.warning("Rollback completed but validation checks failed")
            
            execution_log["completed_at"] = datetime.now().isoformat()
            total_duration = (datetime.now() - datetime.fromisoformat(execution_log["started_at"])).total_seconds()
            execution_log["total_duration_seconds"] = total_duration
            
            # Save rollback log
            self._save_rollback_log(execution_log)
            
            logging.info(f"Rollback {rollback_id} {execution_log['status']} in {total_duration:.2f}s")
            
        except Exception as e:
            execution_log["status"] = "error"
            execution_log["error"] = str(e)
            execution_log["completed_at"] = datetime.now().isoformat()
            self._save_rollback_log(execution_log)
            logging.error(f"Rollback {rollback_id} failed: {e}")
        
        return execution_log
    
    def _run_validation_checks(self, checks: List[str]) -> Dict[str, Any]:
        """Run post-rollback validation checks"""
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "passed": 0,
            "failed": 0,
            "all_passed": True
        }
        
        # Define validation commands
        validation_commands = {
            "Services are responding": "make status",
            "Database connectivity": "python3 scripts/database-fallback.py --status",
            "API endpoints accessible": "curl -f http://sam.chat:8001/health",
            "Core functionality working": "make chat TEXT='test' > /dev/null",
            "No critical errors in logs": "grep -i error logs/combined.log | tail -5"
        }
        
        for check in checks:
            check_result = {
                "check": check,
                "status": "unknown",
                "output": "",
                "error": ""
            }
            
            command = validation_commands.get(check)
            if command:
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        check_result["status"] = "passed"
                        validation_results["passed"] += 1
                    else:
                        check_result["status"] = "failed"
                        check_result["error"] = result.stderr
                        validation_results["failed"] += 1
                        validation_results["all_passed"] = False
                    
                    check_result["output"] = result.stdout
                    
                except Exception as e:
                    check_result["status"] = "error"
                    check_result["error"] = str(e)
                    validation_results["failed"] += 1
                    validation_results["all_passed"] = False
            
            validation_results["checks"].append(check_result)
        
        return validation_results
    
    def _save_rollback_log(self, execution_log: Dict[str, Any]):
        """Save rollback execution log"""
        try:
            # Load existing logs
            if self.rollback_log.exists():
                with open(self.rollback_log, 'r') as f:
                    logs_data = json.load(f)
            else:
                logs_data = {"rollbacks": []}
            
            # Add new log
            logs_data["rollbacks"].append(execution_log)
            
            # Keep only last 50 rollback logs
            logs_data["rollbacks"] = logs_data["rollbacks"][-50:]
            
            # Save logs
            with open(self.rollback_log, 'w') as f:
                json.dump(logs_data, f, indent=2, default=str)
                
        except Exception as e:
            logging.error(f"Failed to save rollback log: {e}")
    
    def get_rollback_history(self) -> List[Dict[str, Any]]:
        """Get rollback execution history"""
        try:
            if self.rollback_log.exists():
                with open(self.rollback_log, 'r') as f:
                    logs_data = json.load(f)
                    return logs_data.get("rollbacks", [])
            return []
        except Exception as e:
            logging.error(f"Failed to load rollback history: {e}")
            return []

# Global rollback manager instance
rollback_manager = RollbackManager()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="UltraMCP Rollback Manager")
    parser.add_argument("--backup", type=str, help="Create backup with description")
    parser.add_argument("--list-backups", action="store_true", help="List all backups")
    parser.add_argument("--verify", type=str, help="Verify backup by ID")
    parser.add_argument("--plan", type=str, help="Create rollback plan for snapshot ID")
    parser.add_argument("--rollback", type=str, help="Execute rollback for snapshot ID")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run (with --rollback)")
    parser.add_argument("--history", action="store_true", help="Show rollback history")
    
    args = parser.parse_args()
    
    if args.backup:
        snapshot = rollback_manager.backup_manager.create_backup(args.backup)
        if snapshot:
            print(f"Backup created: {snapshot.id} ({snapshot.size_mb} MB)")
        else:
            print("Backup creation failed")
    
    if args.list_backups:
        snapshots = rollback_manager.backup_manager.list_snapshots()
        print("Available backups:")
        for snapshot in snapshots:
            print(f"  {snapshot.id}: {snapshot.description} ({snapshot.timestamp}) - {snapshot.size_mb}MB")
    
    if args.verify:
        if rollback_manager.backup_manager.verify_backup(args.verify):
            print(f"Backup {args.verify} is valid")
        else:
            print(f"Backup {args.verify} verification failed")
    
    if args.plan:
        plan = rollback_manager.create_rollback_plan(args.plan)
        if plan:
            print(f"Rollback plan for {args.plan}:")
            print(json.dumps(asdict(plan), indent=2, default=str))
        else:
            print(f"Failed to create rollback plan for {args.plan}")
    
    if args.rollback:
        plan = rollback_manager.create_rollback_plan(args.rollback)
        if plan:
            print(f"Executing rollback to {args.rollback}...")
            result = rollback_manager.execute_rollback(plan, dry_run=args.dry_run)
            print(f"Rollback {result['status']}")
            if result.get('error'):
                print(f"Error: {result['error']}")
        else:
            print(f"Cannot create rollback plan for {args.rollback}")
    
    if args.history:
        history = rollback_manager.get_rollback_history()
        print("Rollback history:")
        for rollback in history[-10:]:  # Last 10 rollbacks
            print(f"  {rollback['rollback_id']}: {rollback['status']} at {rollback['started_at']}")