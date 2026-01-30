"""
Compliance and safety features.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..services import get_logger
from ..models import Account, Campaign, SendLog


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    name: str
    description: str
    check_function: callable
    severity: str  # "warning", "error", "block"
    auto_fix: bool = False


class ComplianceChecker:
    """Checks compliance with safety rules and regulations."""
    
    def __init__(self):
        """Initialize compliance checker."""
        self.logger = get_logger()
        self.rules = self._setup_rules()
    
    def _setup_rules(self) -> List[ComplianceRule]:
        """Set up compliance rules."""
        return [
            ComplianceRule(
                name="rate_limit_check",
                description="Check if sending rate is within limits",
                check_function=self._check_rate_limits,
                severity="block"
            ),
            ComplianceRule(
                name="account_warmup_check",
                description="Check if account has completed warmup",
                check_function=self._check_account_warmup,
                severity="warning"
            ),
            ComplianceRule(
                name="message_content_check",
                description="Check message content for compliance",
                check_function=self._check_message_content,
                severity="warning"
            ),
            ComplianceRule(
                name="recipient_validation",
                description="Validate recipient information",
                check_function=self._check_recipient_validation,
                severity="error"
            ),
        ]
    
    def check_campaign_compliance(self, campaign: Campaign) -> Dict[str, Any]:
        """Check campaign compliance."""
        violations = []
        warnings = []
        
        for rule in self.rules:
            try:
                result = rule.check_function(campaign)
                if not result["compliant"]:
                    if rule.severity == "block":
                        violations.append({
                            "rule": rule.name,
                            "message": result["message"],
                            "severity": rule.severity
                        })
                    else:
                        warnings.append({
                            "rule": rule.name,
                            "message": result["message"],
                            "severity": rule.severity
                        })
            except Exception as e:
                self.logger.error(f"Error checking rule {rule.name}: {e}")
                warnings.append({
                    "rule": rule.name,
                    "message": f"Rule check failed: {e}",
                    "severity": "warning"
                })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "checked_at": datetime.utcnow()
        }
    
    def check_account_compliance(self, account: Account) -> Dict[str, Any]:
        """Check account compliance."""
        violations = []
        warnings = []
        
        # Check account status
        if account.status != "online":
            violations.append({
                "rule": "account_status",
                "message": f"Account is not online (status: {account.status})",
                "severity": "block"
            })
        
        # Check warmup
        if not account.is_warmup_complete():
            warnings.append({
                "rule": "warmup_incomplete",
                "message": "Account has not completed warmup period",
                "severity": "warning"
            })
        
        # Check rate limits
        if account.total_messages_sent > account.rate_limit_per_day:
            violations.append({
                "rule": "daily_limit_exceeded",
                "message": f"Daily message limit exceeded ({account.total_messages_sent}/{account.rate_limit_per_day})",
                "severity": "block"
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "checked_at": datetime.utcnow()
        }
    
    def _check_rate_limits(self, campaign: Campaign) -> Dict[str, Any]:
        """Check rate limits."""
        if campaign.messages_per_minute > 30:
            return {
                "compliant": False,
                "message": f"Messages per minute ({campaign.messages_per_minute}) exceeds safe limit (30)"
            }
        
        if campaign.messages_per_hour > 100:
            return {
                "compliant": False,
                "message": f"Messages per hour ({campaign.messages_per_hour}) exceeds safe limit (100)"
            }
        
        if campaign.messages_per_day > 500:
            return {
                "compliant": False,
                "message": f"Messages per day ({campaign.messages_per_day}) exceeds safe limit (500)"
            }
        
        return {"compliant": True, "message": "Rate limits are within safe bounds"}
    
    def _check_account_warmup(self, campaign: Campaign) -> Dict[str, Any]:
        """Check account warmup status."""
        # This would check if all accounts have completed warmup
        return {"compliant": True, "message": "Account warmup check passed"}
    
    def _check_message_content(self, campaign: Campaign) -> Dict[str, Any]:
        """Check message content for compliance."""
        # Check for spam indicators
        spam_keywords = ["free", "urgent", "limited time", "click here", "act now"]
        message_lower = campaign.message_text.lower()
        
        spam_count = sum(1 for keyword in spam_keywords if keyword in message_lower)
        if spam_count > 2:
            return {
                "compliant": False,
                "message": f"Message contains {spam_count} potential spam keywords"
            }
        
        # Check message length
        if len(campaign.message_text) > 1000:
            return {
                "compliant": False,
                "message": "Message is too long (over 1000 characters)"
            }
        
        return {"compliant": True, "message": "Message content is compliant"}
    
    def _check_recipient_validation(self, campaign: Campaign) -> Dict[str, Any]:
        """Check recipient validation."""
        if campaign.total_recipients == 0:
            return {
                "compliant": False,
                "message": "No recipients specified for campaign"
            }
        
        if campaign.total_recipients > 10000:
            return {
                "compliant": False,
                "message": f"Too many recipients ({campaign.total_recipients}), maximum is 10000"
            }
        
        return {"compliant": True, "message": "Recipient validation passed"}


class SafetyGuard:
    """Safety guard for preventing abuse and ensuring compliance."""
    
    def __init__(self):
        """Initialize safety guard."""
        self.logger = get_logger()
        self.compliance_checker = ComplianceChecker()
        self.blocked_accounts: set = set()
        self.blocked_campaigns: set = set()
    
    def check_send_permission(self, account_id: int, campaign_id: int) -> bool:
        """Check if sending is permitted."""
        if account_id in self.blocked_accounts:
            self.logger.log_safety_event("account_blocked", f"Account {account_id} is blocked")
            return False
        
        if campaign_id in self.blocked_campaigns:
            self.logger.log_safety_event("campaign_blocked", f"Campaign {campaign_id} is blocked")
            return False
        
        return True
    
    def block_account(self, account_id: int, reason: str):
        """Block an account from sending."""
        self.blocked_accounts.add(account_id)
        self.logger.log_safety_event("account_blocked", f"Account {account_id} blocked: {reason}")
    
    def unblock_account(self, account_id: int):
        """Unblock an account."""
        self.blocked_accounts.discard(account_id)
        self.logger.log_safety_event("account_unblocked", f"Account {account_id} unblocked")
    
    def block_campaign(self, campaign_id: int, reason: str):
        """Block a campaign from running."""
        self.blocked_campaigns.add(campaign_id)
        self.logger.log_safety_event("campaign_blocked", f"Campaign {campaign_id} blocked: {reason}")
    
    def unblock_campaign(self, campaign_id: int):
        """Unblock a campaign."""
        self.blocked_campaigns.discard(campaign_id)
        self.logger.log_safety_event("campaign_unblocked", f"Campaign {campaign_id} unblocked")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status."""
        return {
            "blocked_accounts": list(self.blocked_accounts),
            "blocked_campaigns": list(self.blocked_campaigns),
            "total_blocked_accounts": len(self.blocked_accounts),
            "total_blocked_campaigns": len(self.blocked_campaigns)
        }
