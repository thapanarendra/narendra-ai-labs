"""
Asana integration for the Meeting Intelligence Agent.
Creates and manages Asana tasks from action items.
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    import asana
    HAS_ASANA = True
except ImportError:
    HAS_ASANA = False


@dataclass
class AsanaTask:
    """Asana task data."""
    gid: str
    name: str
    notes: str
    completed: bool
    assignee: Optional[str] = None
    due_on: Optional[str] = None
    url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'gid': self.gid,
            'name': self.name,
            'notes': self.notes,
            'completed': self.completed,
            'assignee': self.assignee,
            'due_on': self.due_on,
            'url': self.url
        }


class AsanaIntegration:
    """
    Integration with Asana for creating tasks from action items.
    """
    
    def __init__(
        self,
        api_token: str,
        workspace_gid: str = "",
        project_gid: str = ""
    ):
        """
        Initialize Asana integration.
        
        Args:
            api_token: Asana personal access token
            workspace_gid: Default workspace GID
            project_gid: Default project GID
        """
        if not HAS_ASANA:
            raise ImportError("asana package is required for Asana integration")
        
        self.api_token = api_token
        self.workspace_gid = workspace_gid
        self.project_gid = project_gid
        
        self._client: Optional[asana.Client] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to Asana."""
        try:
            self._client = asana.Client.access_token(self.api_token)
            # Disable deprecation warnings
            self._client.options['client_name'] = 'meeting-intelligence-agent'
            
            # Test connection
            me = self._client.users.me()
            logger.info(f"Connected to Asana as: {me['name']}")
            
            # Get workspace if not set
            if not self.workspace_gid:
                workspaces = list(self._client.workspaces.find_all())
                if workspaces:
                    self.workspace_gid = workspaces[0]['gid']
            
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Asana: {e}")
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Asana."""
        return self._connected and self._client is not None
    
    def create_task(
        self,
        name: str,
        notes: str = "",
        assignee: Optional[str] = None,
        due_on: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        project_gid: Optional[str] = None,
        workspace_gid: Optional[str] = None
    ) -> Optional[AsanaTask]:
        """
        Create an Asana task.
        
        Args:
            name: Task name
            notes: Task description/notes
            assignee: Assignee email or GID
            due_on: Due date
            tags: Task tags
            project_gid: Project to add task to
            workspace_gid: Workspace GID
            
        Returns:
            AsanaTask if created successfully
        """
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            # Build task data
            task_data = {
                'name': name,
                'notes': notes,
                'workspace': workspace_gid or self.workspace_gid
            }
            
            # Add project
            if project_gid or self.project_gid:
                task_data['projects'] = [project_gid or self.project_gid]
            
            # Add due date
            if due_on:
                task_data['due_on'] = due_on.strftime('%Y-%m-%d')
            
            # Create task
            task = self._client.tasks.create(task_data)
            
            # Assign if specified
            if assignee:
                try:
                    # Try to find user by email
                    users = list(self._client.users.find_all(
                        workspace=self.workspace_gid
                    ))
                    for user in users:
                        if user.get('email') == assignee or user.get('gid') == assignee:
                            self._client.tasks.update(task['gid'], {
                                'assignee': user['gid']
                            })
                            break
                except Exception as e:
                    logger.warning(f"Could not assign task: {e}")
            
            result = AsanaTask(
                gid=task['gid'],
                name=name,
                notes=notes,
                completed=False,
                assignee=assignee,
                due_on=due_on.strftime('%Y-%m-%d') if due_on else None,
                url=f"https://app.asana.com/0/{self.project_gid}/{task['gid']}"
            )
            
            logger.info(f"Created Asana task: {task['gid']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Asana task: {e}")
            return None
    
    def create_from_action_item(
        self,
        action_item: Dict[str, Any],
        meeting_title: Optional[str] = None
    ) -> Optional[AsanaTask]:
        """
        Create an Asana task from an action item.
        
        Args:
            action_item: Action item dictionary
            meeting_title: Optional meeting title for context
            
        Returns:
            AsanaTask if created
        """
        # Build notes
        notes_parts = []
        
        if action_item.get('source_quote'):
            notes_parts.append(f"Source: {action_item['source_quote']}")
        
        if meeting_title:
            notes_parts.append(f"Meeting: {meeting_title}")
        
        if action_item.get('meeting_id'):
            notes_parts.append(f"Meeting ID: {action_item['meeting_id']}")
        
        if action_item.get('priority'):
            notes_parts.append(f"Priority: {action_item['priority']}")
        
        notes = "\n".join(notes_parts)
        
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
        
        # Create task
        return self.create_task(
            name=action_item.get('description', 'Action Item'),
            notes=notes,
            assignee=action_item.get('assignee'),
            due_on=deadline,
            tags=action_item.get('tags', [])
        )
    
    def create_batch(
        self,
        action_items: List[Dict[str, Any]],
        meeting_title: Optional[str] = None
    ) -> List[AsanaTask]:
        """
        Create multiple Asana tasks from action items.
        
        Args:
            action_items: List of action items
            meeting_title: Meeting title for context
            
        Returns:
            List of created AsanaTask objects
        """
        created = []
        for item in action_items:
            task = self.create_from_action_item(item, meeting_title)
            if task:
                created.append(task)
        
        logger.info(f"Created {len(created)} Asana tasks")
        return created
    
    def update_task_status(
        self,
        task_gid: str,
        completed: bool
    ) -> bool:
        """
        Update a task's completion status.
        
        Args:
            task_gid: Task GID
            completed: Whether task is completed
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            self._client.tasks.update(task_gid, {'completed': completed})
            logger.info(f"Updated task {task_gid} completed={completed}")
            return True
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return False
    
    def get_task(self, task_gid: str) -> Optional[AsanaTask]:
        """Get a task by GID."""
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            task = self._client.tasks.find_by_id(task_gid)
            return AsanaTask(
                gid=task['gid'],
                name=task['name'],
                notes=task.get('notes', ''),
                completed=task.get('completed', False),
                assignee=task.get('assignee', {}).get('name') if task.get('assignee') else None,
                due_on=task.get('due_on'),
                url=f"https://app.asana.com/0/0/{task['gid']}"
            )
        except Exception as e:
            logger.error(f"Failed to get task {task_gid}: {e}")
            return None
    
    def search_tasks(
        self,
        text: str,
        project_gid: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> List[AsanaTask]:
        """
        Search for tasks.
        
        Args:
            text: Search text
            project_gid: Filter by project
            completed: Filter by completion status
            
        Returns:
            List of matching tasks
        """
        if not self.is_connected:
            if not self.connect():
                return []
        
        try:
            params = {
                'workspace': self.workspace_gid,
                'text': text
            }
            
            if completed is not None:
                params['completed'] = completed
            
            tasks = list(self._client.tasks.search_tasks_for_workspace(
                self.workspace_gid,
                params=params
            ))
            
            return [
                AsanaTask(
                    gid=task['gid'],
                    name=task['name'],
                    notes='',
                    completed=task.get('completed', False),
                    url=f"https://app.asana.com/0/0/{task['gid']}"
                )
                for task in tasks
            ]
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return []
    
    def list_projects(self) -> List[Dict[str, str]]:
        """List available projects."""
        if not self.is_connected:
            if not self.connect():
                return []
        
        try:
            projects = list(self._client.projects.find_all(
                workspace=self.workspace_gid
            ))
            return [
                {'gid': p['gid'], 'name': p['name']}
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
    
    def list_workspaces(self) -> List[Dict[str, str]]:
        """List available workspaces."""
        if not self.is_connected:
            if not self.connect():
                return []
        
        try:
            workspaces = list(self._client.workspaces.find_all())
            return [
                {'gid': w['gid'], 'name': w['name']}
                for w in workspaces
            ]
        except Exception as e:
            logger.error(f"Failed to list workspaces: {e}")
            return []
    
    def create_meeting_section(
        self,
        meeting_title: str,
        meeting_date: datetime,
        project_gid: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a section in Asana for a meeting's action items.
        
        Args:
            meeting_title: Meeting title
            meeting_date: Meeting date
            project_gid: Project to create section in
            
        Returns:
            Section GID if created
        """
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            section_name = f"{meeting_date.strftime('%Y-%m-%d')} - {meeting_title}"
            section = self._client.sections.create_section_for_project(
                project_gid or self.project_gid,
                {'name': section_name}
            )
            logger.info(f"Created section: {section_name}")
            return section['gid']
        except Exception as e:
            logger.error(f"Failed to create section: {e}")
            return None


def get_asana_integration(
    api_token: Optional[str] = None,
    workspace_gid: Optional[str] = None,
    project_gid: Optional[str] = None
) -> Optional[AsanaIntegration]:
    """
    Get an Asana integration instance.
    
    Uses environment variables if not provided:
    - ASANA_API_TOKEN
    - ASANA_WORKSPACE_GID
    - ASANA_PROJECT_GID
    """
    api_token = api_token or os.getenv("ASANA_API_TOKEN", "")
    workspace_gid = workspace_gid or os.getenv("ASANA_WORKSPACE_GID", "")
    project_gid = project_gid or os.getenv("ASANA_PROJECT_GID", "")
    
    if not api_token:
        logger.warning("Asana API token not configured")
        return None
    
    try:
        integration = AsanaIntegration(
            api_token=api_token,
            workspace_gid=workspace_gid,
            project_gid=project_gid
        )
        return integration
    except ImportError:
        logger.warning("Asana package not installed")
        return None
