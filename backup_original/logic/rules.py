#!/usr/bin/env python3

from typing import Dict, Any, List, Tuple, Optional
import logging

from .models import Rule, RuleCondition
from ..utils.logging import get_logger

logger = get_logger(__name__)

class RuleEngine:
    def __init__(self, rules_config: Dict[str, Any]):
        self.rules_config = rules_config
        self.rules: List[Rule] = []
        self._load_rules()
    
    def _load_rules(self):
        rules_data = self.rules_config.get("rules", [])
        for rule_data in rules_data:
            try:
                rule = Rule(**rule_data)
                self.rules.append(rule)
                logger.info(f"Loaded rule: {rule.name}")
            except Exception as e:
                logger.error(f"Failed to load rule: {str(e)}")
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[str, str]:
        reasoning_chain = []
        
        for rule in self.rules:
            try:
                if rule.jurisdiction and rule.jurisdiction != context.get("jurisdiction"):
                    continue
                
                result = self._evaluate_rule(rule, context)
                reasoning_chain.append(f"Rule '{rule.name}': {result['reason']}")
                
                if result['matched']:
                    action = rule.action
                    if action == "GRANT_YES":
                        return "YES", " | ".join(reasoning_chain)
                    elif action == "GRANT_NO":
                        return "NO", " | ".join(reasoning_chain)
                    elif action == "NO_DECISION":
                        return "NO", " | ".join(reasoning_chain)
                        
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
                reasoning_chain.append(f"Rule '{rule.name}': Error - {str(e)}")
        
        return "NO", " | ".join(reasoning_chain) if reasoning_chain else "No applicable rules found"
    
    def _evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> Dict[str, Any]:
        conditions = rule.conditions
        
        if "AND" in conditions:
            result = self._evaluate_and_conditions(conditions["AND"], context)
            if result['matched']:
                return {
                    'matched': True,
                    'reason': rule.reason_pass or f"All AND conditions passed for rule '{rule.name}'"
                }
            else:
                return {
                    'matched': False,
                    'reason': rule.reason_fail or f"AND condition failed: {result['reason']}"
                }
        
        elif "OR" in conditions:
            result = self._evaluate_or_conditions(conditions["OR"], context)
            if result['matched']:
                return {
                    'matched': True,
                    'reason': rule.reason_pass or f"OR condition passed for rule '{rule.name}'"
                }
            else:
                return {
                    'matched': False,
                    'reason': rule.reason_fail or f"All OR conditions failed for rule '{rule.name}'"
                }
        
        else:
            return {
                'matched': False,
                'reason': f"Invalid rule structure for rule '{rule.name}'"
            }
    
    def _evaluate_and_conditions(self, conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        for condition in conditions:
            result = self._evaluate_condition(condition, context)
            if not result['matched']:
                return result
        
        return {'matched': True, 'reason': "All AND conditions passed"}
    
    def _evaluate_or_conditions(self, conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        for condition in conditions:
            result = self._evaluate_condition(condition, context)
            if result['matched']:
                return result
        
        return {'matched': False, 'reason': "All OR conditions failed"}
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        fact = condition.get('fact')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if fact not in context:
            return {
                'matched': False,
                'reason': f"Fact '{fact}' not found in context"
            }
        
        actual_value = context[fact]
        
        try:
            if operator == "EQUALS":
                matched = actual_value == value
            elif operator == "NOT_EQUALS":
                matched = actual_value != value
            elif operator == "GREATER_THAN":
                matched = actual_value > value
            elif operator == "LESS_THAN":
                matched = actual_value < value
            elif operator == "GREATER_THAN_OR_EQUAL_TO":
                matched = actual_value >= value
            elif operator == "LESS_THAN_OR_EQUAL_TO":
                matched = actual_value <= value
            elif operator == "IN":
                matched = actual_value in value if isinstance(value, (list, tuple)) else False
            elif operator == "NOT_IN":
                matched = actual_value not in value if isinstance(value, (list, tuple)) else False
            elif operator == "CONTAINS":
                matched = value in actual_value if isinstance(actual_value, (list, tuple, str)) else False
            elif operator == "NOT_CONTAINS":
                matched = value not in actual_value if isinstance(actual_value, (list, tuple, str)) else False
            else:
                return {
                    'matched': False,
                    'reason': f"Unknown operator: {operator}"
                }
            
            return {
                'matched': matched,
                'reason': f"Condition {fact} {operator} {value} = {matched}"
            }
            
        except Exception as e:
            return {
                'matched': False,
                'reason': f"Error evaluating condition: {str(e)}"
            }
