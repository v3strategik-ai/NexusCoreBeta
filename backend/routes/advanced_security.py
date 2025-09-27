#!/usr/bin/env python3
"""
Phase 6C: Advanced Security System
Multi-factor authentication, session management, and enterprise security features
"""

import asyncio
import logging
import secrets
import hashlib
import base64
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import jwt
import pyotp
import bcrypt
from enum import Enum
import requests
from dataclasses import dataclass

from database import get_database

logger = logging.getLogger(__name__)

class AuthMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    API_KEY = "api_key"
    SSO = "sso"

class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SessionStatus(Enum):
    """Session status types"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    user_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    risk_score: float

# Request/Response Models
class MFASetupRequest(BaseModel):
    """Request to setup multi-factor authentication"""
    user_id: str
    method: AuthMethod = AuthMethod.MFA_TOTP
    phone_number: Optional[str] = None

class MFAVerificationRequest(BaseModel):
    """Request to verify MFA token"""
    user_id: str
    token: str
    method: AuthMethod = AuthMethod.MFA_TOTP

class PasswordPolicyRequest(BaseModel):
    """Request to update password policy"""
    tenant_id: str
    min_length: int = Field(default=8, ge=6, le=50)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_symbols: bool = True
    max_age_days: int = Field(default=90, ge=30, le=365)
    prevent_reuse: int = Field(default=5, ge=3, le=20)
    lockout_attempts: int = Field(default=5, ge=3, le=10)

class IPRestrictionsRequest(BaseModel):
    """Request to manage IP restrictions"""
    tenant_id: str
    allowed_ips: List[str] = Field(default=[], description="List of allowed IP addresses/CIDR blocks")
    blocked_ips: List[str] = Field(default=[], description="List of blocked IP addresses/CIDR blocks")
    require_whitelist: bool = False
    
    @validator('allowed_ips', 'blocked_ips')
    def validate_ip_addresses(cls, v):
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:/\d{1,2})?$'
        )
        for ip in v:
            if not ip_pattern.match(ip):
                raise ValueError(f'Invalid IP address or CIDR: {ip}')
        return v

class APIKeyRequest(BaseModel):
    """Request to generate API key"""
    user_id: str
    name: str = Field(..., min_length=3, max_length=100)
    permissions: List[str] = Field(default=[], description="List of permissions for this API key")
    expires_in_days: int = Field(default=90, ge=1, le=365)

class SessionSecurityRequest(BaseModel):
    """Request for session security settings"""
    tenant_id: str
    session_timeout_hours: int = Field(default=8, ge=1, le=24)
    idle_timeout_minutes: int = Field(default=30, ge=5, le=120)
    require_device_verification: bool = True
    max_concurrent_sessions: int = Field(default=3, ge=1, le=10)

# Response Models
class MFASetupResponse(BaseModel):
    """MFA setup response"""
    user_id: str
    method: str
    secret_key: Optional[str] = None
    qr_code_url: Optional[str] = None
    backup_codes: List[str]
    setup_complete: bool

class SecurityAuditResponse(BaseModel):
    """Security audit response"""
    tenant_id: str
    audit_period: str
    security_events: List[Dict[str, Any]]
    risk_summary: Dict[str, Any]
    recommendations: List[str]
    compliance_score: float

class ThreatDetectionResponse(BaseModel):
    """Threat detection response"""
    threats_detected: List[Dict[str, Any]]
    risk_level: str
    automated_actions: List[str]
    manual_review_required: List[str]

# Router
router = APIRouter(prefix="/advanced-security", tags=["Advanced Security"])
security = HTTPBearer()

class AdvancedSecurityManager:
    """Advanced security management system"""
    
    def __init__(self):
        self.jwt_secret = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        self.security_events: List[SecurityEvent] = []
    
    async def generate_totp_secret(self, user_id: str) -> Dict[str, Any]:
        """Generate TOTP secret for MFA setup"""
        try:
            secret = pyotp.random_base32()
            
            # Store secret in database
            db = await get_database()
            await db.user_mfa.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "totp_secret": secret,
                        "method": "totp",
                        "enabled": False,
                        "backup_codes": [secrets.token_hex(4) for _ in range(10)],
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                },
                upsert=True
            )
            
            # Generate QR code URL
            totp = pyotp.TOTP(secret)
            qr_code_url = totp.provisioning_uri(
                name=user_id,
                issuer_name="Nexus Core"
            )
            
            return {
                "secret_key": secret,
                "qr_code_url": qr_code_url,
                "backup_codes": [secrets.token_hex(4) for _ in range(10)]
            }
            
        except Exception as e:
            logger.error(f"Error generating TOTP secret: {e}")
            raise HTTPException(status_code=500, detail="MFA setup failed")
    
    async def verify_totp_token(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            db = await get_database()
            mfa_data = await db.user_mfa.find_one({"user_id": user_id})
            
            if not mfa_data:
                return False
            
            totp = pyotp.TOTP(mfa_data["totp_secret"])
            is_valid = totp.verify(token, valid_window=1)  # Allow 30-second window
            
            if is_valid:
                # Update last used timestamp
                await db.user_mfa.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_used": datetime.utcnow().isoformat()}}
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {e}")
            return False
    
    async def generate_jwt_tokens(self, user_id: str, tenant_id: str, device_info: Dict) -> Dict[str, str]:
        """Generate access and refresh JWT tokens"""
        try:
            now = datetime.utcnow()
            
            # Access token (short-lived)
            access_payload = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "type": "access",
                "iat": now,
                "exp": now + timedelta(hours=1),
                "device_id": device_info.get("device_id")
            }
            
            # Refresh token (long-lived)
            refresh_payload = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "type": "refresh",
                "iat": now,
                "exp": now + timedelta(days=30),
                "device_id": device_info.get("device_id")
            }
            
            access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            # Store refresh token
            db = await get_database()
            await db.refresh_tokens.insert_one({
                "user_id": user_id,
                "tenant_id": tenant_id,
                "token_hash": hashlib.sha256(refresh_token.encode()).hexdigest(),
                "device_info": device_info,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(days=30)).isoformat(),
                "is_active": True
            })
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600
            }
            
        except Exception as e:
            logger.error(f"Error generating JWT tokens: {e}")
            raise HTTPException(status_code=500, detail="Token generation failed")
    
    async def validate_password_policy(self, password: str, policy: Dict) -> Dict[str, Any]:
        """Validate password against policy"""
        violations = []
        score = 100
        
        if len(password) < policy.get("min_length", 8):
            violations.append(f"Password must be at least {policy['min_length']} characters")
            score -= 20
        
        if policy.get("require_uppercase", True) and not re.search(r'[A-Z]', password):
            violations.append("Password must contain at least one uppercase letter")
            score -= 15
        
        if policy.get("require_lowercase", True) and not re.search(r'[a-z]', password):
            violations.append("Password must contain at least one lowercase letter")
            score -= 15
        
        if policy.get("require_numbers", True) and not re.search(r'[0-9]', password):
            violations.append("Password must contain at least one number")
            score -= 15
        
        if policy.get("require_symbols", True) and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            violations.append("Password must contain at least one special character")
            score -= 15
        
        # Check against common passwords
        common_passwords = ["password", "123456", "qwerty", "admin", "welcome"]
        if password.lower() in common_passwords:
            violations.append("Password is too common")
            score -= 30
        
        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "strength_score": max(0, score)
        }
    
    async def check_ip_restrictions(self, ip_address: str, tenant_id: str) -> Dict[str, Any]:
        """Check IP address against tenant restrictions"""
        try:
            db = await get_database()
            restrictions = await db.ip_restrictions.find_one({"tenant_id": tenant_id})
            
            if not restrictions:
                return {"allowed": True, "reason": "No restrictions configured"}
            
            # Check blocked IPs first
            for blocked_ip in restrictions.get("blocked_ips", []):
                if self._ip_matches_pattern(ip_address, blocked_ip):
                    return {"allowed": False, "reason": f"IP {ip_address} is blocked"}
            
            # Check whitelist if required
            if restrictions.get("require_whitelist", False):
                allowed_ips = restrictions.get("allowed_ips", [])
                if not any(self._ip_matches_pattern(ip_address, allowed_ip) for allowed_ip in allowed_ips):
                    return {"allowed": False, "reason": f"IP {ip_address} not in whitelist"}
            
            return {"allowed": True, "reason": "IP address allowed"}
            
        except Exception as e:
            logger.error(f"Error checking IP restrictions: {e}")
            return {"allowed": True, "reason": "Unable to verify restrictions"}
    
    def _ip_matches_pattern(self, ip: str, pattern: str) -> bool:
        """Check if IP matches pattern (supports CIDR)"""
        try:
            if '/' in pattern:
                # CIDR notation
                import ipaddress
                return ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)
            else:
                # Exact match or wildcard
                return ip == pattern or pattern == "*"
        except:
            return False
    
    async def generate_api_key(self, user_id: str, name: str, permissions: List[str], expires_days: int) -> Dict[str, Any]:
        """Generate secure API key"""
        try:
            # Generate API key
            api_key = f"nxs_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Store in database
            db = await get_database()
            key_data = {
                "user_id": user_id,
                "name": name,
                "key_hash": key_hash,
                "permissions": permissions,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
                "is_active": True,
                "last_used": None,
                "usage_count": 0
            }
            
            result = await db.api_keys.insert_one(key_data)
            
            return {
                "api_key": api_key,
                "key_id": str(result.inserted_id),
                "name": name,
                "permissions": permissions,
                "expires_at": key_data["expires_at"]
            }
            
        except Exception as e:
            logger.error(f"Error generating API key: {e}")
            raise HTTPException(status_code=500, detail="API key generation failed")
    
    async def detect_suspicious_activity(self, user_id: str, request_data: Dict) -> Dict[str, Any]:
        """AI-powered suspicious activity detection"""
        try:
            # Collect activity metrics
            recent_logins = await self._get_recent_logins(user_id)
            ip_changes = self._analyze_ip_changes(recent_logins)
            time_patterns = self._analyze_time_patterns(recent_logins)
            device_changes = self._analyze_device_changes(recent_logins)
            
            # Calculate risk score
            risk_score = 0
            risk_factors = []
            
            if ip_changes > 3:
                risk_score += 25
                risk_factors.append("Multiple IP addresses")
            
            if time_patterns["unusual_hours"]:
                risk_score += 15
                risk_factors.append("Unusual login times")
            
            if device_changes > 2:
                risk_score += 20
                risk_factors.append("Multiple devices")
            
            # High-frequency access
            if len(recent_logins) > 50:
                risk_score += 10
                risk_factors.append("High frequency access")
            
            # Determine threat level
            if risk_score >= 50:
                threat_level = "HIGH"
            elif risk_score >= 30:
                threat_level = "MEDIUM"
            elif risk_score >= 15:
                threat_level = "LOW"
            else:
                threat_level = "NORMAL"
            
            return {
                "risk_score": risk_score,
                "threat_level": threat_level,
                "risk_factors": risk_factors,
                "recommendations": self._generate_security_recommendations(risk_score, risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}")
            return {"risk_score": 0, "threat_level": "UNKNOWN", "risk_factors": []}
    
    async def _get_recent_logins(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get recent login activity"""
        try:
            db = await get_database()
            start_date = datetime.utcnow() - timedelta(days=days)
            
            logins = await db.security_events.find({
                "user_id": user_id,
                "event_type": "login",
                "timestamp": {"$gte": start_date.isoformat()}
            }).to_list(length=None)
            
            return logins
        except:
            return []
    
    def _analyze_ip_changes(self, logins: List[Dict]) -> int:
        """Analyze IP address changes"""
        unique_ips = set()
        for login in logins:
            if "ip_address" in login:
                unique_ips.add(login["ip_address"])
        return len(unique_ips)
    
    def _analyze_time_patterns(self, logins: List[Dict]) -> Dict[str, Any]:
        """Analyze login time patterns"""
        unusual_hours = 0
        hours = []
        
        for login in logins:
            try:
                login_time = datetime.fromisoformat(login.get("timestamp", ""))
                hour = login_time.hour
                hours.append(hour)
                
                # Consider 11 PM - 6 AM as unusual
                if hour >= 23 or hour <= 6:
                    unusual_hours += 1
            except:
                continue
        
        return {
            "unusual_hours": unusual_hours > len(logins) * 0.3,  # More than 30% unusual
            "hours_distribution": hours
        }
    
    def _analyze_device_changes(self, logins: List[Dict]) -> int:
        """Analyze device changes"""
        unique_devices = set()
        for login in logins:
            user_agent = login.get("details", {}).get("user_agent", "")
            if user_agent:
                unique_devices.add(user_agent)
        return len(unique_devices)
    
    def _generate_security_recommendations(self, risk_score: int, risk_factors: List[str]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if risk_score >= 50:
            recommendations.append("Require immediate password reset")
            recommendations.append("Enable multi-factor authentication")
            recommendations.append("Review all active sessions")
        
        if "Multiple IP addresses" in risk_factors:
            recommendations.append("Consider IP restrictions for this user")
        
        if "Unusual login times" in risk_factors:
            recommendations.append("Set up login time restrictions")
        
        if "Multiple devices" in risk_factors:
            recommendations.append("Limit concurrent sessions")
        
        if not recommendations:
            recommendations.append("Continue monitoring user activity")
        
        return recommendations

# Global security manager instance
security_manager = AdvancedSecurityManager()

# API Endpoints
@router.get("/health", summary="Security system health check")
async def get_security_health():
    """Get health status of the security system"""
    try:
        jwt_configured = bool(security_manager.jwt_secret)
        db = await get_database()
        
        # Test database connectivity
        await db.command("ping")
        
        return {
            "status": "healthy",
            "components": {
                "jwt_service": "healthy" if jwt_configured else "not_configured",
                "mfa_service": "healthy",
                "password_policies": "healthy",
                "threat_detection": "healthy",
                "database": "healthy"
            },
            "supported_auth_methods": [method.value for method in AuthMethod],
            "security_levels": [level.value for level in SecurityLevel],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/mfa/setup", response_model=MFASetupResponse, summary="Setup multi-factor authentication")
async def setup_mfa(request: MFASetupRequest):
    """Setup MFA for a user"""
    try:
        if request.method == AuthMethod.MFA_TOTP:
            setup_data = await security_manager.generate_totp_secret(request.user_id)
            
            return MFASetupResponse(
                user_id=request.user_id,
                method=request.method.value,
                secret_key=setup_data["secret_key"],
                qr_code_url=setup_data["qr_code_url"],
                backup_codes=setup_data["backup_codes"],
                setup_complete=True
            )
        else:
            raise HTTPException(status_code=400, detail="MFA method not supported yet")
            
    except Exception as e:
        logger.error(f"Error setting up MFA: {e}")
        raise HTTPException(status_code=500, detail=f"MFA setup failed: {str(e)}")

@router.post("/mfa/verify", summary="Verify MFA token")
async def verify_mfa(request: MFAVerificationRequest):
    """Verify MFA token"""
    try:
        if request.method == AuthMethod.MFA_TOTP:
            is_valid = await security_manager.verify_totp_token(request.user_id, request.token)
            
            return {
                "user_id": request.user_id,
                "method": request.method.value,
                "verified": is_valid,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="MFA method not supported")
            
    except Exception as e:
        logger.error(f"Error verifying MFA: {e}")
        raise HTTPException(status_code=500, detail=f"MFA verification failed: {str(e)}")

@router.post("/password-policy", summary="Set password policy for tenant")
async def set_password_policy(request: PasswordPolicyRequest):
    """Configure password policy for tenant"""
    try:
        db = await get_database()
        
        policy_data = {
            "tenant_id": request.tenant_id,
            "min_length": request.min_length,
            "require_uppercase": request.require_uppercase,
            "require_lowercase": request.require_lowercase,
            "require_numbers": request.require_numbers,
            "require_symbols": request.require_symbols,
            "max_age_days": request.max_age_days,
            "prevent_reuse": request.prevent_reuse,
            "lockout_attempts": request.lockout_attempts,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await db.password_policies.update_one(
            {"tenant_id": request.tenant_id},
            {"$set": policy_data},
            upsert=True
        )
        
        return {
            "tenant_id": request.tenant_id,
            "policy_updated": True,
            "policy": policy_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error setting password policy: {e}")
        raise HTTPException(status_code=500, detail=f"Password policy update failed: {str(e)}")

@router.post("/ip-restrictions", summary="Configure IP restrictions for tenant")
async def set_ip_restrictions(request: IPRestrictionsRequest):
    """Configure IP access restrictions for tenant"""
    try:
        db = await get_database()
        
        restrictions_data = {
            "tenant_id": request.tenant_id,
            "allowed_ips": request.allowed_ips,
            "blocked_ips": request.blocked_ips,
            "require_whitelist": request.require_whitelist,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await db.ip_restrictions.update_one(
            {"tenant_id": request.tenant_id},
            {"$set": restrictions_data},
            upsert=True
        )
        
        return {
            "tenant_id": request.tenant_id,
            "restrictions_updated": True,
            "restrictions": {
                "allowed_ips_count": len(request.allowed_ips),
                "blocked_ips_count": len(request.blocked_ips),
                "whitelist_required": request.require_whitelist
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error setting IP restrictions: {e}")
        raise HTTPException(status_code=500, detail=f"IP restrictions update failed: {str(e)}")

@router.post("/api-keys/generate", summary="Generate secure API key")
async def generate_api_key(request: APIKeyRequest):
    """Generate new API key with permissions"""
    try:
        api_key_data = await security_manager.generate_api_key(
            user_id=request.user_id,
            name=request.name,
            permissions=request.permissions,
            expires_days=request.expires_in_days
        )
        
        return {
            "key_generated": True,
            "api_key": api_key_data["api_key"],
            "key_id": api_key_data["key_id"],
            "name": api_key_data["name"],
            "permissions": api_key_data["permissions"],
            "expires_at": api_key_data["expires_at"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise HTTPException(status_code=500, detail=f"API key generation failed: {str(e)}")

@router.get("/threat-detection/{user_id}", response_model=ThreatDetectionResponse, summary="Analyze user threat level")
async def analyze_user_threats(user_id: str, request: Request):
    """Analyze user for suspicious activity and threats"""
    try:
        request_data = {
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        threat_analysis = await security_manager.detect_suspicious_activity(user_id, request_data)
        
        # Determine automated actions
        automated_actions = []
        manual_review = []
        
        if threat_analysis["threat_level"] == "HIGH":
            automated_actions.append("Session termination recommended")
            automated_actions.append("Password reset required")
            manual_review.append("Investigate user account immediately")
        elif threat_analysis["threat_level"] == "MEDIUM":
            automated_actions.append("Additional authentication required")
            manual_review.append("Review user activity patterns")
        
        return ThreatDetectionResponse(
            threats_detected=[{
                "user_id": user_id,
                "risk_score": threat_analysis["risk_score"],
                "threat_level": threat_analysis["threat_level"],
                "risk_factors": threat_analysis["risk_factors"],
                "timestamp": request_data["timestamp"]
            }],
            risk_level=threat_analysis["threat_level"],
            automated_actions=automated_actions,
            manual_review_required=manual_review
        )
        
    except Exception as e:
        logger.error(f"Error analyzing user threats: {e}")
        raise HTTPException(status_code=500, detail=f"Threat analysis failed: {str(e)}")

@router.get("/audit/{tenant_id}", response_model=SecurityAuditResponse, summary="Generate security audit report")
async def generate_security_audit(tenant_id: str, days: int = 30):
    """Generate comprehensive security audit report"""
    try:
        db = await get_database()
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get security events
        security_events = await db.security_events.find({
            "tenant_id": tenant_id,
            "timestamp": {"$gte": start_date.isoformat()}
        }).to_list(length=None)
        
        # Analyze events
        login_attempts = len([e for e in security_events if e.get("event_type") == "login"])
        failed_logins = len([e for e in security_events if e.get("event_type") == "login_failed"])
        mfa_events = len([e for e in security_events if "mfa" in e.get("event_type", "")])
        
        # Calculate compliance score
        compliance_score = 100
        if failed_logins > login_attempts * 0.1:  # More than 10% failed logins
            compliance_score -= 15
        
        if mfa_events < login_attempts * 0.5:  # Less than 50% MFA usage
            compliance_score -= 20
        
        recommendations = []
        if failed_logins > 10:
            recommendations.append("Consider implementing account lockout policies")
        if mfa_events == 0:
            recommendations.append("Enable multi-factor authentication for all users")
        
        return SecurityAuditResponse(
            tenant_id=tenant_id,
            audit_period=f"{days}_days",
            security_events=[
                {
                    "event_type": event.get("event_type"),
                    "timestamp": event.get("timestamp"),
                    "user_id": event.get("user_id"),
                    "details": event.get("details", {})
                }
                for event in security_events[-50:]  # Last 50 events
            ],
            risk_summary={
                "total_events": len(security_events),
                "login_attempts": login_attempts,
                "failed_logins": failed_logins,
                "mfa_usage": mfa_events,
                "failure_rate": (failed_logins / max(1, login_attempts)) * 100
            },
            recommendations=recommendations or ["Security posture is good"],
            compliance_score=max(0, compliance_score)
        )
        
    except Exception as e:
        logger.error(f"Error generating security audit: {e}")
        raise HTTPException(status_code=500, detail=f"Security audit failed: {str(e)}")

@router.post("/sessions/security", summary="Configure session security settings")
async def configure_session_security(request: SessionSecurityRequest):
    """Configure session security settings for tenant"""
    try:
        db = await get_database()
        
        session_config = {
            "tenant_id": request.tenant_id,
            "session_timeout_hours": request.session_timeout_hours,
            "idle_timeout_minutes": request.idle_timeout_minutes,
            "require_device_verification": request.require_device_verification,
            "max_concurrent_sessions": request.max_concurrent_sessions,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await db.session_security.update_one(
            {"tenant_id": request.tenant_id},
            {"$set": session_config},
            upsert=True
        )
        
        return {
            "tenant_id": request.tenant_id,
            "session_security_updated": True,
            "configuration": session_config,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error configuring session security: {e}")
        raise HTTPException(status_code=500, detail=f"Session security configuration failed: {str(e)}")

@router.get("/security-overview/{tenant_id}", summary="Get comprehensive security overview")
async def get_security_overview(tenant_id: str):
    """Get comprehensive security overview for tenant"""
    try:
        db = await get_database()
        
        # Get policy information
        password_policy = await db.password_policies.find_one({"tenant_id": tenant_id}) or {}
        ip_restrictions = await db.ip_restrictions.find_one({"tenant_id": tenant_id}) or {}
        session_security = await db.session_security.find_one({"tenant_id": tenant_id}) or {}
        
        # Get MFA status
        mfa_users = await db.user_mfa.count_documents({"tenant_id": tenant_id, "enabled": True})
        total_users = await db.users.count_documents({"tenant_id": tenant_id})
        
        # Get API keys
        active_api_keys = await db.api_keys.count_documents({
            "tenant_id": tenant_id, 
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow().isoformat()}
        })
        
        return {
            "tenant_id": tenant_id,
            "security_overview": {
                "password_policy_configured": bool(password_policy),
                "ip_restrictions_enabled": bool(ip_restrictions.get("require_whitelist", False)),
                "mfa_adoption_rate": (mfa_users / max(1, total_users)) * 100,
                "active_api_keys": active_api_keys,
                "session_security_configured": bool(session_security)
            },
            "policy_summary": {
                "password_requirements": {
                    "min_length": password_policy.get("min_length", 8),
                    "complexity_required": password_policy.get("require_uppercase", True),
                    "max_age_days": password_policy.get("max_age_days", 90)
                },
                "access_controls": {
                    "ip_whitelist_required": ip_restrictions.get("require_whitelist", False),
                    "allowed_ips_count": len(ip_restrictions.get("allowed_ips", [])),
                    "blocked_ips_count": len(ip_restrictions.get("blocked_ips", []))
                },
                "session_controls": {
                    "timeout_hours": session_security.get("session_timeout_hours", 8),
                    "max_concurrent": session_security.get("max_concurrent_sessions", 3),
                    "device_verification": session_security.get("require_device_verification", True)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting security overview: {e}")
        raise HTTPException(status_code=500, detail=f"Security overview failed: {str(e)}")