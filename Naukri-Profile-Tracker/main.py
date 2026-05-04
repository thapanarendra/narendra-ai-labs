#!/usr/bin/env python3
"""
Naukri Profile Tracker - Main Entry Point

A comprehensive automation agent for managing your Naukri.com profile,
tracking recruiter activities, and staying visible to potential employers.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.naukri_agent import NaukriAgent, run_agent_task
from src.scheduler import Scheduler, run_scheduler
from src.config import get_settings

app = typer.Typer(
    name="naukri-tracker",
    help="Naukri Profile Tracker - Automate your job search",
    add_completion=False
)
console = Console()


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           🎯 NAUKRI PROFILE TRACKER                          ║
║                                                               ║
║     Automate your job search and stay visible to recruiters  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


@app.command()
def run(
    task: str = typer.Option(
        "full-check",
        "--task", "-t",
        help="Task to run: resume-update, recruiter-check, job-recommendations, full-check"
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--no-headless",
        help="Run browser in headless mode"
    ),
):
    """Run a specific agent task."""
    print_banner()
    
    console.print(f"\n[bold green]Running task:[/bold green] {task}\n")
    
    try:
        # Update settings for headless mode
        import os
        os.environ["HEADLESS_MODE"] = str(headless).lower()
        
        result = asyncio.run(run_agent_task(task))
        
        if "error" in result:
            console.print(f"[bold red]Error:[/bold red] {result['error']}")
            raise typer.Exit(1)
        
        # Display results
        console.print("\n[bold green]Task completed successfully![/bold green]\n")
        
        if task == "full-check":
            _display_full_check_results(result)
        elif task == "recruiter-check":
            _display_recruiter_results(result.get("recruiter_activity", {}))
        elif task == "job-recommendations":
            _display_job_results(result.get("recommendations", []))
        else:
            console.print(result)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Task failed")
        raise typer.Exit(1)


@app.command()
def daemon():
    """Run the agent as a background scheduler daemon."""
    print_banner()
    
    console.print("\n[bold cyan]Starting Naukri Profile Tracker daemon...[/bold cyan]\n")
    console.print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Daemon error:[/bold red] {e}")
        logger.exception("Daemon failed")
        raise typer.Exit(1)


@app.command()
def status():
    """Show current status and scheduled jobs."""
    print_banner()
    
    settings = get_settings()
    
    # Configuration status
    console.print("\n[bold]Configuration Status[/bold]\n")
    
    config_table = Table(show_header=True, header_style="bold magenta")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Email", settings.naukri_email)
    config_table.add_row("Resume Path", str(settings.resume_path))
    config_table.add_row("Headless Mode", str(settings.headless_mode))
    config_table.add_row("Update Frequency", f"{settings.update_frequency_days} days")
    config_table.add_row("Recruiter Check", f"Every {settings.recruiter_check_hours} hours")
    config_table.add_row("Notifications", str(settings.notification_enabled))
    config_table.add_row("Database", str(settings.database_path))
    
    console.print(config_table)
    
    # Check if resume exists
    if settings.resume_path.exists():
        console.print(f"\n[green]✓ Resume file found[/green]")
    else:
        console.print(f"\n[red]✗ Resume file not found at {settings.resume_path}[/red]")


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of activities to show")
):
    """Show recent activity history."""
    print_banner()
    
    from src.database import Database
    settings = get_settings()
    
    db = Database(settings.database_path)
    activities = db.get_recent_activities(limit)
    db.close()
    
    if not activities:
        console.print("\n[yellow]No activities recorded yet.[/yellow]")
        return
    
    console.print(f"\n[bold]Recent Activities (Last {limit})[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Time", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Details", style="white")
    
    for activity in activities:
        table.add_row(
            activity.get("created_at", "N/A"),
            activity.get("activity_type", "N/A"),
            str(activity.get("data", ""))[:50] + "..."
        )
    
    console.print(table)


@app.command()
def jobs(
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search jobs by title"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of jobs to show")
):
    """Show stored job recommendations."""
    print_banner()
    
    from src.database import Database
    settings = get_settings()
    
    db = Database(settings.database_path)
    
    criteria = {}
    if search:
        criteria["title"] = search
    
    jobs_list = db.search_jobs(criteria)[:limit]
    db.close()
    
    if not jobs_list:
        console.print("\n[yellow]No jobs found. Run 'job-recommendations' task first.[/yellow]")
        return
    
    console.print(f"\n[bold]Job Recommendations[/bold]\n")
    
    for job in jobs_list:
        panel_content = f"""
[cyan]Company:[/cyan] {job.get('company', 'N/A')}
[cyan]Location:[/cyan] {job.get('location', 'N/A')}
[cyan]Salary:[/cyan] {job.get('salary', 'N/A')}
[cyan]Experience:[/cyan] {job.get('experience', 'N/A')}
        """
        console.print(Panel(panel_content, title=job.get('title', 'Job'), border_style="blue"))


@app.command()
def applications():
    """Show application statistics."""
    print_banner()
    
    from src.database import Database
    settings = get_settings()
    
    db = Database(settings.database_path)
    stats = db.get_application_stats()
    db.close()
    
    console.print("\n[bold]Application Statistics[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    table.add_row("Total Applications", str(stats.get("total", 0)))
    
    for status, count in stats.get("by_status", {}).items():
        table.add_row(status, str(count))
    
    console.print(table)


def _display_full_check_results(result: dict):
    """Display full check results in a formatted way."""
    
    # Recruiter Activity
    if "recruiter_activity" in result:
        console.print("[bold]Recruiter Activity[/bold]")
        _display_recruiter_results(result["recruiter_activity"])
    
    # Profile Performance
    if "profile_performance" in result:
        perf = result["profile_performance"]
        console.print("\n[bold]Profile Performance[/bold]")
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Profile Views", str(perf.get("profile_views", 0)))
        table.add_row("Search Appearances", str(perf.get("search_appearances", 0)))
        table.add_row("Recruiter Actions", str(perf.get("recruiter_actions", 0)))
        
        console.print(table)
    
    # Jobs
    if "job_recommendations_count" in result:
        console.print(f"\n[bold]Jobs:[/bold] {result['job_recommendations_count']} recommendations found")


def _display_recruiter_results(activity: dict):
    """Display recruiter activity results."""
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    views = activity.get("profile_views", {})
    messages = activity.get("messages", {})
    interviews = activity.get("interview_requests", {})
    
    table.add_row("Profile Views", str(views.get("total", 0)))
    table.add_row("Unread Messages", str(messages.get("unread", 0)))
    table.add_row("Pending Interviews", str(len(interviews.get("pending", []))))
    table.add_row("New Views", str(activity.get("new_profile_views", 0)))
    table.add_row("New Messages", str(activity.get("new_messages", 0)))
    
    console.print(table)


def _display_job_results(jobs: list):
    """Display job recommendations."""
    if not jobs:
        console.print("[yellow]No job recommendations found.[/yellow]")
        return
    
    console.print(f"\n[bold]Found {len(jobs)} job recommendations:[/bold]\n")
    
    for job in jobs[:5]:  # Show top 5
        console.print(f"  • {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
        console.print(f"    Location: {job.get('location', 'N/A')} | {job.get('salary', 'N/A')}")
        console.print()


if __name__ == "__main__":
    app()
