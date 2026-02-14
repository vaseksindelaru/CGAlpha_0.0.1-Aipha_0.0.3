"""
cgalpha.codecraft - Code Craft Sage

Automated code modification system for CGAlpha.
Converts natural language proposals to executable code changes.
"""

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType
from cgalpha.codecraft.proposal_parser import ProposalParser
from cgalpha.codecraft.ast_modifier import ASTModifier
from cgalpha.codecraft.safety_validator import SafetyValidator

__all__ = [
    "TechnicalSpec",
    "ChangeType",
    "ProposalParser",
    "ASTModifier",
    "SafetyValidator",
]

__version__ = "0.2.0-phase2"
