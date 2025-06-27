from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
import logging
from collections import defaultdict
import asyncio

from core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class DocumentationSource:
    """Represents a documentation source for quality analysis"""
    title: str
    content: str
    url: str
    source_type: str  # azure_devops, confluence, sharepoint, github, etc.
    last_updated: Optional[datetime] = None
    authority_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "url": self.url,
            "source_type": self.source_type,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "authority_score": self.authority_score
        }

@dataclass
class InformationConflict:
    """Represents a detected information conflict between sources"""
    topic: str
    conflicting_sources: List[Dict[str, Any]]
    conflict_type: str  # "missing_info", "contradictory", "outdated"
    confidence: float
    resolution_suggestion: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return asdict(self)

@dataclass 
class QualityScore:
    """Represents quality assessment for information sources"""
    authority_score: float  # Based on source type
    completeness_score: float  # Based on information richness
    freshness_score: float  # Based on last update time
    cross_reference_score: float  # Based on corroboration
    overall_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return asdict(self)

class InformationQualityAnalyzer:
    """
    Advanced service that analyzes documentation quality and detects information conflicts.
    Addresses the "fire and forget" documentation problem by cross-referencing information
    and ensuring the AI is not satisfied with outdated information.
    """
    
    def __init__(self):
        # Source authority scores based on type (from configuration)
        self.source_authority = {
            'azure_devops': settings.SOURCE_AUTHORITY_AZURE_DEVOPS,
            'confluence': settings.SOURCE_AUTHORITY_CONFLUENCE,
            'sharepoint': settings.SOURCE_AUTHORITY_SHAREPOINT,
            'github': settings.SOURCE_AUTHORITY_GITHUB,
            'docs': settings.SOURCE_AUTHORITY_DOCS,
            'unknown': settings.SOURCE_AUTHORITY_UNKNOWN
        }
        
        # Team member extraction patterns
        self.team_patterns = [
            r'(?:team\s+)?members?:\s*([^.\n]+)',
            r'(?:team\s+)?lead:\s*([^.\n]+)',
            r'(?:contact|responsible):\s*([^.\n]+)',
            r'staff:\s*([^.\n]+)',
            r'people:\s*([^.\n]+)',
            r'engineers?:\s*([^.\n]+)',
            r'developers?:\s*([^.\n]+)',
        ]
        
        # Email pattern for team identification
        self.email_pattern = r'\b([a-zA-Z0-9._%+-]+)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        
        # Name patterns (assuming Western names)
        self.name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
    
    async def analyze_information_quality(
        self, 
        sources: List[DocumentationSource], 
        query: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method to analyze information quality and detect conflicts.
        
        Args:
            sources: List of documentation sources to analyze
            query: Original user query for context
            session_id: Session ID for logging/debugging
            
        Returns:
            Dictionary containing quality analysis, conflicts, and recommendations
        """
        try:
            logger.info(f"🔍 Analyzing information quality for {len(sources)} sources (session: {session_id})")
            
            if not settings.QUALITY_ANALYSIS_ENABLED:
                logger.info("Quality analysis disabled by configuration")
                return self._get_disabled_response(sources)
            
            # Step 1: Extract structured information from sources
            structured_info = await self._extract_structured_information(sources, query)
            
            # Step 2: Detect conflicts between sources
            conflicts = await self._detect_conflicts(sources, structured_info, query)
            
            # Step 3: Calculate quality scores for each source
            quality_scores = await self._score_information_quality(sources, structured_info)
            
            # Step 4: Generate overall assessment
            overall_assessment = self._generate_overall_assessment(sources, conflicts, quality_scores)
            
            # Step 5: Create user-friendly feedback
            user_feedback = self._generate_user_feedback(conflicts, quality_scores, len(sources))
            
            return {
                "quality_analysis": {
                    "sources_analyzed": len(sources),
                    "conflicts_detected": len(conflicts),
                    "overall_confidence": overall_assessment["confidence"],
                    "quality_scores": {f"source_{i}": v.to_dict() for i, v in enumerate(quality_scores.values())},
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "conflicts": [conflict.to_dict() for conflict in conflicts],
                "overall_assessment": overall_assessment,
                "user_feedback": user_feedback,
                "ai_guidance": self._generate_ai_guidance(conflicts, quality_scores, overall_assessment)
            }
            
        except Exception as e:
            logger.error(f"Error in information quality analysis: {str(e)}", exc_info=True)
            return {
                "quality_analysis": {"error": str(e), "sources_analyzed": len(sources)},
                "conflicts": [],
                "overall_assessment": {"confidence": 0.5},
                "user_feedback": {"status": "error", "message": "Quality analysis failed"},
                "ai_guidance": {"enhanced_prompt": "", "warnings": ["Quality analysis failed"]}
            }
    
    def _get_disabled_response(self, sources: List[DocumentationSource]) -> Dict[str, Any]:
        """Return response when quality analysis is disabled"""
        return {
            "quality_analysis": {
                "sources_analyzed": len(sources),
                "conflicts_detected": 0,
                "overall_confidence": 0.8,
                "enabled": False
            },
            "conflicts": [],
            "overall_assessment": {"confidence": 0.8},
            "user_feedback": {"status": "disabled", "message": "Quality analysis disabled"},
            "ai_guidance": {"enhanced_prompt": "", "warnings": []}
        }
    
    async def _extract_structured_information(
        self, 
        sources: List[DocumentationSource], 
        query: str
    ) -> Dict[str, Any]:
        """Extract structured information from sources for conflict detection."""
        
        structured = {
            "team_info": {},
            "contact_info": {},
            "process_info": {},
            "technical_info": {},
            "general_entities": {}
        }
        
        # Determine query type for focused extraction
        query_lower = query.lower()
        is_team_query = any(term in query_lower for term in ['team', 'member', 'who', 'staff', 'people'])
        
        for i, source in enumerate(sources):
            source_id = f"source_{i}"
            
            # Extract team information if relevant
            if is_team_query:
                team_info = self._extract_team_information(source.content, source)
                if team_info:
                    structured["team_info"][source_id] = team_info
            
            # Extract contact information
            contacts = self._extract_contact_information(source.content)
            if contacts:
                structured["contact_info"][source_id] = contacts
            
            # Extract general entities (organizations, tools, processes)
            entities = self._extract_general_entities(source.content, query)
            if entities:
                structured["general_entities"][source_id] = entities
        
        return structured
    
    def _extract_team_information(self, content: str, source: DocumentationSource) -> Dict[str, Any]:
        """Extract team member information from content."""
        
        team_info = {
            "members": [],
            "leads": [],
            "contacts": [],
            "roles": {},
            "emails": [],
            "source_metadata": {
                "title": source.title,
                "url": source.url,
                "last_updated": source.last_updated.isoformat() if source.last_updated else None
            }
        }
        
        # Extract emails first
        emails = re.findall(self.email_pattern, content)
        team_info["emails"] = emails
        
        # Extract names using patterns
        for pattern in self.team_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                text = match.group(1).strip()
                
                # Extract individual names from the matched text
                names = re.findall(self.name_pattern, text)
                
                if "lead" in pattern.lower():
                    team_info["leads"].extend(names)
                else:
                    team_info["members"].extend(names)
        
        # Remove duplicates
        team_info["members"] = list(set(team_info["members"]))
        team_info["leads"] = list(set(team_info["leads"]))
        
        return team_info if team_info["members"] or team_info["leads"] or team_info["emails"] else None
    
    def _extract_contact_information(self, content: str) -> Dict[str, Any]:
        """Extract contact information from content."""
        contacts = {
            "emails": re.findall(self.email_pattern, content),
            "phone_numbers": re.findall(r'\b\d{3}-\d{3}-\d{4}\b', content),
            "slack_channels": re.findall(r'#[\w-]+', content)
        }
        return contacts if any(contacts.values()) else None
    
    def _extract_general_entities(self, content: str, query: str) -> Dict[str, Any]:
        """Extract general entities based on query context."""
        entities = {
            "systems": re.findall(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:System|Platform|Service)\b', content),
            "tools": re.findall(r'\b(?:Jenkins|Docker|Kubernetes|Git|Azure|AWS)\b', content, re.IGNORECASE),
            "processes": re.findall(r'\b(?:deployment|release|testing|monitoring)\s+process\b', content, re.IGNORECASE)
        }
        return entities if any(entities.values()) else None
    
    async def _detect_conflicts(
        self, 
        sources: List[DocumentationSource], 
        structured_info: Dict[str, Any], 
        query: str
    ) -> List[InformationConflict]:
        """Detect conflicts between information sources."""
        
        if not settings.CONFLICT_DETECTION_ENABLED:
            return []
        
        conflicts = []
        
        # Detect team information conflicts
        if structured_info["team_info"]:
            team_conflicts = await self._detect_team_conflicts(
                structured_info["team_info"], sources
            )
            conflicts.extend(team_conflicts)
        
        # Detect contact information conflicts
        if structured_info["contact_info"]:
            contact_conflicts = await self._detect_contact_conflicts(
                structured_info["contact_info"], sources
            )
            conflicts.extend(contact_conflicts)
        
        # Detect general entity conflicts
        if structured_info["general_entities"]:
            entity_conflicts = await self._detect_entity_conflicts(
                structured_info["general_entities"], sources
            )
            conflicts.extend(entity_conflicts)
        
        return conflicts
    
    async def _detect_team_conflicts(
        self, 
        team_sources: Dict[str, Dict[str, Any]], 
        sources: List[DocumentationSource]
    ) -> List[InformationConflict]:
        """Detect conflicts in team information across sources."""
        
        conflicts = []
        
        if len(team_sources) < 2:
            return conflicts
        
        # Collect all team members from all sources
        all_members = defaultdict(list)
        all_leads = defaultdict(list)
        
        for source_id, team_info in team_sources.items():
            source_idx = int(source_id.split('_')[1])
            source = sources[source_idx]
            
            for member in team_info.get("members", []):
                all_members[member].append((source_id, source))
            
            for lead in team_info.get("leads", []):
                all_leads[lead].append((source_id, source))
        
        # Detect missing team members
        source_ids = list(team_sources.keys())
        for i, source_id_a in enumerate(source_ids):
            for j, source_id_b in enumerate(source_ids[i+1:], i+1):
                members_a = set(team_sources[source_id_a].get("members", []))
                members_b = set(team_sources[source_id_b].get("members", []))
                
                missing_in_a = members_b - members_a
                missing_in_b = members_a - members_b
                
                if missing_in_a or missing_in_b:
                    source_a = sources[int(source_id_a.split('_')[1])]
                    source_b = sources[int(source_id_b.split('_')[1])]
                    
                    missing_names = list(missing_in_a) + list(missing_in_b)
                    
                    conflicts.append(InformationConflict(
                        topic="team_membership",
                        conflicting_sources=[source_a.to_dict(), source_b.to_dict()],
                        conflict_type="missing_info",
                        confidence=0.8,
                        resolution_suggestion=f"Some sources may have incomplete team information. Missing: {', '.join(missing_names)}"
                    ))
        
        return conflicts
    
    async def _detect_contact_conflicts(
        self, 
        contact_sources: Dict[str, Dict[str, Any]], 
        sources: List[DocumentationSource]
    ) -> List[InformationConflict]:
        """Detect conflicts in contact information."""
        # Implementation similar to team conflicts but for contact info
        return []  # Simplified for now
    
    async def _detect_entity_conflicts(
        self, 
        entity_sources: Dict[str, Dict[str, Any]], 
        sources: List[DocumentationSource]
    ) -> List[InformationConflict]:
        """Detect conflicts in general entity information."""
        # Implementation similar to team conflicts but for entities
        return []  # Simplified for now
    
    async def _score_information_quality(
        self, 
        sources: List[DocumentationSource], 
        structured_info: Dict[str, Any]
    ) -> Dict[str, QualityScore]:
        """Calculate quality scores for each source."""
        
        quality_scores = {}
        
        for i, source in enumerate(sources):
            source_id = f"source_{i}"
            
            # Authority score based on source type
            authority_score = self.source_authority.get(source.source_type, self.source_authority['unknown'])
            
            # Completeness score based on information richness
            completeness_score = self._calculate_completeness_score(source, structured_info, source_id)
            
            # Freshness score based on last update time
            freshness_score = self._calculate_freshness_score(source)
            
            # Cross-reference score based on corroboration with other sources
            cross_reference_score = self._calculate_cross_reference_score(
                source, sources, structured_info, source_id
            )
            
            # Calculate overall score (weighted average)
            overall_score = (
                authority_score * 0.3 +
                completeness_score * 0.25 +
                freshness_score * 0.25 +
                cross_reference_score * 0.2
            )
            
            quality_scores[source_id] = QualityScore(
                authority_score=authority_score,
                completeness_score=completeness_score,
                freshness_score=freshness_score,
                cross_reference_score=cross_reference_score,
                overall_score=overall_score
            )
        
        return quality_scores
    
    def _calculate_completeness_score(
        self, 
        source: DocumentationSource, 
        structured_info: Dict[str, Any], 
        source_id: str
    ) -> float:
        """Calculate completeness score based on information richness."""
        
        score = 0.5  # Base score
        
        # Check if source has team information
        if source_id in structured_info.get("team_info", {}):
            team_info = structured_info["team_info"][source_id]
            if team_info.get("members"):
                score += 0.2
            if team_info.get("leads"):
                score += 0.1
            if team_info.get("emails"):
                score += 0.1
        
        # Check content length and richness
        content_length = len(source.content)
        if content_length > 1000:
            score += 0.1
        elif content_length > 500:
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_freshness_score(self, source: DocumentationSource) -> float:
        """Calculate freshness score based on last update time."""
        
        if not source.last_updated:
            return 0.5  # Neutral score if no update time
        
        now = datetime.utcnow()
        time_diff = now - source.last_updated
        
        # Scoring based on age
        if time_diff.days <= 30:
            return 1.0  # Very fresh
        elif time_diff.days <= 90:
            return 0.8  # Moderately fresh
        elif time_diff.days <= 180:
            return 0.6  # Getting old
        elif time_diff.days <= 365:
            return 0.4  # Old
        else:
            return 0.2  # Very old
    
    def _calculate_cross_reference_score(
        self, 
        source: DocumentationSource, 
        all_sources: List[DocumentationSource], 
        structured_info: Dict[str, Any], 
        source_id: str
    ) -> float:
        """Calculate cross-reference score based on corroboration with other sources."""
        
        if len(all_sources) <= 1:
            return 0.5  # Neutral if no other sources to compare
        
        score = 0.5  # Base score
        
        # Check team information corroboration
        if source_id in structured_info.get("team_info", {}):
            team_info = structured_info["team_info"][source_id]
            members = set(team_info.get("members", []))
            
            # Check how many other sources mention the same team members
            corroborating_sources = 0
            for other_source_id, other_team_info in structured_info.get("team_info", {}).items():
                if other_source_id != source_id:
                    other_members = set(other_team_info.get("members", []))
                    if members & other_members:  # If there's overlap
                        corroborating_sources += 1
            
            if corroborating_sources > 0:
                score += 0.3 * min(corroborating_sources / (len(all_sources) - 1), 1.0)
        
        return min(score, 1.0)
    
    def _generate_overall_assessment(
        self, 
        sources: List[DocumentationSource], 
        conflicts: List[InformationConflict], 
        quality_scores: Dict[str, QualityScore]
    ) -> Dict[str, Any]:
        """Generate overall quality assessment."""
        
        if not quality_scores:
            return {"confidence": 0.5, "status": "no_analysis"}
        
        # Calculate average quality
        avg_quality = sum(score.overall_score for score in quality_scores.values()) / len(quality_scores)
        
        # Adjust for conflicts
        conflict_penalty = len(conflicts) * 0.1
        final_confidence = max(avg_quality - conflict_penalty, 0.1)
        
        return {
            "confidence": final_confidence,
            "average_quality": avg_quality,
            "conflict_count": len(conflicts),
            "source_count": len(sources),
            "status": "analyzed"
        }
    
    def _generate_user_feedback(
        self, 
        conflicts: List[InformationConflict], 
        quality_scores: Dict[str, QualityScore], 
        source_count: int
    ) -> Dict[str, Any]:
        """Generate user-friendly feedback about information quality."""
        
        if not quality_scores:
            return {"status": "no_feedback", "message": "No quality analysis available"}
        
        avg_quality = sum(score.overall_score for score in quality_scores.values()) / len(quality_scores)
        
        if avg_quality >= 0.8:
            status = "high_quality"
            message = f"✅ High quality sources detected (average: {avg_quality:.0%})"
        elif avg_quality >= 0.6:
            status = "moderate_quality"
            message = f"✅ Moderate quality sources detected (average: {avg_quality:.0%})"
        else:
            status = "low_quality"
            message = f"⚠️ Lower quality sources detected (average: {avg_quality:.0%})"
        
        feedback = {
            "status": status,
            "message": message,
            "source_count": source_count,
            "average_quality": avg_quality
        }
        
        if conflicts:
            feedback["conflicts"] = f"⚠️ Detected {len(conflicts)} information conflicts"
            feedback["conflict_details"] = [
                f"{conflict.topic}: {conflict.resolution_suggestion}" 
                for conflict in conflicts[:3]  # Show first 3
            ]
        
        return feedback
    
    def _generate_ai_guidance(
        self, 
        conflicts: List[InformationConflict], 
        quality_scores: Dict[str, QualityScore], 
        overall_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate guidance for AI response generation."""
        
        warnings = []
        enhanced_prompt = ""
        
        if conflicts:
            warnings.append(f"Information conflicts detected: {len(conflicts)}")
            enhanced_prompt += "\n\nINFORMATION QUALITY ANALYSIS:\n"
            enhanced_prompt += f"- Sources analyzed: {len(quality_scores)}\n"
            enhanced_prompt += f"- Information conflicts detected: {len(conflicts)}\n"
            enhanced_prompt += f"- Overall confidence: {overall_assessment.get('confidence', 0.5):.0%}\n\n"
            
            enhanced_prompt += "DETECTED CONFLICTS - HANDLE WITH CARE:\n"
            for conflict in conflicts[:3]:  # Show first 3 conflicts
                enhanced_prompt += f"- {conflict.topic}: {conflict.resolution_suggestion}\n"
            
            enhanced_prompt += "\nCONFLICT RESOLUTION GUIDANCE:\n"
            enhanced_prompt += "- Acknowledge when sources provide conflicting information\n"
            enhanced_prompt += "- Use phrases like 'According to [source], though other sources may have additional information...'\n"
            enhanced_prompt += "- Recommend verifying current information through official channels\n"
        
        confidence = overall_assessment.get("confidence", 0.5)
        if confidence < settings.LOW_QUALITY_WARNING_THRESHOLD:
            warnings.append("Low quality sources detected")
            enhanced_prompt += "\nQUALITY WARNING: Sources may be outdated or incomplete. Recommend verification.\n"
        
        return {
            "enhanced_prompt": enhanced_prompt,
            "warnings": warnings,
            "confidence": confidence,
            "should_warn_user": len(conflicts) > 0 or confidence < settings.CONFLICT_WARNING_THRESHOLD
        } 