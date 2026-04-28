"""
Jira integration for the Meeting Intelligence Agent.
Creates and manages Jira issues from action items.
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    from jira import JIRA
    HAS_JIRA = True
except ImportError:
    HAS_JIRA = False


@dataclass
class JiraIssue:
    """Jira issue data."""
    key: str
    summary: str
    description: str
    status: str
    assignee: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'summary': self.summary,
            'description': self.description,
            'status': self.status,
            'assignee': self.assignee,
            'priority': self.priority,
            'due_date': self.due_date,
            'url': self.url
        }


class JiraIntegration:
    """
    Integration with Jira for creating issues from action items.
    """
    
    PRIORITY_MAP = {
        'critical': 'Highest',
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low'
    }
    
    def __init__(
        self,
        url: str,
        email: str,
        api_token: str,
        project_key: str = "MEET",
        default_issue_type: str = "Task"
    ):
        """
        Initialize Jira integration.
        
        Args:
            url: Jira instance URL
            email: Jira user email
            api_token: Jira API token
            project_key: Default project key
            default_issue_type: Default issue type
        """
        if not HAS_JIRA:
            raise ImportError("jira package is required for Jira integration")
        
        self.url = url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        self.default_issue_type = default_issue_type
        
        self._client: Optional[JIRA] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to Jira."""
        try:
            self._client = JIRA(
                server=self.url,
                basic_auth=(self.email, self.api_token)
            )
            # Test connection
            self._client.myself()
            self._connected = True
            logger.info(f"Connected to Jira: {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Jira."""
        return self._connected and self._client is not None
    
    def create_issue(
        self,
        summary: str,
        description: str,
        assignee: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[datetime] = None,
        labels: Optional[List[str]] = None,
        issue_type: Optional[str] = None,
        project_key: Optional[str] = None
    ) -> Optional[JiraIssue]:
        """
        Create a Jira issue.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            assignee: Assignee email or account ID
            priority: Priority level
            due_date: Due date
            labels: Issue labels
            issue_type: Issue type (Task, Story, Bug, etc.)
            project_key: Project key
            
        Returns:
            JiraIssue if created successfully
        """
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            # Build issue fields
            fields = {
                'project': {'key': project_key or self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type or self.default_issue_type}
            }
            
            # Add priority
            jira_priority = self.PRIORITY_MAP.get(priority.lower(), 'Medium')
            fields['priority'] = {'name': jira_priority}
            
            # Add due date
            if due_date:
                fields['duedate'] = due_date.strftime('%Y-%m-%d')
            
            # Add labels
            if labels:
                fields['labels'] = labels
            
            # Create issue
            issue = self._client.create_issue(fields=fields)
            
            # Assign if specified
            if assignee:
                try:
                    self._client.assign_issue(issue, assignee)
                except Exception as e:
                    logger.warning(f"Could not assign issue to {assignee}: {e}")
            
            result = JiraIssue(
                key=issue.key,
                summary=summary,
                description=description,
                status=str(issue.fields.status),
                assignee=assignee,
                priority=priority,
                due_date=due_date.strftime('%Y-%m-%d') if due_date else None,
                url=f"{self.url}/browse/{issue.key}"
            )
            
            logger.info(f"Created Jira issue: {issue.key}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return None
    
    def create_from_action_item(
        self,
        action_item: Dict[str, Any],
        meeting_title: Optional[str] = None
    ) -> Optional[JiraIssue]:
        """
        Create a Jira issue from an action item.
        
        Args:
            action_item: Action item dictionary
            meeting_title: Optional meeting title for context
            
        Returns:
            JiraIssue if created
        """
        # Build description
        description_parts = [action_item.get('description', '')]
        
        if action_item.get('source_quote'):
            description_parts.append(f"\n*Source:* {action_item['source_quote']}")
        
        if meeting_title:
            description_parts.append(f"\n*Meeting:* {meeting_title}")
        
        if action_item.get('meeting_id'):
            description_parts.append(f"\n*Meeting ID:* {action_item['meeting_id']}")
        
        description = "\n".join(description_parts)
        
        # Parse deadline
        deadline = None
        if action_item.get('deadline'):
            if isinstance(action_item['deadline'], str):
                try:
                    deadline = datetime.fromisoformat(action_item['deadline'])
                except:
                    pass
            else:
                deadline = action_item['deadline']
        
        # Create issue
        return self.create_issue(
            summary=action_item.get('description', 'Action Item'),
            description=description,
            assignee=action_item.get('assignee'),
            priority=action_item.get('priority', 'medium'),
            due_date=deadline,
            labels=['meeting-action-item'] + action_item.get('tags', [])
        )
    
    def create_batch(
        self,
        action_items: List[Dict[str, Any]],
        meeting_title: Optional[str] = None
    ) -> List[JiraIssue]:
        """
        Create multiple Jira issues from action items.
        
        Args:
            action_items: List of action items
            meeting_title: Meeting title for context
            
        Returns:
            List of created JiraIssue objects
        """
        created = []
        for item in action_items:
            issue = self.create_from_action_item(item, meeting_title)
            if issue:
                created.append(issue)
        
        logger.info(f"Created {len(created)} Jira issues")
        return created
    
    def update_issue_status(
        self,
        issue_key: str,
        status: str
    ) -> bool:
        """
        Update an issue's status.
        
        Args:
            issue_key: Issue key (e.g., "MEET-123")
            status: Target status name
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            issue = self._client.issue(issue_key)
            
            # Find transition
            transitions = self._client.transitions(issue)
            for t in transitions:
                if t['name'].lower() == status.lower():
                    self._client.transition_issue(issue, t['id'])
                    logger.info(f"Updated {issue_key} status to {status}")
                    return True
            
            logger.warning(f"Status '{status}' not found for {issue_key}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update issue status: {e}")
            return False
    
    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Get an issue by key."""
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            issue = self._client.issue(issue_key)
            return JiraIssue(
                key=issue.key,
                summary=issue.fields.summary,
                description=issue.fields.description or "",
                status=str(issue.fields.status),
                assignee=str(issue.fields.assignee) if issue.fields.assignee else None,
                priority=str(issue.fields.priority) if issue.fields.priority else None,
                due_date=str(issue.fields.duedate) if issue.fields.duedate else None,
                url=f"{self.url}/browse/{issue.key}"
            )
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {e}")
            return None
    
    def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[JiraIssue]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum results to return
            
        Returns:
            List of matching issues
        """
        if not self.is_connected:
            if not self.connect():
                return []
        
        try:
            issues = self._client.search_issues(jql, maxResults=max_results)
            return [
                JiraIssue(
                    key=issue.key,
                    summary=issue.fields.summary,
                    description=issue.fields.description or "",
                    status=str(issue.fields.status),
                    url=f"{self.url}/browse/{issue.key}"
                )
                for issue in issues
            ]
        except Exception as e:
            logger.error(f"Failed to search issues: {e}")
            return []
    
    def get_meeting_actions(self, meeting_id: str) -> List[JiraIssue]:
        """Get Jira issues created from a meeting."""
        jql = f'labels = "meeting-action-item" AND description ~ "{meeting_id}"'
        return self.search_issues(jql)
    
    def list_projects(self) -> List[Dict[str, str]]:
        """List available Jira projects."""
        if not self.is_connected:
            if not self.connect():
                return []
        
        try:
            projects = self._client.projects()
            return [
                {'key': p.key, 'name': p.name}
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []


def get_jira_integration(
    url: Optional[str] = None,
    email: Optional[str] = None,
    api_token: Optional[str] = None,
    project_key: str = "MEET"
) -> Optional[JiraIntegration]:
    """
    Get a Jira integration instance.
    
    Uses environment variables if not provided:
    - JIRA_URL
    - JIRA_EMAIL
    - JIRA_API_TOKEN
    """
    url = url or os.getenv("JIRA_URL", "")
    email = email or os.getenv("JIRA_EMAIL", "")
    api_token = api_token or os.getenv("JIRA_API_TOKEN", "")
    
    if not all([url, email, api_token]):
        logger.warning("Jira credentials not configured")
        return None
    
    try:
        integration = JiraIntegration(
            url=url,
            email=email,
            api_token=api_token,
            project_key=project_key
        )
        return integration
    except ImportError:
        logger.warning("Jira package not installed")
        return None
